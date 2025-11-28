import json
from channels.generic.websocket import AsyncWebsocketConsumer

class PedidoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Todos los clientes y cocina se unen al mismo grupo global de pedidos
        self.group_name = "pedidos_grupo"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print(f"WebSocket conectado: {self.channel_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print(f"WebSocket desconectado: {self.channel_name}")

    # Recibir mensaje desde cliente (opcional)
    async def receive(self, text_data):
        data = json.loads(text_data)
        print("Mensaje recibido desde cliente:", data)
      
    # Método para enviar alertas a todos los clientes del grupo
    async def enviar_alerta(self, event):
        # event['mensaje'] contiene el diccionario de alerta
        await self.send(text_data=json.dumps({
            'mensaje': event['mensaje']
        }))
