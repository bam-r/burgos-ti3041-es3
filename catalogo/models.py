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
