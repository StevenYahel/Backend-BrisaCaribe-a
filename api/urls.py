from django.urls import path, include
from rest_framework import routers
from . import views
from .views import PedidosPorUsuarioView, pedidos_por_mesa

# Routers para CRUD (admin)
router = routers.DefaultRouter()
router.register(r'categorias', views.CategoriaViewSet)
router.register(r'productos', views.ProductoViewSet)
router.register(r'mesas', views.MesaViewSet)
router.register(r'meseros', views.MeseroViewSet)
router.register(r'pedidos', views.PedidoViewSet)
router.register(r'detalles', views.DetallePedidoViewSet)
router.register(r'pagos', views.PagoViewSet)

urlpatterns = [

    # --------------------------
    # PEDIDOS
    # --------------------------
    path('pedidos/crear/', views.registrar_pedido, name='registrar_pedido'),
    path('pedidos-cocina/', views.pedidos_cocina, name='pedidos_cocina'),
    path('pedidos/<int:pk>/estado/', views.actualizar_pedido_estado, name='actualizar_pedido_estado'),
    path('pedidos/mesero/<int:mesero_id>/', views.pedidos_por_mesero, name='pedidos_por_mesero'),
    path('pedidos/usuario/<int:id_usuario>/', PedidosPorUsuarioView.as_view(), name='pedidos_por_usuario'),
    path('pedidos/cliente/', views.pedidos_cliente, name='pedidos_cliente'),
    path('pedidos/cliente/crear/', views.registrar_pedido_cliente, name='registrar_pedido_cliente'),
    path('pedidos-mesa/', pedidos_por_mesa, name='pedidos_por_mesa'),

    # --------------------------
    # MESAS
    # --------------------------
    path('mesas/disponibles/', views.mesas_disponibles, name='mesas_disponibles'),

    # --------------------------
    # CARRITO
    # --------------------------
    path('carrito/', views.obtener_carrito, name='obtener_carrito'),
    path('carrito/agregar/', views.agregar_al_carrito, name='agregar_al_carrito'),

    # --------------------------
    # PRODUCTOS
    # --------------------------
    path('productos/crear/', views.crear_producto, name='crear_producto'),
    path('productos/listar/', views.listar_productos, name='listar_productos'),

    # --------------------------
    # DASHBOARD
    # --------------------------
    path('dashboard/resumen/', views.resumen_dashboard, name='resumen_dashboard'),
    path('dashboard/estadisticas/', views.estadisticas_dashboard, name='estadisticas_dashboard'),

    # --------------------------
    # LOGIN
    # --------------------------
    path('login-admin/', views.login_admin, name='login_admin'),
    path('login_cliente/', views.login_cliente, name='login_cliente'),

    # --------------------------
    # PAGOS
    # --------------------------
    path('pagos/registrar/', views.registrar_pago, name='registrar_pago'),
    # 🛑 CORRECCIÓN: Se elimina el prefijo 'api/' de esta línea.
    path('factura/<int:factura_id>/', views.descargar_pdf_factura, name='descargar_pdf_factura'),

    # --------------------------
    # CLIENTES
    # --------------------------
    path('registrar_cliente/', views.registrar_cliente, name='registrar_cliente'),
    path('pedidos-cliente/', views.pedidos_cliente, name='pedidos_cliente'),

    # --------------------------
    # TIEMPOS / ALERTAS
    # --------------------------
    path('verificar-retrasos/', views.verificar_retrasos, name='verificar_retrasos'),
    path('pedidos/tiempos/', views.tiempos_pedidos, name='tiempos_pedidos'),

    # --------------------------
    # HISTORIAL
    # --------------------------
    path('historial-facturas/', views.historial_facturas, name='historial_facturas'),

    # --------------------------
    # ROUTER
    # --------------------------
    path('', include(router.urls)),
]