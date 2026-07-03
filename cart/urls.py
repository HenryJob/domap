from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    path('agregar/', views.cart_add, name='cart_add'),
    path('actualizar/<int:line_id>/', views.cart_update, name='cart_update'),
    path('eliminar/<int:line_id>/', views.cart_remove, name='cart_remove'),
    path('lista-deseos/alternar/', views.wishlist_toggle, name='wishlist_toggle'),
]
