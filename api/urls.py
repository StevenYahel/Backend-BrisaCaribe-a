from django.urls import path, include
from rest_framework import routers
from . import views

# -------------------------------
# Router automático para CRUDs
# -------------------------------
router = routers.DefaultRouter()
router.register(r'categorias', views.CategoriaViewSet)
router.register(r'productos', views.ProductoViewSet)
router.register(r'mesas', views.MesaViewSet)
router.register(r'meseros', views.MeseroViewSet)
router.register(r'pedidos', views.PedidoViewSet)
router.register(r'detalles', views.DetallePedidoViewSet)
router.register(r'pagos', views.PagoViewSet)

# -------------------------------
# Rutas URL
# -------------------------------
urlpatterns = [
    # Endpoints personalizados para el carrito / cliente (van primero)
    path('pedidos/crear/', views.registrar_pedido, name='registrar_pedido'),
    path('pedidos-cocina/', views.pedidos_cocina, name='pedidos_cocina'),
   path('pedidos/<int:pedido_id>/actualizar/', views.actualizar_pedido_estado, name='actualizar_pedido_estado'),

    # Mesas disponibles para el frontend
    path('mesas/disponibles/', views.mesas_disponibles, name='mesas_disponibles'),

    # Rutas automáticas del router (CRUD estándar)
    path('', include(router.urls)),

    # Rutas HTML o pruebas
    path('hola/', views.hola_mundo, name='hola_mundo'),
    path('carrito/', views.obtener_carrito, name='obtener_carrito'),
    path('carrito/agregar/', views.agregar_al_carrito, name='agregar_al_carrito'),

    # Formularios HTML
    path('productos/crear/', views.crear_producto, name='crear_producto'),
    path('productos/listar/', views.listar_productos, name='listar_productos'),

    # Dashboard
    path('dashboard/resumen/', views.resumen_dashboard, name='resumen_dashboard'),
    path('dashboard/estadisticas/', views.estadisticas_dashboard, name='estadisticas_dashboard'),

    # Login admin
    path('login-admin/', views.login_admin, name='login_admin'),

    # Pagos
    path('pagos/registrar/', views.registrar_pago, name='registrar_pago'),
]

# -------------------------------
# Rutas para el panel del mesero
# -------------------------------
urlpatterns += [
    # Pedidos creados por el mesero
    path('pedidos/mesero/<int:mesero_id>/', views.pedidos_por_mesero, name='pedidos_por_mesero'),

    # Marcar pedido como entregado
    path('pedidos/<int:pedido_id>/entregar/', views.marcar_entregado, name='marcar_entregado'),
]