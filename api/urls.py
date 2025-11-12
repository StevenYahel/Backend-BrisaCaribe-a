from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'categorias', views.CategoriaViewSet)
router.register(r'productos', views.ProductoViewSet)
router.register(r'mesas', views.MesaViewSet)
router.register(r'meseros', views.MeseroViewSet)
router.register(r'pedidos', views.PedidoViewSet)
router.register(r'detalles', views.DetallePedidoViewSet)
router.register(r'pagos', views.PagoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('crear-producto/', views.crear_producto, name='crear_producto'),
    path('listar-productos/', views.listar_productos, name='listar_productos'),
    path('hola/', views.hola_mundo, name='hola_mundo'),
    path('carrito/', views.obtener_carrito, name='obtener_carrito'),
    path('carrito/agregar/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('registrar-pedido/', views.registrar_pedido, name='registrar_pedido'),
    path('pedidos-cocina/', views.pedidos_cocina, name='pedidos_cocina'),
    path('pedidos/<int:pedido_id>/', views.actualizar_pedido_estado, name='actualizar_pedido_estado'),
    path('registrar-pago/', views.registrar_pago, name='registrar_pago'),
    path('dashboard/resumen/', views.resumen_dashboard, name='resumen_dashboard'),
    path('dashboard/estadisticas/', views.estadisticas_dashboard, name='estadisticas_dashboard'),
    path('login-admin/', views.login_admin, name='login_admin'),
]