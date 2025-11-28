from django.db import models
from django.utils import timezone

# ===============================
# MÓDULO MENÚ
# ===============================
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


# ===============================
# MÓDULO MESAS Y MESEROS
# ===============================
class Mesa(models.Model):
    numero = models.PositiveIntegerField(unique=True)
    capacidad = models.PositiveIntegerField(default=2)
    ubicacion = models.CharField(max_length=100, blank=True)
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return f"Mesa {self.numero} (Capacidad: {self.capacidad})"


class Mesero(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    documento_identidad = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


# ===============================
# MÓDULO PEDIDOS
# ===============================
class Pedido(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('en_preparacion', 'En preparación'),
        ('servido', 'Servido'),
        ('pagado', 'Pagado'),
        ('cancelado', 'Cancelado'),
        ('retrasado', 'Retrasado')
    ]

    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE, related_name="pedidos", null=True, blank=True)
    mesero = models.ForeignKey(Mesero, on_delete=models.SET_NULL, null=True, related_name="pedidos")
    fecha_hora = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hora_inicio_preparacion = models.DateTimeField(null=True, blank=True)
    hora_fin_preparacion = models.DateTimeField(null=True, blank=True)

    def calcular_total(self):
        total = sum(detalle.subtotal() for detalle in self.detalles.all())
        self.total = total
        self.save()

    @property
    def tiempo_transcurrido_min(self):
        return (timezone.now() - self.fecha_hora).total_seconds() / 60

    @property
    def tiempo_preparacion(self):
        if self.hora_inicio_preparacion and self.hora_fin_preparacion:
            return (self.hora_fin_preparacion - self.hora_inicio_preparacion).total_seconds() / 60
        return None

    def marcar_inicio_preparacion(self):
        if not self.hora_inicio_preparacion:
            self.hora_inicio_preparacion = timezone.now()
            self.save()

    def marcar_fin_preparacion(self):
        if not self.hora_fin_preparacion:
            self.hora_fin_preparacion = timezone.now()
            self.save()

    def __str__(self):
        mesa_num = self.mesa.numero if self.mesa else "N/A"
        return f"Pedido #{self.id} - Mesa {mesa_num} - {self.estado}"

    def save(self, *args, **kwargs):
        # --- REGISTRO AUTOMÁTICO DE TIEMPOS ---
        
        if self.estado == "en_preparacion" and not self.hora_inicio_preparacion:
            self.hora_inicio_preparacion = timezone.now()

        if self.estado == "servido" and not self.hora_fin_preparacion:
            self.hora_fin_preparacion = timezone.now()

        super().save(*args, **kwargs)




# ===============================
# DETALLE DE PEDIDO (Faltaba)
# ===============================
class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} (Pedido #{self.pedido.id})"


# ===============================
# MÓDULO PAGOS
# ===============================
class Pago(models.Model):
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

    def es_completo(self):
        return self.monto_pagado >= self.pedido.total

    def __str__(self):
        return f"Pago de Pedido #{self.pedido.id} - {self.metodo_pago}"


# ===============================
# MÓDULO PRODUCTOS (extra)
# ===============================
class Productos(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    disponible = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"


# ===============================
# MÓDULO ALERTAS
# ===============================
class Alerta(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="alertas")
    tiempo_estimado = models.IntegerField(default=15)  # minutos
    alerta_retraso = models.BooleanField(default=False)

    @property
    def minutos_transcurridos(self):
        return (timezone.now() - self.pedido.fecha_hora).total_seconds() / 60
