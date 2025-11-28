from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta

from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db.models import Sum, Count
from django.db.models.functions import TruncDate

from xhtml2pdf import pisa
from .models import Pago, Pedido

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import (
    Categoria, Producto, Mesa, Mesero,
    Pedido, DetallePedido, Pago
)

from .serializers import (
    CategoriaSerializer, ProductoSerializer, MesaSerializer,
    MeseroSerializer, PedidoSerializer, DetallePedidoSerializer, PagoSerializer
)

from .forms import ProductoForm
import json


# ===============================
# CRUD ViewSets
# ===============================
class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer


class MesaViewSet(viewsets.ModelViewSet):
    queryset = Mesa.objects.all()
    serializer_class = MesaSerializer


class MeseroViewSet(viewsets.ModelViewSet):
    queryset = Mesero.objects.all()
    serializer_class = MeseroSerializer


class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer


class DetallePedidoViewSet(viewsets.ModelViewSet):
    queryset = DetallePedido.objects.all()
    serializer_class = DetallePedidoSerializer


class PagoViewSet(viewsets.ModelViewSet):
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer


# ===============================
# Formularios HTML
# ===============================
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" creado correctamente.')
            return redirect('listar_productos')
    else:
        form = ProductoForm()
    return render(request, 'api/crear_producto.html', {'form': form})


def listar_productos(request):
    productos = Producto.objects.all()
    return render(request, 'api/listar_productos.html', {'productos': productos})


# ===============================
# Prueba API
# ===============================
def hola_mundo(request):
    return JsonResponse({"mensaje": "Hola desde la API"})


# ===============================
# Carrito 
# ===============================
carrito = []

@api_view(['GET'])
def obtener_carrito(request):
    return Response({'carrito': carrito})

@api_view(['POST'])
def agregar_al_carrito(request):
    producto_id = request.data.get('producto_id')
    cantidad = int(request.data.get('cantidad', 1))

    if not producto_id:
        return Response({'error': 'Se requiere el ID del producto'}, status=400)

    carrito.append({'producto_id': producto_id, 'cantidad': cantidad})
    return Response({'mensaje': 'Producto agregado al carrito', 'carrito': carrito})


# ===============================
# Registrar Pedido
# ===============================
@api_view(['POST'])
def registrar_pedido(request):
    try:
        mesa_id = request.data.get("mesa_id")
        mesero_id = request.data.get("mesero_id")
        productos = request.data.get("productos", [])

        if not mesa_id or not mesero_id or not productos:
            return Response({"error": "Faltan campos requeridos"}, status=400)

        mesa = Mesa.objects.filter(id=mesa_id).first()
        if not mesa:
            return Response({"error": "Mesa no encontrada"}, status=404)

        mesero = Mesero.objects.filter(id=mesero_id).first()
        if not mesero:
            return Response({"error": "Mesero no encontrado"}, status=404)

        # Crear el pedido
        pedido = Pedido.objects.create(
            mesa=mesa,
            mesero=mesero,
            estado="pendiente",
            total=0
        )

        total = 0
        detalles = []

        for item in productos:
            producto = Producto.objects.filter(id=item.get("producto_id")).first()
            if not producto:
                continue

            cantidad = int(item.get("cantidad", 1))
            subtotal = producto.precio * cantidad
            total += subtotal

            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio
            )

            detalles.append({
                "producto": producto.nombre,
                "cantidad": cantidad,
                "subtotal": subtotal
            })

        pedido.total = total
        pedido.save()

        return Response({
            "mensaje": "Pedido registrado correctamente",
            "pedido_id": pedido.id,
            "total": total,
            "detalles": detalles
        }, status=201)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ===============================
# Pedidos para cocina
# ===============================
@api_view(['GET'])
def pedidos_cocina(request):
    try:
        pedidos = Pedido.objects.exclude(
            estado__in=['cancelado', 'pagado', 'servido']
        ).order_by('-id')

        data = []

        for pedido in pedidos:
            detalles = DetallePedido.objects.filter(pedido=pedido)
            detalles_data = [
                {
                    "producto_nombre": det.producto.nombre,
                    "cantidad": det.cantidad,
                    "subtotal": float(det.precio_unitario * det.cantidad)
                }
                for det in detalles
            ]

            data.append({
                "id": pedido.id,
                "mesa": pedido.mesa.numero if pedido.mesa else None,
                "mesero": pedido.mesero.nombre if pedido.mesero else None,
                "total": float(pedido.total),
                "estado": pedido.estado,
                "detalles": detalles_data
            })

        return Response(data)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ===============================
# Actualizar estado de pedido
# ===============================
@api_view(['PATCH'])
def actualizar_pedido_estado(request, pedido_id):
    try:
        pedido = Pedido.objects.filter(id=pedido_id).first()

        if not pedido:
            return Response({"error": "Pedido no encontrado."}, status=404)

        nuevo_estado = request.data.get('estado')
        if not nuevo_estado:
            return Response({"error": "Debe enviar el estado a actualizar."}, status=400)

        pedido.estado = nuevo_estado
        pedido.save()

        return Response({
            "mensaje": f"Pedido {pedido_id} actualizado",
            "estado": pedido.estado
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ===============================
# Mesas disponibles
# ===============================
@api_view(['GET'])
def mesas_disponibles(request):
    mesas_ocupadas = Pedido.objects.filter(
        estado__in=['pendiente', 'en preparación']
    ).values_list('mesa_id', flat=True)

    mesas_libres = Mesa.objects.exclude(id__in=mesas_ocupadas)

    return Response([
        {"id": m.id, "numero": m.numero}
        for m in mesas_libres
    ])


# ===============================
# Registrar pago
# ===============================
@api_view(['POST'])
def registrar_pago(request):
    try:
        pedido_id = request.data.get("pedido_id")
        metodo = request.data.get("metodo_pago")
        monto = request.data.get("monto_pagado")

        if not all([pedido_id, metodo, monto]):
            return Response({"error": "Faltan campos requeridos"}, status=400)

        pedido = Pedido.objects.filter(id=pedido_id).first()
        if not pedido:
            return Response({"error": "Pedido no encontrado"}, status=404)

        if Pago.objects.filter(pedido=pedido).exists():
            return Response({"error": "El pedido ya tiene un pago registrado"}, status=400)

        pago = Pago.objects.create(
            pedido=pedido,
            metodo_pago=metodo,
            monto_pagado=monto
        )

        pedido.estado = "pagado"
        pedido.save()

        return Response({
            "mensaje": "Pago registrado correctamente",
            "pago_id": pago.id
        }, status=201)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ===============================
# Dashboard
# ===============================
@api_view(['GET'])
def resumen_dashboard(request):
    datos = {
        "total_pedidos": Pedido.objects.count(),
        "meseros_activos": Mesero.objects.count(),
        "ventas_totales": Pago.objects.aggregate(total=Sum('monto_pagado'))['total'] or 0
    }
    return Response(datos)


@api_view(['GET'])
def estadisticas_dashboard(request):
    ventas_por_dia = list(
        Pago.objects.annotate(
            fecha=TruncDate('fecha_pago')
        ).values('fecha').annotate(
            total=Sum('monto_pagado')
        ).order_by('fecha')
    )

    pedidos_por_dia = list(
        Pedido.objects.annotate(
            fecha=TruncDate('fecha_hora')
        ).values('fecha').annotate(
            total=Count('id')
        ).order_by('fecha')
    )

    return Response({
        "ventas_por_dia": ventas_por_dia,
        "pedidos_por_dia": pedidos_por_dia
    })


# ===============================
# Login administrador
# ===============================
@csrf_exempt
def login_admin(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = authenticate(
                username=data.get('username'),
                password=data.get('password')
            )

            if user and user.is_staff:
                return JsonResponse({'success': True})

            return JsonResponse({'success': False, 'message': 'Credenciales inválidas'}, status=401)

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)


# ===============================
# Pedidos por mesero
# ===============================
@api_view(['GET'])
def pedidos_por_mesero(request, mesero_id):
    pedidos = Pedido.objects.filter(mesero_id=mesero_id).order_by('-id')

    resultado = []

    for pedido in pedidos:
        detalles = DetallePedido.objects.filter(pedido=pedido)

        resultado.append({
            "id": pedido.id,
            "mesa": pedido.mesa.numero if pedido.mesa else None,
            "total": float(pedido.total),
            "estado": pedido.estado,
            "detalles": [
                {
                    "producto_nombre": d.producto.nombre,
                    "cantidad": d.cantidad,
                    "subtotal": float(d.precio_unitario * d.cantidad)
                }
                for d in detalles
            ]
        })

    return Response(resultado)


# ===============================
# Marcar pedido como entregado
# ===============================
@csrf_exempt
def marcar_entregado(request, pedido_id):
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        pedido.estado = "servido"
        pedido.save()

        return JsonResponse({
            "message": "Pedido marcado como entregado",
            "pedido_id": pedido.id
        })

    except Pedido.DoesNotExist:
        return JsonResponse({"error": "El pedido no existe"}, status=404)


# ===============================
# Pedidos por usuario (cliente)
# ===============================
class PedidosPorUsuarioView(APIView):
    def get(self, request, id_usuario):
        pedidos = Pedido.objects.filter(mesa_id=id_usuario).order_by('-id')

        resultado = []

        for pedido in pedidos:
            detalles = DetallePedido.objects.filter(pedido=pedido)

            resultado.append({
                "id": pedido.id,
                "mesa": pedido.mesa.numero if pedido.mesa else None,
                "total": float(pedido.total),
                "estado": pedido.estado,
                "fecha": str(pedido.fecha_hora),
                "detalles": [
                    {
                        "producto_nombre": d.producto.nombre,
                        "cantidad": d.cantidad,
                        "subtotal": float(d.precio_unitario * d.cantidad)
                    }
                    for d in detalles
                ]
            })

        return Response(resultado)


# ===============================
# Pedidos por mesa (GET con mesa_id)
# ===============================
@api_view(['GET'])
def pedidos_por_mesa(request):
    mesa_id = request.GET.get('mesa_id')
    if not mesa_id:
        return Response({"error": "No se proporcionó mesa_id"}, status=400)

    try:
        mesa_id = int(mesa_id)
    except ValueError:
        return Response({"error": "mesa_id inválido"}, status=400)

    if not Mesa.objects.filter(id=mesa_id).exists():
        return Response({"error": "No se encontró la mesa"}, status=404)

    pedidos = Pedido.objects.filter(mesa_id=mesa_id).order_by('fecha_hora')
    serializer = PedidoSerializer(pedidos, many=True)
    return Response(serializer.data)


# ===============================
# LOGIN CLIENTE
# ===============================
@csrf_exempt
def login_cliente(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mesa_id = data.get('mesa_id')

            if not mesa_id:
                return JsonResponse({"success": False, "message": "Debe proporcionar el ID de la mesa"}, status=400)

            try:
                mesa = Mesa.objects.get(id=mesa_id)
            except Mesa.DoesNotExist:
                return JsonResponse({"success": False, "message": "Mesa no encontrada"}, status=404)

            request.session['mesa_id'] = mesa.id

            return JsonResponse({"success": True, "mesa_numero": mesa.numero})

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)

    return JsonResponse({"success": False, "message": "Método no permitido"}, status=405)


# ===============================
# PEDIDOS DEL CLIENTE POR SESIÓN
# ===============================
@api_view(['GET'])
def pedidos_cliente(request):
    mesa_id = request.session.get('mesa_id')
    if not mesa_id:
        return Response({"error": "No se encontró la mesa. Inicia sesión nuevamente."}, status=401)

    pedidos = Pedido.objects.filter(mesa_id=mesa_id).order_by('fecha_hora')
    serializer = PedidoSerializer(pedidos, many=True)
    return Response(serializer.data)


# ===============================
# Registrar cliente (crea mesa)
# ===============================
@api_view(['POST'])
def registrar_cliente(request):
    data = request.data
    nombre = data.get("nombre")

    if not nombre:
        return Response({"message": "Falta el nombre"}, status=400)

    mesa = Mesa.objects.create(
        numero=Mesa.objects.count() + 1,
        capacidad=1,
        ubicacion=f"Cliente {nombre}",
        disponible=True
    )

    return Response({
        "success": True,
        "mesa_id": mesa.id,
        "mesa_numero": mesa.numero,
        "mensaje": f"Mesa creada para {nombre}"
    })


# ===============================
# ALERTA DE RETRASOS (RF-10)
# ===============================
@api_view(['GET'])
def verificar_retrasos(request):
    ahora = timezone.now()
    limite = ahora - timedelta(minutes=20)

    pedidos_retrasados = Pedido.objects.filter(
        estado__in=["pendiente", "en preparación"],
        fecha_hora__lte=limite  # CAMBIADO
    )

    alertas = [
        {
            "id": pedido.id,
            "mesa": pedido.mesa.numero if pedido.mesa else "N/A",
            "estado": pedido.estado,
            "tiempo": str(ahora - pedido.fecha_hora)  # CAMBIADO
        }
        for pedido in pedidos_retrasados
    ]

    return Response({"alertas": alertas})

# ===============================
# 🛑 Marcar pedido como retrasado (notificación en tiempo real)
# ===============================
@api_view(['POST'])
def marcar_retrasado(request, pedido_id):
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        pedido.estado = "retrasado"
        pedido.save()

        # Notificación en tiempo real
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "pedidos_grupo",   
            {
                "type": "enviar_alerta",  
                "mensaje": {
                    "texto": f"🚨 El pedido #{pedido.id} presenta retraso",
                    "tipo": "retraso",
                    "mesa": pedido.mesa.numero if pedido.mesa else "N/A"
                }
            }
        )

        return Response({
            "message": "Pedido marcado como retrasado",
            "pedido_id": pedido.id,
            "estado": pedido.estado
        })

    except Pedido.DoesNotExist:
        return Response({"error": "Pedido no encontrado"}, status=404)

from django.http import JsonResponse
from .models import Pedido
import json

def actualizar_estado_pedido(request, pedido_id):
    if request.method == "PATCH":
        body = json.loads(request.body)
        nuevo_estado = body.get("estado")

        try:
            pedido = Pedido.objects.get(id=pedido_id)
            pedido.estado = nuevo_estado
            pedido.save()

            return JsonResponse({"mensaje": "Estado actualizado", "estado": pedido.estado})
        except Pedido.DoesNotExist:
            return JsonResponse({"error": "Pedido no encontrado"}, status=404)

    return JsonResponse({"error": "Método no permitido"}, status=405)


@api_view(['PATCH'])
def actualizar_pedido_estado(request, pk):
    try:
        pedido = Pedido.objects.get(pk=pk)
    except Pedido.DoesNotExist:
        return Response({"error": "Pedido no encontrado"}, status=404)

    nuevo_estado = request.data.get("estado")
    if not nuevo_estado:
        return Response({"error": "Estado no enviado"}, status=400)

    pedido.estado = nuevo_estado

    # ✅ Guardar hora de finalización solo si el pedido se completa
    if nuevo_estado in ["servido", "pagado", "listo"]:  # ajusta según tus estados
        pedido.hora_fin_preparacion = timezone.now()

    pedido.save()

    return Response({
        "mensaje": "Estado actualizado correctamente",
        "estado": nuevo_estado
    })


@api_view(['GET'])
def analisis_tiempos(request):
    pedidos = Pedido.objects.filter(tiempo_inicio__isnull=False, tiempo_fin__isnull=False)

    tiempos = [p.tiempo_preparacion for p in pedidos if p.tiempo_preparacion]

    if not tiempos:
        return Response({"mensaje": "No hay datos suficientes"}, status=200)

    promedio = sum(tiempos) / len(tiempos)

    return Response({
        "pedidos_analizados": len(tiempos),
        "tiempo_promedio_min": round(promedio, 2),
        "tiempo_maximo_min": round(max(tiempos), 2),
        "tiempo_minimo_min": round(min(tiempos), 2)
    })

def api_tiempos_pedidos(request):
    # últimos 20 pedidos con tiempo calculado
    pedidos = Pedido.objects.annotate(
        tiempo_preparacion=ExpressionWrapper(
            F('hora_fin_preparacion') - F('hora_creacion'),
            output_field=DurationField()
        )
    ).order_by('-hora_creacion')[:20]

    datos = [
        {
            "id": p.id,
            "tiempo_preparacion_min": p.tiempo_preparacion.total_seconds() / 60
        }
        for p in pedidos if p.hora_fin_preparacion
    ]
    return JsonResponse(datos, safe=False)


@api_view(['GET'])
def tiempos_pedidos(request):
    """
    Devuelve los últimos 20 pedidos con su tiempo de preparación en minutos.
    """
    pedidos = Pedido.objects.all().order_by('-fecha_hora')[:20]
    serializer = PedidoSerializer(pedidos, many=True)
    
    # Extraemos solo id y tiempo
    datos = [
        {"id": p["id"], "tiempo_preparacion_min": p["tiempo_preparacion_min"]}
        for p in serializer.data
    ]
    
    return Response(datos)

# ===============================
# HISTORIAL DE FACTURAS 
# ===============================
@api_view(['GET'])
def historial_facturas(request):
    pagos = Pago.objects.select_related('pedido').order_by('-fecha_pago')

    data = [
        {
            "factura_id": pago.id,
            "pedido_id": pago.pedido.id,
            "mesa": pago.pedido.mesa.numero if pago.pedido.mesa else None,
            "monto_pagado": float(pago.monto_pagado),
            "metodo_pago": pago.metodo_pago,
            "fecha_pago": pago.fecha_pago
        }
        for pago in pagos
    ]

    return Response(data)

