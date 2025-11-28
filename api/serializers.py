from rest_framework import serializers
from django.utils import timezone
from .models import Categoria, Producto, Mesa, Mesero, Pedido, DetallePedido, Pago, Alerta

# -------------------------------
# CATEGORÍAS
# -------------------------------
class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'


# -------------------------------
# PRODUCTOS
# -------------------------------
class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'


# -------------------------------
# MESAS
# -------------------------------
class MesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mesa
        fields = '__all__'


# -------------------------------
# MESEROS
# -------------------------------
class MeseroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mesero
        fields = '__all__'


# -------------------------------
# DETALLE DE PEDIDO
# -------------------------------
class DetallePedidoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = DetallePedido
        fields = ['id', 'producto', 'producto_nombre', 'cantidad', 'precio_unitario', 'subtotal']

    def get_subtotal(self, obj):
        return obj.cantidad * obj.precio_unitario


# -------------------------------
# PEDIDO
# -------------------------------
class DetallePedidoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = DetallePedido
        fields = ['id', 'producto', 'producto_nombre', 'cantidad', 'precio_unitario', 'subtotal']

    def get_subtotal(self, obj):
        return obj.cantidad * obj.precio_unitario


class PedidoSerializer(serializers.ModelSerializer):
    mesa = serializers.PrimaryKeyRelatedField(queryset=Mesa.objects.all())
    mesero = serializers.PrimaryKeyRelatedField(queryset=Mesero.objects.all())
    detalles = DetallePedidoSerializer(many=True, read_only=True)
    tiempo_transcurrido_min = serializers.SerializerMethodField()
    tiempo_preparacion_min = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = [
            'id',
            'mesa',
            'mesero',
            'estado',
            'total',
            'fecha_hora',
            'hora_inicio_preparacion',
            'hora_fin_preparacion',
            'detalles',
            'tiempo_transcurrido_min',
            'tiempo_preparacion_min',
        ]

    def get_tiempo_transcurrido_min(self, obj):
        if obj.fecha_hora:
            return round((timezone.now() - obj.fecha_hora).total_seconds() / 60, 2)
        return None

    def get_tiempo_preparacion_min(self, obj):
        if obj.hora_inicio_preparacion and obj.hora_fin_preparacion:
            return round((obj.hora_fin_preparacion - obj.hora_inicio_preparacion).total_seconds() / 60, 2)
        return None

# -------------------------------
# PAGO
# -------------------------------
class PagoSerializer(serializers.ModelSerializer):
    pedido_id = serializers.IntegerField(source='pedido.id', read_only=True)
    mesa = serializers.IntegerField(source='pedido.mesa.numero', read_only=True)
    estado_pedido = serializers.CharField(source='pedido.estado', read_only=True)
    total_pedido = serializers.DecimalField(source='pedido.total', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Pago
        fields = [
            'id',
            'pedido_id',
            'mesa',
            'metodo_pago',
            'monto_pagado',
            'total_pedido',
            'estado_pedido',
            'fecha_pago',
            'observaciones'
        ]


# -------------------------------
# ALERTAS
# -------------------------------
class AlertaSerializer(serializers.ModelSerializer):
    minutos_transcurridos = serializers.SerializerMethodField()

    class Meta:
        model = Alerta
        fields = ['id', 'pedido', 'tiempo_estimado', 'alerta_retraso', 'minutos_transcurridos']

    def get_minutos_transcurridos(self, obj):
        return obj.minutos_transcurridos
