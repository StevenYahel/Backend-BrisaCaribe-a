from django.db import models
from django.utils import timezone




# Modulo del Menu #

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """
    Representa un ítem del menú.
    """
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    disponible = models.BooleanField(default=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name="productos")

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"







# Modulo de Mesas y Meseros #

class Mesa(models.Model):
    numero = models.PositiveIntegerField(unique=True)  # Ej: Mesa 1, Mesa 2
    capacidad = models.PositiveIntegerField(default=2)  # Número de personas
    ubicacion = models.CharField(max_length=100, blank=True)  
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return f"Mesa {self.numero} (Capacidad: {self.capacidad})"

class Mesero(models.Model):
    """
    Representa un mesero del restaurante.
    """
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    documento_identidad = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"







# Modulo de Pedidos #

class Pedido(models.Model):
    """
    Representa un pedido realizado en el restaurante.
    """
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('en_preparacion', 'En preparación'),
        ('servido', 'Servido'),
        ('pagado', 'Pagado'),
        ('cancelado', 'Cancelado'),
    ]

    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE, related_name="pedidos", null=True, blank=True)
    mesero = models.ForeignKey(Mesero, on_delete=models.SET_NULL, null=True, related_name="pedidos")
    fecha_hora = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def calcular_total(self):
        """
        Calcula el total del pedido sumando los precios de los detalles.
        """
        total = sum(detalle.subtotal() for detalle in self.detalles.all())
        self.total = total
        self.save()

    def __str__(self):
        return f"Pedido #{self.id} - Mesa {self.mesa.numero} - {self.estado}"


class DetallePedido(models.Model):
    """
    Representa un producto dentro de un pedido.
    """
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="detalles") # type: ignore
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        """
        Calcula el subtotal de este producto.
        """
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} (Pedido #{self.pedido.id})"
    

from django.http import JsonResponse
from .models import Pedido

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


# Módulo de Pagos #

class Pago(models.Model):
    """
    Representa un pago realizado por un cliente.
    """
    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
        ('qr', 'Código QR'),
    ]

    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name="pago")
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField(default=timezone.now)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Pago de Pedido #{self.pedido.id} - {self.metodo_pago}"

    def es_completo(self):
        """
        Retorna True si el pago cubre el total del pedido.
        """
        return self.monto_pagado >= self.pedido.total
class Productos(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    disponible = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
