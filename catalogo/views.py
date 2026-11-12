import json
from django.db.models import Avg, Count, F, Sum
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_exempt

from .models import Producto, Usuario

carrito = {} 


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
    """Obtiene el usuario autenticado desde el modelo Usuario en la base de datos o cookies."""
    usuario_id = request.COOKIES.get('usuario_id')
    if usuario_id and usuario_id.isdigit():
        usuario_db = Usuario.objects.filter(pk=int(usuario_id), activo=True).first()
        if usuario_db:
            return {
                'id': usuario_db.pk,
                'nombre': usuario_db.nombreCompleto or usuario_db.user,
                'user': usuario_db.user,
                'email': usuario_db.email,
                'rol': usuario_db.rol,
            }

    nombre = request.COOKIES.get('nombre_usuario')
    rol = request.COOKIES.get('rol_usuario')
    if not nombre:
        return None
    return {
        'nombre': nombre,
        'user': request.COOKIES.get('user_login', nombre),
        'rol': rol or 'usuario',
    }


def login_view(request):
    error = None

    if request.method == 'POST':
        user_input = (request.POST.get('user') or request.POST.get('usuario') or '').strip()
        contraseña_input = (request.POST.get('contraseña') or request.POST.get('password') or '').strip()

        if user_input and contraseña_input:
            usuario_db = Usuario.objects.filter(
                user=user_input,
                contraseña=contraseña_input,
                activo=True,
            ).first()

            if usuario_db:
                rol = 'admin' if usuario_db.rol == 'admin' else 'usuario'
                destino = 'lista'
                respuesta = redirect(destino)
                respuesta.set_cookie('usuario_id', str(usuario_db.pk), max_age=60 * 60 * 8)
                respuesta.set_cookie('user_login', usuario_db.user, max_age=60 * 60 * 8)
                respuesta.set_cookie('nombre_usuario', usuario_db.nombreCompleto or usuario_db.user, max_age=60 * 60 * 8)
                respuesta.set_cookie('rol_usuario', rol, max_age=60 * 60 * 8)
                return respuesta
            else:
                error = 'Usuario o contraseña incorrectos.'
        else:
            error = 'Ingresa tu usuario y contraseña para continuar.'

    return render(request, 'catalogo/login.html', {
        'error': error,
        'usuario': usuario_actual(request),
    })


def logout_view(request):
    respuesta = redirect('lista')
    respuesta.delete_cookie('usuario_id')
    respuesta.delete_cookie('user_login')
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
    disponibles = productos_visibles.filter(activo=True, stock__gt=0).count()
    stock_bajo = productos_visibles.filter(activo=True, stock__gt=0, stock__lte=5).count()
    sin_stock = productos_visibles.filter(stock=0).count()
    retirados = productos_visibles.filter(activo=False).count()

    categorias = list(
        productos_visibles.values_list('categoria', flat=True).distinct()
    )

    destacados = list(
        productos_visibles.filter(activo=True, stock__gt=0).order_by('-precio')[:4]
    )

    resumen = {
        'total': total_productos,
        'disponibles': disponibles,
        'stock_bajo': stock_bajo,
        'sin_stock': sin_stock,
        'retirados': retirados,
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


def editar_producto(request, producto_id):
    usuario = usuario_actual(request)
    if usuario is None or usuario['rol'] != 'admin':
        return redirect('login')

    producto = get_object_or_404(Producto, pk=producto_id)
    error = None

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        categoria = request.POST.get('categoria', '').strip()
        imagen = request.POST.get('imagen', '').strip() or '/static/catalogo/img/sin-imagen.jpg'
        activo = request.POST.get('activo') in ('on', 'true', '1', True)

        try:
            precio = int(request.POST.get('precio', -1))
            stock = int(request.POST.get('stock', -1))
        except ValueError:
            precio = -1
            stock = -1

        if nombre and categoria and precio >= 0 and stock >= 0:
            producto.nombre = nombre
            producto.categoria = categoria
            producto.precio = precio
            producto.stock = stock
            producto.imagen = imagen
            producto.activo = activo
            producto.save()
            return redirect('lista')
        error = 'Verifica que todos los campos obligatorios tengan valores válidos.'

    categorias = list(
        Producto.objects.values_list('categoria', flat=True).distinct()
    )
    items_carrito = obtener_carrito()
    datos_carrito = resumen_carrito(items_carrito)

    contexto = {
        'producto': producto,
        'categorias': categorias,
        'error': error,
        'carrito': items_carrito,
        'carrito_total': datos_carrito['precio_total'],
        'carrito_cantidad': datos_carrito['cantidad_total'],
        'usuario': usuario,
    }
    return render(request, 'catalogo/editar.html', contexto)


def resumen_admin(request):
    usuario = usuario_actual(request)
    if usuario is None or usuario.get('rol') != 'admin':
        return redirect('login')

    metricas_generales = Producto.objects.aggregate(
        cantidad_articulos=Count('id'),
        stock_total=Sum('stock'),
        costo_promedio=Avg('precio'),
        valor_inventario=Sum(F('precio') * F('stock')),
    )

    por_categoria = list(
        Producto.objects.values('categoria')
        .annotate(
            cantidad_articulos=Count('id'),
            stock_categoria=Sum('stock'),
            costo_promedio=Avg('precio'),
            valor_categoria=Sum(F('precio') * F('stock')),
        )
        .order_by('-stock_categoria')
    )

    items_carrito = obtener_carrito()
    datos_carrito = resumen_carrito(items_carrito)

    contexto = {
        'metricas': {
            'cantidad_articulos': metricas_generales['cantidad_articulos'] or 0,
            'stock_total': metricas_generales['stock_total'] or 0,
            'costo_promedio': round(metricas_generales['costo_promedio'] or 0),
            'valor_inventario': metricas_generales['valor_inventario'] or 0,
        },
        'por_categoria': por_categoria,
        'carrito': items_carrito,
        'carrito_total': datos_carrito['precio_total'],
        'carrito_cantidad': datos_carrito['cantidad_total'],
        'usuario': usuario,
    }
    return render(request, 'catalogo/resumen.html', contexto)


def _datos_peticion(request):
    """Extrae datos desde JSON (Postman) o desde request.POST (formularios HTML)."""
    if request.content_type and 'application/json' in request.content_type:
        try:
            return json.loads(request.body.decode('utf-8') or '{}')
        except (ValueError, UnicodeDecodeError):
            return {}
    return request.POST


def _es_peticion_api(request):
    """Detecta si la petición proviene de Postman o solicita respuesta JSON."""
    if request.content_type and 'application/json' in request.content_type:
        return True
    accept = request.headers.get('Accept', '')
    user_agent = request.headers.get('User-Agent', '')
    return 'application/json' in accept or 'Postman' in user_agent


@csrf_exempt
def registro_view(request):
    error = None

    if request.method == 'POST':
        datos = _datos_peticion(request)
        nombre_completo = (datos.get('nombreCompleto') or datos.get('nombre') or '').strip()
        user_input = (datos.get('user') or datos.get('usuario') or '').strip()
        contraseña_input = (datos.get('contraseña') or datos.get('password') or '').strip()
        email_input = (datos.get('email') or '').strip()

        if nombre_completo and user_input and contraseña_input and email_input:
            if Usuario.objects.filter(user=user_input).exists():
                error = 'El nombre de usuario ya está registrado.'
                if _es_peticion_api(request):
                    return JsonResponse({'error': error}, status=400)
            else:
                nuevo_usuario = Usuario.objects.create(
                    nombreCompleto=nombre_completo,
                    user=user_input,
                    contraseña=contraseña_input,
                    email=email_input,
                    activo=True,
                    rol='usuario',
                )
                if _es_peticion_api(request):
                    return JsonResponse({
                        'id': nuevo_usuario.id,
                        'nombreCompleto': nuevo_usuario.nombreCompleto,
                        'user': nuevo_usuario.user,
                        'email': nuevo_usuario.email,
                        'activo': nuevo_usuario.activo,
                        'rol': nuevo_usuario.rol,
                    }, status=201)

                respuesta = redirect('lista')
                respuesta.set_cookie('usuario_id', str(nuevo_usuario.pk), max_age=60 * 60 * 8)
                respuesta.set_cookie('user_login', nuevo_usuario.user, max_age=60 * 60 * 8)
                respuesta.set_cookie('nombre_usuario', nuevo_usuario.nombreCompleto or nuevo_usuario.user, max_age=60 * 60 * 8)
                respuesta.set_cookie('rol_usuario', 'usuario', max_age=60 * 60 * 8)
                return respuesta
        else:
            error = 'Completa todos los campos para registrarte.'
            if _es_peticion_api(request):
                return JsonResponse({'error': error}, status=400)

    return render(request, 'catalogo/registro.html', {
        'error': error,
        'usuario': usuario_actual(request),
    })


@csrf_exempt
def lista_usuarios(request):
    if request.method == 'POST':
        return agregar_usuario(request)

    usuarios = list(
        Usuario.objects.values('id', 'nombreCompleto', 'user', 'email', 'activo', 'rol')
    )
    return JsonResponse({'usuarios': usuarios})


@csrf_exempt
def detalle_usuario(request, usuario_id):
    usuario_obj = get_object_or_404(Usuario, pk=usuario_id)
    return JsonResponse({
        'id': usuario_obj.id,
        'nombreCompleto': usuario_obj.nombreCompleto,
        'user': usuario_obj.user,
        'email': usuario_obj.email,
        'activo': usuario_obj.activo,
        'rol': usuario_obj.rol,
    })


@csrf_exempt
def agregar_usuario(request):
    if request.method == 'POST':
        datos = _datos_peticion(request)
        nombre_completo = (datos.get('nombreCompleto') or datos.get('nombre') or '').strip()
        user_input = (datos.get('user') or datos.get('usuario') or '').strip()
        contraseña_input = (datos.get('contraseña') or datos.get('password') or '').strip()
        email_input = (datos.get('email') or '').strip()
        rol_input = (datos.get('rol') or 'usuario').strip() or 'usuario'
        activo_val = datos.get('activo', True)
        activo = activo_val in ('on', 'true', '1', True, 1)

        if nombre_completo and user_input and contraseña_input and email_input:
            nuevo_usuario = Usuario.objects.create(
                nombreCompleto=nombre_completo,
                user=user_input,
                contraseña=contraseña_input,
                email=email_input,
                activo=activo,
                rol=rol_input,
            )
            if _es_peticion_api(request):
                return JsonResponse({
                    'id': nuevo_usuario.id,
                    'nombreCompleto': nuevo_usuario.nombreCompleto,
                    'user': nuevo_usuario.user,
                    'email': nuevo_usuario.email,
                    'activo': nuevo_usuario.activo,
                    'rol': nuevo_usuario.rol,
                }, status=201)
        elif _es_peticion_api(request):
            return JsonResponse({'error': 'Faltan campos obligatorios (nombreCompleto, user, contraseña, email).'}, status=400)

    return redirect(request.META.get('HTTP_REFERER', 'lista'))


@csrf_exempt
def editar_usuario(request, usuario_id):
    usuario_obj = get_object_or_404(Usuario, pk=usuario_id)

    if request.method in ('POST', 'PUT', 'PATCH'):
        datos = _datos_peticion(request)
        nombre_completo = (datos.get('nombreCompleto') or usuario_obj.nombreCompleto).strip()
        user_input = (datos.get('user') or usuario_obj.user).strip()
        contraseña_input = (datos.get('contraseña') or usuario_obj.contraseña).strip()
        email_input = (datos.get('email') or usuario_obj.email).strip()
        rol_input = (datos.get('rol') or usuario_obj.rol).strip()

        if 'activo' in datos:
            activo_val = datos.get('activo')
            usuario_obj.activo = activo_val in ('on', 'true', '1', True, 1)

        if nombre_completo and user_input and contraseña_input and email_input:
            usuario_obj.nombreCompleto = nombre_completo
            usuario_obj.user = user_input
            usuario_obj.contraseña = contraseña_input
            usuario_obj.email = email_input
            usuario_obj.rol = rol_input
            usuario_obj.save()

            if _es_peticion_api(request):
                return JsonResponse({
                    'id': usuario_obj.id,
                    'nombreCompleto': usuario_obj.nombreCompleto,
                    'user': usuario_obj.user,
                    'email': usuario_obj.email,
                    'activo': usuario_obj.activo,
                    'rol': usuario_obj.rol,
                })

    return redirect(request.META.get('HTTP_REFERER', 'lista'))


@csrf_exempt
def retirar_usuario(request, usuario_id):
    usuario_obj = get_object_or_404(Usuario, pk=usuario_id)

    if request.method == 'POST':
        usuario_obj.activo = False
        usuario_obj.save(update_fields=['activo'])
        if _es_peticion_api(request):
            return JsonResponse({'id': usuario_obj.id, 'user': usuario_obj.user, 'activo': False})

    return redirect(request.META.get('HTTP_REFERER', 'lista'))


@csrf_exempt
def reactivar_usuario(request, usuario_id):
    usuario_obj = get_object_or_404(Usuario, pk=usuario_id)

    if request.method == 'POST':
        usuario_obj.activo = True
        usuario_obj.save(update_fields=['activo'])
        if _es_peticion_api(request):
            return JsonResponse({'id': usuario_obj.id, 'user': usuario_obj.user, 'activo': True})

    return redirect(request.META.get('HTTP_REFERER', 'lista'))



