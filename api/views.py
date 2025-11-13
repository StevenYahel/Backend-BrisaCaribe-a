from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt

from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate

from .models import (
    Categoria, Producto, Mesa, Mesero,
    Pedido, DetallePedido, Pago
)
from .serializers import (
    CategoriaSerializer, ProductoSerializer, MesaSerializer,
    MeseroSerializer, PedidoSerializer, DetallePedidoSerializer, PagoSerializer
)
from .forms import ProductoForm

# -------------------------------
# ViewSets para API CRUD
# -------------------------------
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

# -------------------------------
# Formularios HTML
# -------------------------------
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

# -------------------------------
# Prueba API
# -------------------------------
def hola_mundo(request):
    return JsonResponse({"mensaje": "Hola desde la API"})

# -------------------------------
# Carrito temporal (solo pruebas)
# -------------------------------
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

# -------------------------------
# Registrar pedido (única versión)
# -------------------------------
@api_view(['POST'])
def registrar_pedido(request):
    """
    Crea un pedido con sus detalles y calcula el total.
    JSON esperado:
    {
        "mesa_id": 1,
        "productos": [
            {"producto_id": 1, "cantidad": 2},
            {"producto_id": 3, "cantidad": 1}
        ]
    }
    """
    try:
        data = request.data
        mesa_id = data.get("mesa_id")
        productos = data.get("productos", [])

        if not mesa_id or not productos:
            return Response({"error": "Faltan campos requeridos"}, status=400)

        # Verificar mesa
        mesa = Mesa.objects.filter(id=mesa_id).first()
        if not mesa:
            return Response({"error": "Mesa no encontrada"}, status=404)

        # Crear pedido
        pedido = Pedido.objects.create(
            mesa=mesa,
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
            "estado": pedido.estado,
            "total": total,
            "detalles": detalles
        }, status=201)

    except Exception as e:
        print("⚠️ Error registrando pedido:", e)
        return Response({"error": str(e)}, status=500)

# -------------------------------
# Pedidos pendientes para cocina
# -------------------------------
@api_view(['GET'])
def pedidos_cocina(request):
    try:
        pedidos = Pedido.objects.filter(estado__in=['pendiente', 'en preparación']).order_by('-id')
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
        print("⚠️ Error en pedidos_cocina:", e)
        return Response({"error": str(e)}, status=500)

# -------------------------------
# Actualizar estado del pedido
# -------------------------------
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
            "mensaje": f"Pedido {pedido_id} actualizado a '{nuevo_estado}'",
            "pedido_id": pedido.id,
            "estado": pedido.estado
        })
    except Exception as e:
        print("⚠️ Error actualizando pedido:", e)
        return Response({"error": str(e)}, status=500)

# -------------------------------
# Mesas disponibles
# -------------------------------
@api_view(['GET'])
def mesas_disponibles(request):
    mesas_ocupadas = Pedido.objects.filter(estado__in=['pendiente', 'en preparación']).values_list('mesa_id', flat=True)
    mesas_libres = Mesa.objects.exclude(id__in=mesas_ocupadas)
    mesas_data = [{"id": m.id, "numero": m.numero} for m in mesas_libres]
    return Response(mesas_data)

# -------------------------------
# Registrar pago
# -------------------------------
@api_view(['POST'])
def registrar_pago(request):
    try:
        data = request.data
        pedido_id = data.get("pedido_id")
        metodo = data.get("metodo_pago")
        monto = data.get("monto_pagado")

        if not all([pedido_id, metodo, monto]):
            return Response({"error": "Faltan campos requeridos"}, status=400)

        pedido = Pedido.objects.filter(id=pedido_id).first()
        if not pedido:
            return Response({"error": "Pedido no encontrado"}, status=404)

        if Pago.objects.filter(pedido=pedido).exists():
            return Response({"error": "El pedido ya tiene un pago registrado"}, status=400)

        pago = Pago.objects.create(
            pedido=pedido,
            metodo_pago=metodo.lower(),
            monto_pagado=monto
        )

        pedido.estado = "pagado"
        pedido.save()

        return Response({
            "mensaje": "Pago registrado correctamente",
            "pago_id": pago.id,
            "pedido_id": pedido.id,
            "estado_pedido": pedido.estado
        }, status=201)
    except Exception as e:
        print("⚠️ Error registrando pago:", e)
        return Response({"error": str(e)}, status=500)

# -------------------------------
# Dashboard y estadísticas
# -------------------------------
@api_view(['GET'])
def resumen_dashboard(request):
    try:
        total_pedidos = Pedido.objects.count()
        total_meseros = Mesero.objects.count()
        ventas_totales = Pago.objects.aggregate(total=Sum('monto_pagado'))['total'] or 0

        return Response({
            "total_pedidos": total_pedidos,
            "meseros_activos": total_meseros,
            "ventas_totales": ventas_totales
        })
    except Exception as e:
        print("❌ Error en resumen_dashboard:", e)
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
def estadisticas_dashboard(request):
    try:
        ventas_por_dia = (
            Pago.objects
            .annotate(fecha=TruncDate('fecha_pago'))
            .values('fecha')
            .annotate(total=Sum('monto_pagado'))
            .order_by('fecha')
        )

        pedidos_por_dia = (
            Pedido.objects
            .annotate(fecha=TruncDate('fecha_hora'))
            .values('fecha')
            .annotate(total=Count('id'))
            .order_by('fecha')
        )

        return Response({
            "ventas_por_dia": list(ventas_por_dia),
            "pedidos_por_dia": list(pedidos_por_dia)
        })
    except Exception as e:
        print("❌ Error en estadisticas_dashboard:", e)
        return Response({"error": str(e)}, status=500)

# -------------------------------
# Login admin
# -------------------------------
@csrf_exempt
def login_admin(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            user = authenticate(username=username, password=password)

            if user and user.is_staff:
                return JsonResponse({'success': True, 'message': 'Inicio de sesión exitoso'})
            else:
                return JsonResponse({'success': False, 'message': 'Credenciales inválidas o usuario no autorizado'}, status=401)
        except Exception as e:
            print("⚠️ Error en login_admin:", e)
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

# -------------------------------
# Pedidos activos por mesero
# -------------------------------
@api_view(['GET'])
def pedidos_por_mesero(request, mesero_id):
    try:
        pedidos = Pedido.objects.filter(mesero_id=mesero_id).order_by('-id')
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
                "total": float(pedido.total),
                "estado": pedido.estado,
                "detalles": detalles_data
            })

        return Response(data)

    except Exception as e:
        print("⚠️ Error en pedidos_por_mesero:", e)
        return Response({"error": str(e)}, status=500)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Pedido

@csrf_exempt
def marcar_entregado(request, pedido_id):
    """
    Cambia el estado del pedido a 'servido'.
    """
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        pedido.estado = "servido"
        pedido.save()

        return JsonResponse({
            "message": "Pedido marcado como entregado (servido).",
            "pedido_id": pedido.id,
            "nuevo_estado": pedido.estado,
        })
    
    except Pedido.DoesNotExist:
        return JsonResponse({"error": "El pedido no existe"}, status=404)
