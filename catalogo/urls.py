from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista, name='lista'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('producto/<int:producto_id>/', views.detalle, name='detalle'),
    path('comprar/<int:producto_id>/', views.comprar, name='comprar'),
    path('carrito/eliminar/<int:producto_id>/', views.eliminar_carrito, name='eliminar_carrito'),
    path('carrito/vaciar/', views.vaciar_carrito, name='vaciar_carrito'),
    path('carrito/finalizar/', views.finalizar_compra, name='finalizar_compra'),
    path('retirar/<int:producto_id>/', views.retirar, name='retirar'),
    path('reactivar/<int:producto_id>/', views.reactivar, name='reactivar'),
    path('agregar-stock/<int:producto_id>/', views.agregar_stock, name='agregar_stock'),
    path('agregar-producto/', views.agregar_producto, name='agregar_producto'),
    path('editar/<int:producto_id>/', views.editar_producto, name='editar_producto'),
]
