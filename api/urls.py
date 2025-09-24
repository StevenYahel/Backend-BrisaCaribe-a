from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Rutas de los ViewSets
router = DefaultRouter()
router.register(r'categorias', views.CategoriaViewSet)
router.register(r'productos', views.ProductoViewSet)
router.register(r'mesas', views.MesaViewSet)
router.register(r'meseros', views.MeseroViewSet)
router.register(r'pedidos', views.PedidoViewSet)
router.register(r'detalles', views.DetallePedidoViewSet)
router.register(r'pagos', views.PagoViewSet)

urlpatterns = [
    path('hola/', views.hola_mundo),  # Ruta de prueba
    path('', include(router.urls)),   # Incluye las rutas REST
]
