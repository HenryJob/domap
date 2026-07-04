from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('comprar/', views.checkout, name='checkout'),
    path('resumen-parcial/', views.cart_summary_partial, name='cart_summary_partial'),
    path('confirmacion/<int:order_id>/', views.order_success, name='order_success'),
    path('rastrear/', views.order_lookup, name='order_lookup'),
    path('staff/ventas-whatsapp/', views.manual_sale_list, name='manual_sale_list'),
    path('staff/ventas-whatsapp/nueva/', views.manual_sale_create, name='manual_sale_create'),
    path('staff/whatsapp/', views.whatsapp_connect, name='whatsapp_connect'),
    path('staff/whatsapp/estado/', views.whatsapp_state, name='whatsapp_state'),
    path('staff/whatsapp/desconectar/', views.whatsapp_logout, name='whatsapp_logout'),
    path('staff/whatsapp/reiniciar/', views.whatsapp_restart, name='whatsapp_restart'),
    path('staff/whatsapp/prueba/', views.whatsapp_test, name='whatsapp_test'),
]
