from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('beacon/duracion/', views.record_duration, name='record_duration'),
    path('evento/whatsapp-click/', views.log_whatsapp_click, name='log_whatsapp_click'),
    path('evento/instagram-click/', views.log_instagram_click, name='log_instagram_click'),
    path('panel/', views.dashboard, name='dashboard'),
]
