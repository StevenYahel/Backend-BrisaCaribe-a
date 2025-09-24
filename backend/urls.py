from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def pagina_inicio(request):
    return HttpResponse("<h1>Servidor Backend Brisa Caribeña funcionando ✅</h1>")

urlpatterns = [
    path('', pagina_inicio),  # Página de bienvenida
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),  # Rutas de la app API
]
 