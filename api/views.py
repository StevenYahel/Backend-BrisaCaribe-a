from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
import json

from .models import Categoria, Producto, Mesa, Mesero, Pedido, DetallePedido, Pago
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
# Carrito temporal
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
# Registrar pedido
# -------------------------------
@csrf_exempt
@api_view(['POST'])
def registrar_pedido(request):
    """
    JSON esperado:
    {
        "mesero": "Juan",
        "mesa": 1,
        "items": [
            {"id": 1, "cantidad": 2},
            {"id": 3, "cantidad": 1}
        ]
    }
    """
    try:
        data = request.data
        items = data.get('items', [])
        mesa_numero = data.get('mesa')
        mesero_nombre = data.get('mesero')

        mesa = Mesa.objects.filter(numero=mesa_numero).first() if mesa_numero else None
        mesero = Mesero.objects.filter(nombre__iexact=mesero_nombre).first() if mesero_nombre else None

        if not mesa or not mesero:
            return Response({"error": "Mesa o mesero no encontrados"}, status=404)

        pedido = Pedido.objects.create(
            mesa=mesa,
            mesero=mesero,
            estado="pendiente"
        )

        total = 0
        for item in items:
            producto = Producto.objects.get(id=item['id'])
            cantidad = int(item.get('cantidad', 1))
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

        carrito.clear()  # limpiar carrito

        return Response({"mensaje": "Pedido registrado correctamente", "id_pedido": pedido.id}, status=status.HTTP_201_CREATED)

    except Producto.DoesNotExist:
        return Response({"error": "Producto no encontrado"}, status=404)
    except Exception as e:
        print("⚠️ Error al registrar pedido:", e)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# -------------------------------
# Pedidos pendientes para cocina
# -------------------------------
@api_view(['GET'])
def pedidos_cocina(request):
    try:
        pedidos = Pedido.objects.filter(estado='pendiente').order_by('id')
        pedidos_list = []

        for pedido in pedidos:
            detalles = [
                {
                    "producto_nombre": d.producto.nombre,
                    "cantidad": d.cantidad,
                    "subtotal": float(d.precio_unitario * d.cantidad)
                } for d in pedido.detalles.all()
            ]

            pedidos_list.append({
                "id": pedido.id,
                "mesa": pedido.mesa.numero,
                "mesero": pedido.mesero.nombre,
                "total": float(pedido.total),
                "detalles": detalles
            })

        return Response(pedidos_list)
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
# Dashboard
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
