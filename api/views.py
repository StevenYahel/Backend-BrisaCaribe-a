from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from django.http import HttpResponse


from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404


from django.db.models import Sum, Count, F, DurationField, ExpressionWrapper
from django.db.models.functions import TruncDate

from django.template.loader import get_template 
from io import BytesIO


from xhtml2pdf import pisa
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


# =====================================
# CRUD ViewSets
# =====================================
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


# =====================================
# Formularios HTML
# =====================================
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


# =====================================
# Prueba API
# =====================================
def hola_mundo(request):
    return JsonResponse({"mensaje": "Hola desde la API"})


# =====================================
# Carrito
# =====================================
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
    return Response({'mensaje': 'Producto agregado', 'carrito': carrito})


# =====================================
# Registrar Pedido (Administrador)
# =====================================
@api_view(['POST'])
def registrar_pedido(request):
    try:
        mesa_id = request.data.get("mesa_id")
        mesero_id = request.data.get("mesero_id")
        productos = request.data.get("productos", [])

        if not mesa_id or not mesero_id or not productos:
            return Response({"error": "Faltan datos"}, status=400)

        mesa = Mesa.objects.filter(id=mesa_id).first()
        mesero = Mesero.objects.filter(id=mesero_id).first()

        if not mesa:
            return Response({"error": "Mesa no encontrada"}, status=404)
        if not mesero:
            return Response({"error": "Mesero no encontrado"}, status=404)

        pedido = Pedido.objects.create(
            mesa=mesa,
            mesero=mesero,
            estado="pendiente",
            total=0
        )

        total = 0
        detalles_finales = []

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

            detalles_finales.append({
                "producto": producto.nombre,
                "cantidad": cantidad,
                "subtotal": subtotal
            })

        pedido.total = total
        pedido.save()

        return Response({
            "mensaje": "Pedido registrado",
            "pedido_id": pedido.id,
            "total": total,
            "detalles": detalles_finales
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# =====================================
# Pedidos para cocina
# =====================================
@api_view(['GET'])
def pedidos_cocina(request):
    try:
        pedidos = Pedido.objects.exclude(
            estado__in=['cancelado', 'pagado', 'servido']
        ).order_by('-id')

        data = []
        for pedido in pedidos:
            detalles = DetallePedido.objects.filter(pedido=pedido)

            data.append({
                "id": pedido.id,
                "mesa": pedido.mesa.numero if pedido.mesa else None,
                "mesero": pedido.mesero.nombre if pedido.mesero else None,
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

        return Response(data)

    except Exception as e:
        return Response({"error": str(e)}, status=500)




# =====================================
# Actualizar estado de pedido
# =====================================

@api_view(['PATCH'])
def actualizar_pedido_estado(request, pk):
    """
    Actualiza el estado de un pedido y gestiona automáticamente
    los tiempos de inicio, fin y preparación.
    """
    try:
        pedido = Pedido.objects.get(pk=pk)
    except Pedido.DoesNotExist:
        return Response({"detail": "Pedido no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    # Obtener estado enviado desde el JS
    estado = request.data.get('estado')
    if not estado:
        return Response({"detail": "No se proporcionó el estado"}, status=status.HTTP_400_BAD_REQUEST)

    # Validar que el estado sea uno permitido
    if estado not in [e[0] for e in Pedido.ESTADOS]:
        return Response({"detail": f"Estado inválido: {estado}"}, status=status.HTTP_400_BAD_REQUEST)

    pedido.estado = estado

    # ===== Lógica de tiempos =====
    if estado == "en_preparacion" and not pedido.tiempo_inicio:
        pedido.tiempo_inicio = timezone.now()

    if estado in ["listo", "servido", "pagado"]:
        if pedido.tiempo_inicio and not pedido.tiempo_fin:
            pedido.tiempo_fin = timezone.now()

    # Calcular tiempo de preparación
    if pedido.tiempo_inicio and pedido.tiempo_fin:
        duracion = pedido.tiempo_fin - pedido.tiempo_inicio
        pedido.tiempo_preparacion = round(duracion.total_seconds() / 60, 2)
    else:
        pedido.tiempo_preparacion = None

    pedido.save()

    # Retornar datos para el JS
    return Response({
        "pedido": {
            "id": pedido.id,
            "estado": pedido.estado,
            "estado_normalizado": pedido.estado,
            "tiempo_inicio": pedido.tiempo_inicio,
            "tiempo_fin": pedido.tiempo_fin,
            "tiempo_preparacion": pedido.tiempo_preparacion
        }
    }, status=status.HTTP_200_OK)

# =====================================
# Mesas disponibles
# =====================================
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


# =====================================
# Registrar Pago
# =====================================

@api_view(['POST'])
def registrar_pago(request):
    try:
        pedido_id = request.data.get("pedido_id")
        metodo = request.data.get("metodo_pago")
        monto = request.data.get("monto_pagado")

        if not all([pedido_id, metodo, monto]):
            return Response({"error": "Faltan datos"}, status=400)

        pedido = Pedido.objects.filter(id=pedido_id).first()
        if not pedido:
            return Response({"error": "Pedido no existe"}, status=404)

        if Pago.objects.filter(pedido=pedido).exists():
            return Response({"error": "Ya tiene pago"}, status=400)

        # Crear pago
        pago = Pago.objects.create(
            pedido=pedido,
            metodo_pago=metodo,
            monto_pagado=monto
        )

        # Cambiar estado del pedido a "pagado"
        pedido.estado = "pagado"
        pedido.save()

        # Notificar a través de WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "pedidos",
            {
                "type": "enviar_pedido",
                "mensaje": {
                    "pedido_id": pedido.id,
                    "estado": pedido.estado
                }
            }
        )

        return Response({"mensaje": "Pago registrado", "pago_id": pago.id})

    except Exception as e:
        return Response({"error": f"Error interno: {str(e)}"}, status=500)

# =====================================
# Dashboard
# =====================================
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
        )
    )

    pedidos_por_dia = list(
        Pedido.objects.annotate(
            fecha=TruncDate('fecha_hora')
        ).values('fecha').annotate(
            total=Count('id')
        )
    )

    return Response({
        "ventas_por_dia": ventas_por_dia,
        "pedidos_por_dia": pedidos_por_dia
    })


# =====================================
# Login Admin
# =====================================
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


# =====================================
# Pedidos por mesero
# =====================================
@api_view(['GET'])
def pedidos_por_mesero(request, mesero_id):
    pedidos = Pedido.objects.filter(mesero_id=mesero_id).order_by('-id')

    resultado = []
    for p in pedidos:
        detalles = DetallePedido.objects.filter(pedido=p)

        resultado.append({
            "id": p.id,
            "mesa": p.mesa.numero if p.mesa else None,
            "total": float(p.total),
            "estado": p.estado,
            "detalles": [
                {
                    "producto_nombre": d.producto.nombre,
                    "cantidad": d.cantidad,
                    "subtotal": float(d.precio_unitario * d.cantidad)
                } for d in detalles
            ]
        })

    return Response(resultado)


# =====================================
# Marcar pedido como entregado
# =====================================
@csrf_exempt
def marcar_entregado(request, pedido_id):
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        pedido.estado = "servido"
        pedido.save()

        return JsonResponse({"message": "Pedido entregado"})
    except Pedido.DoesNotExist:
        return JsonResponse({"error": "No existe"}, status=404)


# =====================================
# Pedidos por usuario-cliente
# =====================================
class PedidosPorUsuarioView(APIView):
    def get(self, request, id_usuario):
        pedidos = Pedido.objects.filter(mesa_id=id_usuario).order_by('-id')

        salida = []
        for p in pedidos:
            detalles = DetallePedido.objects.filter(pedido=p)

            salida.append({
                "id": p.id,
                "mesa": p.mesa.numero if p.mesa else None,
                "total": float(p.total),
                "estado": p.estado,
                "fecha": str(p.fecha_hora),
                "detalles": [
                    {
                        "producto_nombre": d.producto.nombre,
                        "cantidad": d.cantidad,
                        "subtotal": float(d.precio_unitario * d.cantidad)
                    } for d in detalles
                ]
            })

        return Response(salida)


# =====================================
# Pedidos por mesa
# =====================================
@api_view(['GET'])
def pedidos_por_mesa(request):
    mesa_id = request.GET.get('mesa_id')
    if not mesa_id:
        return Response({"error": "mesa_id faltante"}, status=400)

    if not Mesa.objects.filter(id=mesa_id).exists():
        return Response({"error": "Mesa no existe"}, status=404)

    pedidos = Pedido.objects.filter(mesa_id=mesa_id).order_by('fecha_hora')
    serializer = PedidoSerializer(pedidos, many=True)
    return Response(serializer.data)


# =====================================
# LOGIN CLIENTE
# =====================================
@csrf_exempt
def login_cliente(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mesa_id = data.get('mesa_id')

            if not mesa_id:
                return JsonResponse({"success": False, "message": "Falta mesa_id"}, status=400)

            mesa = Mesa.objects.filter(id=mesa_id).first()
            if not mesa:
                return JsonResponse({"success": False, "message": "Mesa no existe"}, status=404)

            request.session['mesa_id'] = mesa.id

            return JsonResponse({"success": True, "mesa_numero": mesa.numero})

        except:
            return JsonResponse({"success": False, "message": "Error interno"}, status=500)

    return JsonResponse({"success": False}, status=405)


# =====================================
# Pedidos cliente según sesión
# =====================================
@api_view(['GET'])
def pedidos_cliente(request):
    mesa_id = request.session.get('mesa_id')
    if not mesa_id:
        return Response({"error": "Sin sesión"}, status=401)

    pedidos = Pedido.objects.filter(mesa_id=mesa_id)
    return Response(PedidoSerializer(pedidos, many=True).data)


# =====================================
# Registrar Cliente (crea una mesa)
# =====================================
@api_view(['POST'])
def registrar_cliente(request):
    nombre = request.data.get("nombre")

    if not nombre:
        return Response({"message": "Falta nombre"}, status=400)

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


# =====================================
# Revisar retrasos
# =====================================
@api_view(['GET'])
def verificar_retrasos(request):
    ahora = timezone.now()
    limite = ahora - timedelta(minutes=20)

    pedidos_retrasados = Pedido.objects.filter(
        estado__in=["pendiente", "en preparación"],
        fecha_hora__lte=limite
    )

    alertas = [
        {
            "id": p.id,
            "mesa": p.mesa.numero if p.mesa else "N/A",
            "estado": p.estado,
            "tiempo": str(ahora - p.fecha_hora)
        }
        for p in pedidos_retrasados
    ]

    return Response({"alertas": alertas})


# =====================================
# Marcar retrasado + WebSocket
# =====================================
@api_view(['POST'])
def marcar_retrasado(request, pedido_id):
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        pedido.estado = "retrasado"
        pedido.save()

        layer = get_channel_layer()
        async_to_sync(layer.group_send)(
            "pedidos_grupo",
            {
                "type": "enviar_alerta",
                "mensaje": {
                    "texto": f"🚨 Pedido #{pedido.id} retrasado",
                    "tipo": "retraso",
                    "mesa": pedido.mesa.numero
                }
            }
        )

        return Response({"mensaje": "Marcado como retrasado"})
    except Pedido.DoesNotExist:
        return Response({"error": "No existe"}, status=404)


# =====================================
# Análisis de tiempos
# =====================================
@api_view(['GET'])
def analisis_tiempos(request):
    pedidos = Pedido.objects.filter(
        tiempo_inicio__isnull=False,
        tiempo_fin__isnull=False
    )

    tiempos = [p.tiempo_preparacion for p in pedidos if p.tiempo_preparacion]

    if not tiempos:
        return Response({"mensaje": "No hay datos"})

    promedio = sum(tiempos) / len(tiempos)

    return Response({
        "pedidos_analizados": len(tiempos),
        "tiempo_promedio_min": round(promedio, 2),
        "tiempo_maximo_min": round(max(tiempos), 2),
        "tiempo_minimo_min": round(min(tiempos), 2)
    })


# =====================================
# API tiempos de pedidos (últimos 20)
# =====================================
@api_view(['GET'])
def tiempos_pedidos(request):
    pedidos = Pedido.objects.all().order_by('-fecha_hora')[:20]
    serializer = PedidoSerializer(pedidos, many=True)

    datos = [
        {"id": row["id"], "tiempo_preparacion_min": row["tiempo_preparacion_min"]}
        for row in serializer.data
    ]

    return Response(datos)


# =====================================
# Historial de facturas
# =====================================
@api_view(['GET'])
def historial_facturas(request):
    pagos = Pago.objects.select_related('pedido').order_by('-fecha_pago')

    salida = [
        {
            "factura_id": p.id,
            "pedido_id": p.pedido.id,
            "mesa": p.pedido.mesa.numero if p.pedido.mesa else None,
            "monto_pagado": float(p.monto_pagado),
            "metodo_pago": p.metodo_pago,
            "fecha_pago": p.fecha_pago
        }
        for p in pagos
    ]

    return Response(salida)


# =====================================
# Registrar pedido del cliente (App Cliente)
# =====================================
@api_view(['POST'])
def registrar_pedido_cliente(request):
    try:
        # Obtener mesa_id desde sesión o desde el body
        mesa_id = request.session.get("mesa_id") or request.data.get("mesa_id")
        if not mesa_id:
            return Response({"error": "Debe enviar mesa_id o iniciar sesión"}, status=400)

        productos = request.data.get("productos", [])
        if not productos:
            return Response({"error": "Debe enviar productos"}, status=400)

        mesa = Mesa.objects.filter(id=mesa_id).first()
        if not mesa:
            return Response({"error": "Mesa no existe"}, status=404)

        # Tomamos el primer mesero disponible
        mesero = Mesero.objects.first()
        if not mesero:
            return Response({"error": "No hay mesero disponible"}, status=500)

        # Crear pedido
        pedido = Pedido.objects.create(
            mesa=mesa,
            mesero=mesero,
            estado="pendiente",
            total=0
        )

        total = 0
        for item in productos:
            producto = Producto.objects.filter(id=item["producto_id"]).first()
            if not producto:
                continue
            cantidad = int(item["cantidad"])
            subtotal = producto.precio * cantidad
            total += subtotal

            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio
            )

        pedido.total = total
        pedido.save()

        return Response({
            "mensaje": "Pedido registrado correctamente",
            "pedido_id": pedido.id,
            "total": total
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)

# ==========================================================
# 🛑 Vista para la descarga de PDF
# ==========================================================
def descargar_pdf_factura(request, factura_id):
    """
    Genera y devuelve la factura en formato PDF.
    factura_id es el PK del objeto Pago (Factura).
    """

    # --- Obtener la factura ---
    try:
        pago = get_object_or_404(Pago, pk=factura_id)
    except Exception:
        return HttpResponse(
            f"Error: La factura con ID {factura_id} no fue encontrada.",
            status=404
        )

    # --- Preparar datos para la plantilla ---
    context = {
        'factura_id': pago.id,
        'fecha_emision': pago.fecha_pago.strftime("%d/%m/%Y %H:%M:%S"),
        'monto_total': pago.monto_pagado,
        'metodo_pago': pago.metodo_pago,
        'pedido_id': pago.pedido.id,          # Pago → Pedido
        'mesa_numero': pago.pedido.mesa.numero,  # Pedido → Mesa
    }

    # --- Renderizar PDF ---
    pdf = render_to_pdf('factura_template.html', context)

    if pdf:
        filename = f'Factura_Brisa_Caribena_{factura_id}.pdf'
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    return HttpResponse("Error al generar el PDF.", status=500)
def render_to_pdf(template_src, context_dict={}):
    """ Convierte una plantilla HTML renderizada a un objeto PDF usando xhtml2pdf """
    template = get_template(template_src)
    html = template.render(context_dict)
    
    # Crea el objeto HttpResponse que contendrá la respuesta PDF
    result = BytesIO() # 🛑 Necesitas importar BytesIO
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        return result.getvalue()
    return None # Retorna None si hay un error en la conversión


