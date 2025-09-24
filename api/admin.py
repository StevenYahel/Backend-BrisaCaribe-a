from django.contrib import admin
from .models import Categoria, Producto, Mesa, Mesero, Pedido, DetallePedido, Pago

admin.site.register(Categoria)
admin.site.register(Producto)
admin.site.register(Mesa)
admin.site.register(Mesero)
admin.site.register(Pedido)
admin.site.register(DetallePedido)
admin.site.register(Pago)
