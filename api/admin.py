from django.contrib import admin
from .models import Categoria, Producto, Mesa, Mesero, Pedido, DetallePedido, Pago

# === ADMIN DE CATEGORÍAS ===
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'descripcion')
    search_fields = ('nombre',)


# === ADMIN DE PRODUCTOS ===
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'precio', 'categoria', 'disponible')
    search_fields = ('nombre',)
    list_filter = ('categoria', 'disponible')


# === ADMIN DE MESAS ===
@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_display = ('id', 'numero', 'capacidad', 'ubicacion', 'disponible')
    list_filter = ('disponible',)
    search_fields = ('numero',)


# === ADMIN DE MESEROS ===
@admin.register(Mesero)
class MeseroAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'apellido', 'documento_identidad', 'telefono', 'email', 'activo')
    search_fields = ('nombre', 'apellido', 'documento_identidad')
    list_filter = ('activo',)


# === ADMIN DE PEDIDOS ===
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'mesa', 'mesero', 'fecha_hora', 'estado', 'total')
    list_filter = ('estado', 'fecha_hora')
    search_fields = ('mesa__numero', 'mesero__nombre')


# === ADMIN DE DETALLES DE PEDIDO ===
@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'pedido', 'producto', 'cantidad', 'precio_unitario', 'subtotal_display')

    def subtotal_display(self, obj):
        return obj.subtotal()
    subtotal_display.short_description = 'Subtotal'


# === ADMIN DE PAGOS ===
@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'pedido', 'metodo_pago', 'monto_pagado', 'fecha_pago')
    list_filter = ('metodo_pago',)
    search_fields = ('pedido__id',)


# === PERSONALIZACIÓN DEL PANEL ===
admin.site.site_header = "Administración del Sistema Brisa Caribeña"
admin.site.site_title = "Panel Administrativo"
admin.site.index_title = "Gestión de Datos del Restaurante"
