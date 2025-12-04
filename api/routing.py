from django.urls import path
from .consumers import PedidoConsumer

websocket_urlpatterns = [
    path("ws/pedidos/", PedidoConsumer.as_asgi()),
]
