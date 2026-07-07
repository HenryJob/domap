from django.urls import path

from . import views

app_name = 'panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('analitica/', views.analytics, name='analytics'),

    path('productos/', views.product_list, name='product_list'),
    path('productos/nuevo/', views.product_form, name='product_create'),
    path('productos/<int:pk>/editar/', views.product_form, name='product_edit'),
    path('productos/<int:pk>/eliminar/', views.product_delete, name='product_delete'),

    path('extras/', views.extra_list, name='extra_list'),
    path('extras/nuevo/', views.extra_form, name='extra_create'),
    path('extras/<int:pk>/editar/', views.extra_form, name='extra_edit'),
    path('extras/<int:pk>/eliminar/', views.extra_delete, name='extra_delete'),

    path('pedidos/', views.order_list, name='order_list'),
    path('pedidos/<int:pk>/', views.order_detail, name='order_detail'),

    path('zonas/', views.zone_list, name='zone_list'),
    path('zonas/nueva/', views.zone_form, name='zone_create'),
    path('zonas/<int:pk>/editar/', views.zone_form, name='zone_edit'),
    path('zonas/<int:pk>/eliminar/', views.zone_delete, name='zone_delete'),

    path('whatsapp/', views.whatsapp, name='whatsapp'),

    path('ventas-manuales/', views.manual_sale_list, name='manual_sale_list'),
    path('ventas-manuales/nueva/', views.manual_sale_create, name='manual_sale_create'),
]
