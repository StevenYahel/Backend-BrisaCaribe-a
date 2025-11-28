from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from pedidos.consumers import PedidoConsumer

application = ProtocolTypeRouter({
    "websocket": URLRouter([
        path("ws/pedidos/", PedidoConsumer.as_asgi()),
    ])
})
