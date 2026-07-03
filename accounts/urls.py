from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('registro/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='core:home'), name='logout'),
    path('perfil/', views.profile, name='profile'),
    path('perfil/direcciones/nueva/', views.address_add, name='address_add'),
    path('perfil/direcciones/<int:address_id>/editar/', views.address_edit, name='address_edit'),
    path('perfil/direcciones/<int:address_id>/eliminar/', views.address_delete, name='address_delete'),
    path('pedidos/', views.order_history, name='order_history'),
]
