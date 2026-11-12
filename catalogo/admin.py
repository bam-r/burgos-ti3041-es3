from django.contrib import admin
from .models import Producto, Usuario


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
	list_display = ('nombre', 'categoria', 'precio', 'stock', 'activo')
	search_fields = ('nombre', 'categoria')
	list_filter = ('categoria', 'activo')


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
	list_display = ('nombreCompleto', 'user', 'email', 'rol', 'activo')
	search_fields = ('nombreCompleto', 'user', 'email')
	list_filter = ('rol', 'activo')

