from rest_framework import serializers
from .models import Categoria, Producto, Mesa, Mesero, Pedido, DetallePedido, Pago

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

class MesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mesa
        fields = '__all__'

class MeseroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mesero
        fields = '__all__'

class DetallePedidoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = DetallePedido
        fields = ['id', 'producto', 'producto_nombre', 'cantidad', 'subtotal']

class PedidoSerializer(serializers.ModelSerializer):
    mesa = MesaSerializer(read_only=True)
    mesero = MeseroSerializer(read_only=True)
    detalles = DetallePedidoSerializer(many=True, source='detallepedido_set', read_only=True)

    class Meta:
        model = Pedido
        fields = ['id', 'nombre_cliente', 'mesa', 'mesero', 'estado', 'total', 'fecha_creacion', 'detalles']

class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = '__all__'