from django.db import models


class Producto(models.Model):
	nombre = models.CharField(max_length=150)
	categoria = models.CharField(max_length=100)
	precio = models.PositiveIntegerField()
	stock = models.PositiveIntegerField()
	imagen = models.CharField(
		max_length=255,
		default='/static/catalogo/img/sin-imagen.jpg',
	)
	activo = models.BooleanField(default=True)

	def __str__(self):
		return self.nombre

class Usuario(models.Model):
	nombreCompleto = models.CharField(max_length=150)
	user = models.CharField(max_length=100)
	contraseña = models.CharField(max_length=100)
	email = models.EmailField()
	activo = models.BooleanField(default=True)
	rol = models.CharField(max_length=50, default='usuario')


	def __str__(self):
		return self.user

class ConsultaCliente(models.Model):
	nombre = models.CharField(max_length=150)
	email = models.EmailField()
	mensaje = models.TextField()
	productoInteres = models.ForeignKey(Producto, null=True, blank=True, on_delete=models.SET_NULL)
	fecha = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.nombre