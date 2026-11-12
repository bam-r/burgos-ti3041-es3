from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Producto, Usuario


class ProductoAdminCRUDTests(TestCase):
	def setUp(self):
		admin_user = get_user_model().objects.create_superuser(
			username='admin_test',
			email='admin@example.com',
			password='test-password',
		)
		self.client.force_login(admin_user)

	def test_admin_can_create_edit_and_delete_producto(self):
		self.assertEqual(self.client.get(reverse('admin:index')).status_code, 200)

		response = self.client.post(reverse('admin:catalogo_producto_add'), {
			'nombre': 'Producto temporal de prueba',
			'categoria': 'Pruebas',
			'precio': '1000',
			'stock': '2',
			'imagen': '/static/catalogo/img/sin-imagen.jpg',
			'activo': 'on',
			'_save': 'Guardar',
		})
		self.assertEqual(response.status_code, 302)
		producto = Producto.objects.get(nombre='Producto temporal de prueba')

		response = self.client.post(
			reverse('admin:catalogo_producto_change', args=[producto.pk]),
			{
				'nombre': producto.nombre,
				'categoria': 'Pruebas editado',
				'precio': '1500',
				'stock': '3',
				'imagen': producto.imagen,
				'activo': 'on',
				'_save': 'Guardar',
			},
		)
		self.assertEqual(response.status_code, 302)
		producto.refresh_from_db()
		self.assertEqual(producto.categoria, 'Pruebas editado')
		self.assertEqual(producto.precio, 1500)
		self.assertEqual(producto.stock, 3)

		delete_url = reverse('admin:catalogo_producto_delete', args=[producto.pk])
		self.assertEqual(self.client.get(delete_url).status_code, 200)
		response = self.client.post(delete_url, {'post': 'yes'})
		self.assertEqual(response.status_code, 302)
		self.assertFalse(Producto.objects.filter(pk=producto.pk).exists())


class CatalogoDatabaseViewsTests(TestCase):
	def setUp(self):
		from . import views

		views.carrito.clear()
		self.producto = Producto.objects.create(
			nombre='Producto solo en SQLite',
			categoria='Pruebas',
			precio=2500,
			stock=5,
			imagen='/static/catalogo/img/sin-imagen.jpg',
			activo=True,
		)
		self.client.cookies['nombre_usuario'] = 'cliente'
		self.client.cookies['rol_usuario'] = 'cliente'

	def tearDown(self):
		from . import views

		views.carrito.clear()

	def test_lista_y_detalle_leen_productos_de_la_base_de_datos(self):
		response = self.client.get(reverse('lista'))
		self.assertContains(response, 'Producto solo en SQLite')

		response = self.client.get(reverse('detalle', args=[self.producto.pk]))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Producto solo en SQLite')

	def test_compra_y_acciones_admin_actualizan_la_base_de_datos(self):
		self.client.cookies['nombre_usuario'] = 'admin'
		self.client.cookies['rol_usuario'] = 'admin'

		response = self.client.post(reverse('comprar', args=[self.producto.pk]))
		self.assertEqual(response.status_code, 302)
		self.producto.refresh_from_db()
		self.assertEqual(self.producto.stock, 4)

		response = self.client.post(
			reverse('agregar_stock', args=[self.producto.pk]),
			{'cantidad': '3'},
		)
		self.assertEqual(response.status_code, 302)
		self.producto.refresh_from_db()
		self.assertEqual(self.producto.stock, 7)

		response = self.client.post(reverse('retirar', args=[self.producto.pk]))
		self.assertEqual(response.status_code, 302)
		self.producto.refresh_from_db()
		self.assertFalse(self.producto.activo)

		response = self.client.post(reverse('reactivar', args=[self.producto.pk]))
		self.assertEqual(response.status_code, 302)
		self.producto.refresh_from_db()
		self.assertTrue(self.producto.activo)

	def test_admin_puede_agregar_producto_desde_la_pagina(self):
		self.client.cookies['nombre_usuario'] = 'admin'
		self.client.cookies['rol_usuario'] = 'admin'

		response = self.client.get(reverse('lista'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Añadir nuevo producto')
		self.assertNotContains(response, 'Ir al Panel de Base de Datos')
		self.assertNotContains(response, 'Django Admin')

		response = self.client.post(
			reverse('agregar_producto'),
			{
				'nombre': 'Nivel láser autonivelante',
				'categoria': 'Medición',
				'precio': '45990',
				'stock': '8',
				'imagen': '',
				'activo': 'on',
			},
		)
		self.assertEqual(response.status_code, 302)
		nuevo = Producto.objects.get(nombre='Nivel láser autonivelante')
		self.assertEqual(nuevo.categoria, 'Medición')
		self.assertEqual(nuevo.precio, 45990)
		self.assertEqual(nuevo.stock, 8)
		self.assertEqual(nuevo.imagen, '/static/catalogo/img/sin-imagen.jpg')
		self.assertTrue(nuevo.activo)

	def test_admin_puede_editar_producto_desde_vista_editar(self):
		self.client.cookies['nombre_usuario'] = 'admin'
		self.client.cookies['rol_usuario'] = 'admin'

		edit_url = reverse('editar_producto', args=[self.producto.pk])
		response = self.client.get(edit_url)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.producto.nombre)

		response = self.client.post(
			edit_url,
			{
				'nombre': 'Producto editado desde admin web',
				'categoria': 'Herramientas manuales',
				'precio': '9990',
				'stock': '25',
				'imagen': '/static/catalogo/img/martillocar.jpg',
				'activo': 'on',
			},
		)
		self.assertEqual(response.status_code, 302)
		self.producto.refresh_from_db()
		self.assertEqual(self.producto.nombre, 'Producto editado desde admin web')
		self.assertEqual(self.producto.categoria, 'Herramientas manuales')
		self.assertEqual(self.producto.precio, 9990)
		self.assertEqual(self.producto.stock, 25)
		self.assertEqual(self.producto.imagen, '/static/catalogo/img/martillocar.jpg')
		self.assertTrue(self.producto.activo)

	def test_acceso_invitado_sin_login_opcional(self):
		self.client.cookies.clear()
		response = self.client.get(reverse('lista'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Producto solo en SQLite')

		response = self.client.get(reverse('detalle', args=[self.producto.pk]))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Producto solo en SQLite')

	def test_login_con_modelo_usuario_y_roles(self):
		self.client.cookies.clear()
		Usuario.objects.create(
			nombreCompleto='Admin Prueba',
			user='admin_db',
			contraseña='clave_admin',
			email='admin_db@example.com',
			activo=True,
			rol='admin',
		)
		Usuario.objects.create(
			nombreCompleto='Usuario Prueba',
			user='user_db',
			contraseña='clave_user',
			email='user_db@example.com',
			activo=True,
			rol='usuario',
		)

		# Login como rol 'admin'
		response = self.client.post(reverse('login'), {
			'user': 'admin_db',
			'contraseña': 'clave_admin',
		})
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.cookies['rol_usuario'].value, 'admin')
		home_admin = self.client.get(reverse('lista'))
		self.assertContains(home_admin, 'Modo Administrador Activo')

		# Login como rol 'usuario'
		response = self.client.post(reverse('login'), {
			'user': 'user_db',
			'contraseña': 'clave_user',
		})
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.cookies['rol_usuario'].value, 'usuario')
		home_user = self.client.get(reverse('lista'))
		self.assertNotContains(home_user, 'Modo Administrador Activo')
		self.assertContains(home_user, 'Usuario Prueba')


