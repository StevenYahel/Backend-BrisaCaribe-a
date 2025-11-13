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
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = DetallePedido
        fields = ['id', 'producto', 'producto_nombre', 'cantidad', 'precio_unitario', 'subtotal']

    def get_subtotal(self, obj):
        return obj.cantidad * obj.precio_unitario

class PedidoSerializer(serializers.ModelSerializer):
    mesa = MesaSerializer(read_only=True)
    mesero = MeseroSerializer(read_only=True)
    detalles = DetallePedidoSerializer(many=True, read_only=True)  # usa el related_name definido en el modelo
    nombre_cliente = serializers.CharField(source='mesero.nombre', read_only=True)

    class Meta:
        model = Pedido
        fields = ['id', 'nombre_cliente', 'mesa', 'mesero', 'estado', 'total', 'fecha_hora', 'detalles']

class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = '__all__'
