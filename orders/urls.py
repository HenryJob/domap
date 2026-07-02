from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('comprar/', views.checkout, name='checkout'),
    path('resumen-parcial/', views.cart_summary_partial, name='cart_summary_partial'),
    path('confirmacion/<int:order_id>/', views.order_success, name='order_success'),
    path('staff/ventas-whatsapp/', views.manual_sale_list, name='manual_sale_list'),
    path('staff/ventas-whatsapp/nueva/', views.manual_sale_create, name='manual_sale_create'),
]
