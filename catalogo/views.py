from django.db.models import F
from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect

from .models import Producto

carrito = {}  # {id_producto: cantidad} — en memoria, sin sesión ni base de datos


def obtener_carrito():
    productos = Producto.objects.in_bulk(carrito)
    items = []
    for producto_id, cantidad in carrito.items():
        if producto_id in productos:
            prod = productos[producto_id]
            items.append({
                'producto': prod,
                'cantidad': cantidad,
                'subtotal': prod.precio * cantidad,
            })
    return items


def resumen_carrito(items_carrito=None):
    if items_carrito is None:
        items_carrito = obtener_carrito()
    total_unidades = sum(item['cantidad'] for item in items_carrito)
    total_precio = sum(item['producto'].precio * item['cantidad'] for item in items_carrito)
    return {
        'items': items_carrito,
        'cantidad_total': total_unidades,
        'precio_total': total_precio,
    }


def usuario_actual(request):
    """Lee el usuario logeado desde las cookies del navegador (sin sesión, sin BD)."""
    nombre = request.COOKIES.get('nombre_usuario')
    rol = request.COOKIES.get('rol_usuario')
    if not nombre:
        return None
    return {'nombre': nombre, 'rol': rol or 'cliente'}


def login_view(request):
    error = None
    if request.method == 'POST':
        nombre = request.POST.get('usuario', '').strip()
        if nombre:
            rol = 'admin' if nombre.lower() == 'admin' else 'cliente'
            next_url = request.POST.get('next') or 'lista'
            respuesta = redirect(next_url)
            respuesta.set_cookie('nombre_usuario', nombre, max_age=60 * 60 * 8)
            respuesta.set_cookie('rol_usuario', rol, max_age=60 * 60 * 8)
            return respuesta
        error = 'Ingresa un nombre o identificador para continuar.'
    return render(request, 'catalogo/login.html', {
        'error': error,
        'usuario': usuario_actual(request),
    })


def logout_view(request):
    respuesta = redirect('lista')
    respuesta.delete_cookie('nombre_usuario')
    respuesta.delete_cookie('rol_usuario')
    return respuesta


def lista(request):
    usuario = usuario_actual(request)
    es_admin = usuario is not None and usuario.get('rol') == 'admin'

    productos_visibles = Producto.objects.all()
    if not es_admin:
        productos_visibles = productos_visibles.filter(activo=True)

    total_productos = productos_visibles.count()
    disponibles = productos_visibles.filter(stock__gt=0).count()

    categorias = list(
        productos_visibles.values_list('categoria', flat=True).distinct()
    )

    destacados = list(
        productos_visibles.filter(activo=True, stock__gt=0).order_by('-precio')[:4]
    )

    resumen = {
        'total': total_productos,
        'disponibles': disponibles,
        'sin_stock': total_productos - disponibles,
        'categorias_count': len(categorias),
    }

    items_carrito = obtener_carrito()
    datos_carrito = resumen_carrito(items_carrito)

    contexto = {
        'productos': productos_visibles,
        'categorias': categorias,
        'destacados': destacados,
        'resumen': resumen,
        'carrito': items_carrito,
        'carrito_total': datos_carrito['precio_total'],
        'carrito_cantidad': datos_carrito['cantidad_total'],
        'usuario': usuario,
    }
    return render(request, 'catalogo/lista.html', contexto)


def detalle(request, producto_id):
    usuario = usuario_actual(request)
    es_admin = usuario is not None and usuario.get('rol') == 'admin'

    producto = get_object_or_404(Producto, pk=producto_id)

    if not producto.activo and not es_admin:
        raise Http404("El producto solicitado no existe en el catálogo.")

    relacionados_qs = Producto.objects.filter(
        activo=True,
        categoria=producto.categoria,
    ).exclude(pk=producto.pk)[:4]

    relacionados = list(relacionados_qs)
    if len(relacionados) < 4:
        ids_excluidos = [producto.pk] + [p.pk for p in relacionados]
        extras = Producto.objects.filter(activo=True).exclude(pk__in=ids_excluidos)[:4 - len(relacionados)]
        relacionados.extend(list(extras))

    items_carrito = obtener_carrito()
    datos_carrito = resumen_carrito(items_carrito)

    contexto = {
        'producto': producto,
        'relacionados': relacionados,
        'carrito': items_carrito,
        'carrito_total': datos_carrito['precio_total'],
        'carrito_cantidad': datos_carrito['cantidad_total'],
        'usuario': usuario,
    }
    return render(request, 'detalles.html', contexto)


def comprar(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)

    if request.method == 'POST':
        actualizado = Producto.objects.filter(
            pk=producto.pk,
            activo=True,
            stock__gt=0,
        ).update(stock=F('stock') - 1)
        if actualizado:
            carrito[producto_id] = carrito.get(producto_id, 0) + 1

    return redirect(request.META.get('HTTP_REFERER', 'lista'))


def eliminar_carrito(request, producto_id):
    if request.method == 'POST':
        cantidad_en_carrito = carrito.pop(producto_id, 0)
        if cantidad_en_carrito > 0:
            Producto.objects.filter(pk=producto_id).update(
                stock=F('stock') + cantidad_en_carrito
            )
    return redirect(request.META.get('HTTP_REFERER', 'lista'))


def vaciar_carrito(request):
    if request.method == 'POST':
        for prod_id, cant in list(carrito.items()):
            if cant > 0:
                Producto.objects.filter(pk=prod_id).update(stock=F('stock') + cant)
        carrito.clear()
    return redirect(request.META.get('HTTP_REFERER', 'lista'))


def finalizar_compra(request):
    if request.method == 'POST':
        carrito.clear()
    return redirect(request.META.get('HTTP_REFERER', 'lista'))


def retirar(request, producto_id):
    usuario = usuario_actual(request)
    if usuario is None or usuario['rol'] != 'admin':
        return redirect('login')

    producto = get_object_or_404(Producto, pk=producto_id)

    if request.method == 'POST':
        producto.activo = False
        producto.save(update_fields=['activo'])

    return redirect(request.META.get('HTTP_REFERER', 'lista'))


def reactivar(request, producto_id):
    usuario = usuario_actual(request)
    if usuario is None or usuario['rol'] != 'admin':
        return redirect('login')

    producto = get_object_or_404(Producto, pk=producto_id)

    if request.method == 'POST':
        producto.activo = True
        producto.save(update_fields=['activo'])

    return redirect(request.META.get('HTTP_REFERER', 'lista'))


def agregar_stock(request, producto_id):
    usuario = usuario_actual(request)
    if usuario is None or usuario['rol'] != 'admin':
        return redirect('login')

    producto = get_object_or_404(Producto, pk=producto_id)

    if request.method == 'POST':
        try:
            cantidad = int(request.POST.get('cantidad', 1))
        except ValueError:
            cantidad = 0
        if cantidad > 0:
            Producto.objects.filter(pk=producto.pk).update(stock=F('stock') + cantidad)

    return redirect(request.META.get('HTTP_REFERER', 'lista'))


def agregar_producto(request):
    usuario = usuario_actual(request)
    if usuario is None or usuario['rol'] != 'admin':
        return redirect('login')

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        categoria = request.POST.get('categoria', '').strip()
        imagen = request.POST.get('imagen', '').strip() or '/static/catalogo/img/sin-imagen.jpg'
        activo = request.POST.get('activo') in ('on', 'true', '1', True)

        try:
            precio = int(request.POST.get('precio', 0))
            stock = int(request.POST.get('stock', 0))
        except ValueError:
            precio = -1
            stock = -1

        if nombre and categoria and precio >= 0 and stock >= 0:
            Producto.objects.create(
                nombre=nombre,
                categoria=categoria,
                precio=precio,
                stock=stock,
                imagen=imagen,
                activo=activo,
            )

    return redirect(request.META.get('HTTP_REFERER', 'lista'))

