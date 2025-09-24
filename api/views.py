from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse

def hola_mundo(request):
    return JsonResponse({"mensaje": "Hola desde la API"})

from rest_framework import viewsets
from .models import Categoria, Producto, Mesa, Mesero, Pedido, DetallePedido, Pago
from .serializers import (
    CategoriaSerializer, ProductoSerializer, MesaSerializer,
    MeseroSerializer, PedidoSerializer, DetallePedidoSerializer, PagoSerializer
)

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
