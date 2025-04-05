from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.utils.dateparse import parse_date
from django.db.models import Sum
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.template.loader import render_to_string

from django.db.utils import IntegrityError
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .utils import *
# Create your views here.

def index(request):
    cat_id = request.GET.get("cat")  
    carrito = request.session.get('carrito', {})
    total = 0
    carrito = request.session.get('carrito', {}).copy()  # Hacer una copia
    total_general = 0

    for item in carrito.values():
        item['total'] = float(item['cantidad']) * float(item['precio'])
        total_general += item['total']


    if cat_id:
        try:
            categoria = Categoria.objects.get(id=cat_id)  
            productos = Producto.objects.filter(fk2_producto_categoria__categoria=categoria)  
        except Categoria.DoesNotExist:
            categoria = None
            productos = []
    else:
        categoria = None
        productos = Producto.objects.all() 

    categorias = Categoria.objects.all() 
    car = Carrito.objects.all()  

    contexto = {
        "productoInfo": productos,
        "categorias": categorias,  
        "carrito": car,
        'carrito': carrito,
        'total': total,
        "carrito": carrito,
        "totalg": total_general
    }
    return render(request, 'index.html', contexto)


def login(request):
    # autenticación
    if request.method == "POST":
        usuario = request.POST.get("email")
        passwd = request.POST.get("password")
        try:
            q = User.objects.get(email=usuario, password=passwd)
             # if verify_password(passwd, q.password):
            # Crear variable de sesión ========
            # Crear variable de sesión ========
            request.session["auth"] = {
                "id": q.id,
                "foto": q.foto.url,
                "nombre": q.nombre,
                "apellido":q.apellido,
                "email": q.email,
                "celular": q.celular,
                "rol": q.rol,
            }
            verificar = request.session.get("auth", False)
            if verificar :
                if verificar["rol"] == 1:
                    return redirect("admin_dashboard")
                else:
                    return redirect("index")
            return redirect("index")
        except User.DoesNotExist:
            messages.warning(request, "Usuario o contraseña no válidos..")
            request.session["auth"] = None
        except Exception as e:
            messages.error(request, f"Error: {e}")
            request.session["auth"] = None
        return redirect("login")
    else:
        verificar = request.session.get("auth", False)

        if verificar:
            return redirect("index")
        else:
            return render(request, "login.html")

def logout(request):
    try:
        del request.session["auth"]

        if 'carrito' in request.session:
            del request.session['carrito']


        messages.success(request, "Has cerrado sesión correctamente")
    except Exception as e:
        messages.info(request, "No se pudo cerrar sesión, intente de nuevo")
    return redirect("index")
    

def cambiar_clave(request):
    if request.method == "POST":
        clave_actual = request.POST.get("clave_actual")
        nueva = request.POST.get("nueva")
        repite_nueva = request.POST.get("repite_nueva")
        logueado = request.session.get("auth", False)

        q = User.objects.get(pk=logueado["id"])
        if verify_password(clave_actual, q.password):
            if nueva == repite_nueva:
                q.password = hash_password(nueva)       # utils.py
                q.save()
                messages.success(request, "Contraseña cambiada con éxito!!")
            else:
                messages.info(request, "Contraseñas nuevas no coinciden...")
        else:
            messages.warning(request, "Contraseña no concuerda...")

        return redirect("cambiar_clave")
    else:
        return render(request, "usuarios/cambiar_clave.html")

    



def contactanos(request):
    return render(request, 'contactanos.html')

def facturas(request): 
    verificar = request.session.get("auth", False)

    if verificar:
        if verificar["rol"] == 1:
            fac = Carrito.objects.filter()
            contexto = {
                "facturas": fac
            }
            return render(request, "admin/admin-facturas.html", contexto) 
        else:
            messages.info(request, "Usted no tiene permisos para éste módulo...")
        return redirect( "index")
    
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")
    

def about(request):
    return render(request, 'about.html')


# def register(request):
#     return render(request, 'register.html')

def clave (request):
    return render(request, 'recuperarclave.html')

def dashboardAdmin(request):
     
    verificar = request.session.get("auth", False)

    if verificar:
        if verificar["rol"] == 1:
            cat_id = request.GET.get("cat")     
            if cat_id:
                try:
                    categoria = Categoria.objects.get(id=cat_id)  
                    productos = Producto.objects.filter(fk2_producto_categoria__categoria=categoria)  
                except Categoria.DoesNotExist:
                    categoria = None
                    productos = []
            else:
                categoria = None
                productos = Producto.objects.all() 

            categorias = Categoria.objects.all() 
            car = Carrito.objects.all()  
            contexto = {
                "productoInfo": productos,
                "categorias": categorias,  
                "carrito": car
            } 
            return render(request, "admin/admin-DashBoard.html", contexto)
        else:
            messages.info(request, "Usted no tiene permisos para éste módulo...")
        return redirect( "index")
    
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")

    



def crud_categorias(request): 
    verificar = request.session.get("auth", False)

    if verificar:
        if verificar["rol"] == 1:
            cate = Categoria.objects.all()
            contexto = {
                "categorias": cate
            }
            return render  (request, "admin/adminCRUDCategorias.html", contexto)
        else:
            messages.info(request, "Usted no tiene permisos para éste módulo...")
        return redirect( "index")
    
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")

      

def eliminar_categoria(request, id_categoria):
    try:
        cate = Categoria.objects.get(pk = id_categoria)
        cate.delete()
        messages.success(request, "Cita eliminada correctamente!")
    except IntegrityError:
        messages.warning(request, "Error: No puede eliminar el cita, está en uso.")
    except Exception as e:
        messages.error(request, f"Error: {e}")

    return redirect("crud_categoria")


def crud_productos(request):
    verificar = request.session.get("auth", False)

    if verificar:
        if verificar["rol"] == 1:
            p = Producto.objects.all()
            c = Categoria.objects.all()
            contexto = {
                "productos": p,
                "catProduct": c
            }
            return render (request,"admin/admin-CRUD-productos.html", contexto) 
        else:
            messages.info(request, "Usted no tiene permisos para éste módulo...")
        return redirect( "index")
    
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")
    



#CRUD USUARIOS 

#CREAR USUARIO 
def crear_usuario(request):
    if request.method == 'POST':
        nombre = request.POST.get("nombre")
        apellido = request.POST.get("apellido")
        celular = request.POST.get("celular")
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirmar_password = request.POST.get('confirmar_password')
        direccion = request.POST.get('direccion')  # Asegúrate de que este campo esté en tu formulario

        if password == confirmar_password:
            try:
                # Crear el usuario usando tu modelo personalizado
                q = User(
                    nombre=nombre,
                    apellido=apellido,
                    celular=celular,
                    email=email,
                    password=password,  # Recuerda que deberías encriptar la contraseña
                    direccion=direccion,
                    rol=2  # Asignar un rol por defecto, si es necesario
                )
                q.save()  # Guardar el usuario en la base de datos
                messages.success(request, "Usuario creado correctamente!")
                return redirect("login")  # Cambia 'index' por la vista a la que quieras redirigir
            except Exception as e:
                messages.error(request, f"Error: {e}")
                return redirect("register")
        else:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect("register")
    else:
        return render(request, "register.html")
    

def editar_perfil(request):
    if request.method == 'POST':
    
        user_id = request.session.get("auth", {}).get("id")
        if not user_id:
            messages.error(request, "Debes iniciar sesión para editar tu perfil.")
            return redirect("login")

        try:
            q = User.objects.get(pk=user_id)

            nombre = request.POST.get("nombre").strip()
            apellido = request.POST.get("apellido").strip()
            celular = request.POST.get("celular").strip()
            email = request.POST.get("email").strip()

            q.nombre = nombre
            q.apellido = apellido
            q.celular = celular
            q.email = email
            q.save()

            request.session["auth"] = {
                "id": q.id,
                "nombre": nombre,
                "apellido": apellido,
                "celular": celular,
                "email": email,
                "foto": q.foto.url,
            }
            messages.success(request, "Datos actualizados correctamente")
            return redirect("editar-perfil")
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect("editar-perfil")
    else:
        # Verificamos si el usuario está logueado antes de proceder
        user_id = request.session.get("auth", {}).get("id")
        if not user_id:
            messages.error(request, "Debes iniciar sesión para editar tu perfil.")
            return redirect("login")
        
        return render(request, "usuarios/user-Crud.html")


def correos1 (request): 
    try:  
        send_mail (
            
            "PanaderiasMaye",
            "mensajes de prueba........ desde django",
            settings.EMAIL_HOST_USER,
            ["gonzacardona09@gmail.com"],
            fail_silently = False,
        )

        return HttpResponse(f"correo enviado")
    except Exception as e: 
        return HttpResponse(f"Error {e}")
    












def correos2 (request): 
    try:  
        html_message="""hola mundo<strong style='color:blue;'>Django</strong> desde mi app
        <br>
        bienvenido 
        """
        send_mail (
            
            "PanaderiasMaye",
            "",
            settings.EMAIL_HOST_USER,
            ["gonzacardona09@gmail.com"],
            fail_silently = False,
            html_message=html_message,
        )

        return HttpResponse(f"correo enviado")
    except Exception as e: 
        return HttpResponse(f"Error {e}")

def agregar_categoria(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")

        try:
            nueva_categoria = Categoria(nombre=nombre, descripcion=descripcion)
            nueva_categoria.save()
            messages.success(request, "Categoría añadida correctamente!")
            return redirect("crud_categoria")
        except Exception as e:
            messages.error(request, f"Error al añadir categoría: {e}")

      # Redirige a la página de listado de categorías

    return redirect("crud_categorias")

def CrudUsuarios(request):
    verificar = request.session.get("auth", False)

    if verificar:
        if verificar["rol"] == 1:
            if request.method == 'POST':
                # Recoger los datos del formulario
                nombre = request.POST.get("nombre")
                apellido = request.POST.get("apellido")
                rol = request.POST.get("rol")
                celular = request.POST.get("celular")
                email = request.POST.get('email')
                password = request.POST.get('password')
                confirmar_password = request.POST.get('confirmar_password')

                # Validar si las contraseñas coinciden
                if password == confirmar_password:
                    try:
                        # Encriptar la contraseña antes de guardarla
                        from django.contrib.auth.hashers import make_password
                        password = make_password(password)

                        # Crear el nuevo usuario
                        nuevo_usuario = User(
                            nombre=nombre,
                            apellido=apellido,
                            celular=celular,
                            email=email,
                            password=password,  # Contraseña encriptada
                            rol=rol  # Asignar un rol
                        )
                        nuevo_usuario.save()  # Guardar en la base de datos
                        messages.success(request, "Usuario creado correctamente!")
                        return redirect("adminCRUDU")  # Cambia por la vista a la que quieras redirigir
                    except Exception as e:
                        messages.error(request, f"Error: {e}")
                        return redirect("admin_dashboard")  # Redirigir si hay error
                else:
                    messages.error(request, "Las contraseñas no coinciden.")
                    return redirect("admin_dashboard")  # Redirigir si las contraseñas no coinciden
            else:
                # Si es un GET, obtener todos los usuarios
                usuarios = User.objects.all()
                contexto = {
                    "usuarios": usuarios
                }
                return render(request, "admin/adminCRUDU.html", contexto)
        else:
            messages.info(request, "Usted no tiene permisos para éste módulo...")
        return redirect( "index")
    
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")
    


def editar_usuario(request, usuario_id):
    try:
        usuario = User.objects.get(id=usuario_id)
        if request.method == 'POST':
            # Obtener los datos del formulario
            usuario.nombre = request.POST.get("nombre")
            usuario.apellido = request.POST.get("apellido")
            usuario.celular = request.POST.get("celular")
            usuario.email = request.POST.get('email')
            password = request.POST.get('password')
            
            
            # Si la contraseña se cambia, encriptarla
            if password:
                from django.contrib.auth.hashers import make_password
                usuario.password = make_password(password)
            
            # Guardar los cambios
            usuario.save()
            messages.success(request, "Usuario actualizado correctamente.")
            return redirect("adminCRUDU")
        else:
            contexto = {
                "usuario": usuario
            }
            return render(request, "admin/editar_usuario.html", contexto)
    except User.DoesNotExist:
        messages.error(request, "Usuario no encontrado.")
        return redirect("adminCRUDU")

def eliminar_usuario(request, id_usuario):
    try:
        usuario = User.objects.get(pk=id_usuario)
        usuario.delete()
        messages.success(request, "Usuario eliminado correctamente.")
    except IntegrityError:
        messages.warning(request, "Error: No puede eliminar el usuario, está en uso.")
    except Exception as e:
        messages.error(request, f"Error: {e}")

    return redirect("adminCRUDU")

def eliminar_producto(request, id_producto):
    try:
        p = Producto.objects.get(pk = id_producto)
        p.delete()
        messages.success(request, "Producto eliminado correctamente.")
    except IntegrityError:
        messages.warning(request, "Error: No puede eliminar el producto")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect("crud_productos")


def editar_producto(request, producto_id):
    try:
        p = Producto.objects.get(pk = producto_id)
        if request.method == 'POST':
            # Obtener los datos del formulario
            p.nombre = request.POST.get("nombre", p.nombre)
            p.precio = request.POST.get("precio", p.precio)
            p.stock = request.POST.get("stock")
            p.disponibilidad = request.POST.get("disponibilidad", p.disponibilidad)
            p.foto = request.FILES.get("foto", p.foto)
            
            # Guardar los cambios
            p.save()
            messages.success(request, "Producto actualizado correctamente.")
            return redirect("crud_productos")
        else:
            contexto = {
                "producto": p
            }
            return render(request, "admin/editar_producto.html", contexto)
    except Producto.DoesNotExist:
        messages.error(request, "Producto no encontrado.")
        return redirect("crud_productos")
    


def agregar_producto(request):
    if request.method == 'POST':
        print(request.POST)
        print(request.FILES)

        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        precio = request.POST.get("precio")
        disponibilidad = request.POST.get("disponibilidad")
        foto = request.FILES.get("foto")  # Se obtiene la imagen del formulario
        categoria_ids = request.POST.getlist("categorias")  # Se obtiene una lista de los IDs de categorías seleccionadas

        if not nombre or not descripcion or not precio or not disponibilidad or not foto or not categoria_ids:
            messages.error(request, "Todos los campos son obligatorios")
            return redirect("crud_productos")

        try:
            # Crear el producto usando el modelo Producto
            producto = Producto(
                nombre=nombre,
                descripcion=descripcion,
                precio=precio,
                disponibilidad=disponibilidad,
                foto=foto if foto else "productos/pan9.jpeg"  # Se asigna la imagen si se sube
            )
            producto.save()  # Guardar el producto en la base de datos
            for categoria_id in categoria_ids:
                categoria = Categoria.objects.get(id=categoria_id)
                ProductoCategoria.objects.create(producto=producto, categoria=categoria)

            messages.success(request, "¡Producto creado correctamente!")
            return redirect("crud_productos")  
        except Exception as e:
            messages.error(request, f"Error al crear el producto: {e}")
            return redirect("crud_productos")
    else:
        return render(request, "admin-CRUD-productos.html")
    
def editar_categoria(request, categoria_id):
    try:
        cate = Categoria.objects.get(pk = categoria_id)
        if request.method == 'POST':
            # Obtener los datos del formulario
            cate.nombre = request.POST.get("nombre")
            cate.descripcion = request.POST.get("descripcion")
            
            # Guardar los cambios
            cate.save()
            messages.success(request, "Categoría actualizada correctamente.")
            return redirect("crud_categoria")
        else:
            contexto = {
                "categoria": cate
            }
            return render(request, "admin/editar_categoria.html", contexto)
    except Categoria.DoesNotExist:
        messages.error(request, "Categoría no encontrada.")
        return redirect("crud_categoria")
    
def eliminar_categoria(request, id_categoria):
    try:
        c = Categoria.objects.get(pk = id_categoria)
        c.delete()
        messages.success(request, "Categoria eliminada correctamente.")
    except IntegrityError:
        messages.warning(request, "Error: No puede eliminar la categoria")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect("crud_categoria")


#Carrito:

def agregar_carrito(request, producto_id):
    logueado = request.session.get("auth")

    if not logueado:
        messages.error(request, "Inicia sesión para añadir al carrito.")
        return redirect("login")
    
    producto = get_object_or_404(Producto, id=producto_id)
    carrito = request.session.get('carrito', {})

    if str(producto.id) in carrito:
        carrito[str(producto.id)]['cantidad'] += 1
    else:
        carrito[str(producto.id)] = {
            'id': producto.id,
            'foto': producto.foto.url,
            'nombre': producto.nombre,
            'precio': float(producto.precio),  # Asegurar que sea float
            'cantidad': 1,
            'total': 0
        }
    
    # **Actualizar el total por producto**
    carrito[str(producto.id)]['total'] = carrito[str(producto.id)]['cantidad'] * carrito[str(producto.id)]['precio']

    request.session['carrito'] = carrito
    messages.success(request, f"{producto.nombre} agregado correctamente al carrito.")
    return redirect('ver_carrito')


def ver_carrito(request):
    logueado = request.session.get("auth")

    if not logueado:
        messages.error(request, "Inicia sesión para ver el carrito.")
        return redirect("login")

    carrito = request.session.get('carrito', {}).copy()  # Hacer una copia
    total_general = 0

    for key, item in carrito.items():
        item['total'] = float(item['precio']) * item['cantidad']  # Asegurar conversión a float
        total_general += item['total']

    request.session['carrito'] = carrito  # Guardar cambios en la sesión

    print(f"Total General Calculado: {total_general}")  # <-- Agrega esta línea para depuración

    contexto = {
        "carrito": carrito,
        "total": total_general
    }
    return render(request, 'index.html', contexto)



def eliminar_producto_carrito(request, producto_id):
    logueado = request.session.get("auth")

    if not logueado:
        messages.error(request, "Inicia sesión para eliminar productos del carrito.")
        return redirect("login")

    carrito = request.session.get('carrito', {})

    # Verifica si el producto está en el carrito
    if str(producto_id) in carrito:
        del carrito[str(producto_id)]  # Elimina el producto del carrito
        messages.success(request, "Producto eliminado del carrito.")
    else:
        messages.error(request, "El producto no está en el carrito.")

    request.session['carrito'] = carrito  # Guarda los cambios en la sesión
    return redirect('ver_carrito_completo')  # Redirige a la vist



def ver_carrito_completo(request):
    logueado = request.session.get("auth")

    if not logueado:
        messages.error(request, "Inicia sesión para ver el carrito.")
        return redirect("login")

    carrito = request.session.get('carrito', {}).copy()  # Hacer una copia
    total_general = 0

    for item in carrito.values():
        item['total'] = float(item['cantidad']) * float(item['precio'])
        total_general += item['total']

    request.session['carrito'] = carrito  # Guardar cambios en la sesión

    print(f"Total General Calculado: {total_general}")  # <-- Agrega esta línea para depuración

    contexto = {
        "carrito": carrito,
        "total": total_general
    }
    return render(request, 'carrito.html', contexto)

def actualizar_cantidad(request, producto_id):
    if request.method == "POST":
        nueva_cantidad = int(request.POST.get("cantidad", 1))
        carrito = request.session.get("carrito", {})

        if str(producto_id) in carrito:
            carrito[str(producto_id)]['cantidad'] = nueva_cantidad
            carrito[str(producto_id)]['total'] = nueva_cantidad * float(carrito[str(producto_id)]['precio'])

        request.session["carrito"] = carrito
        return redirect("ver_carrito_completo")

#Facturas y PAGOS 

def formulario_pago(request):
    logueado = request.session.get("auth")
    carrito_sesion = request.session.get('carrito', {}).copy()
    total_general = 0

    for item in carrito_sesion.values():
        item['total'] = float(item['cantidad']) * float(item['precio'])
        total_general += item['total']

    if request.method == "POST":
        carrito_id = request.session.get('carrito_id')
        if not carrito_id:
            messages.error(request, "No se encontró la factura para pagar.")
            return redirect('ver_carrito')

        try:
            metodo = request.POST.get('metodo_pago')
            factura = Carrito.objects.get(id=carrito_id)
            factura.estado = 2
            factura.meotdo_pago = metodo
            factura.save()
        except Carrito.DoesNotExist:
            messages.error(request, "La factura no existe.")
            return redirect('ver_carrito')
        
        print("metodo pago", factura.meotdo_pago)

        # Limpiar sesión
        request.session['carrito'] = {}
        del request.session['carrito_id']

        messages.success(request, "¡Pago exitoso!")
        return redirect('ver_carrito')
    
    contexto = {
        "carrito": carrito_sesion,
        "total_general": total_general,
        "carrito_id": request.session.get('carrito_id')
    }

    return render(request, 'pago.html', contexto)


def procesar_pedido(request):
    logueado = request.session.get("auth")

    if not logueado:
        messages.error(request, "Debes loguearte primero para continuar... ")
        return redirect("login")
    
    carrito_sesion = request.session.get('carrito', {})
    if not carrito_sesion:
        messages.error(request, "Tu carrito está vacío.")
        return redirect('ver_carrito')
    
    total_general = sum(item['cantidad'] * item['precio'] for item in carrito_sesion.values())

    nuevo_carrito = Carrito.objects.create(
        usuario_id=logueado["id"],
        fecha=timezone.now(),
        cantidad=sum(item['cantidad'] for item in carrito_sesion.values()),  # Total de productos
        estado=1
    )

    for producto_id, item in carrito_sesion.items():
        detalle = Detalle_carrito.objects.create(
            carrito=nuevo_carrito,
            producto_id=int(producto_id),
            cantidad=item['cantidad'],
            total=item['cantidad'] * item['precio']
        )

    request.session['carrito_id'] = nuevo_carrito.id

    messages.success(request, "Tu pedido ha sido procesado correctamente.")
    return redirect('formulario_pago')

#FACTURAS

def facturas_usuario(request):
    logueado = request.session.get("auth")
    
    if not logueado:
        messages.error(request, "Debes iniciar sesión para ver tus facturas.")
        return redirect("login")

    usuario_id = logueado["id"]
    fecha_filtro = request.GET.get("fecha", "")

    facturas = Carrito.objects.filter(usuario_id=usuario_id, estado=2).order_by("-fecha")

    if fecha_filtro:
        try:
            fecha_filtrada = parse_date(fecha_filtro)
            facturas = facturas.filter(fecha__date=fecha_filtrada)
        except:
            messages.warning(request, "Fecha inválida.")

    # Crea una lista de facturas con sus totales
    facturas_con_totales = []
    for factura in facturas:
        total = factura.detalles.aggregate(total=Sum('total'))["total"] or 0
        facturas_con_totales.append({
            "factura": factura,
            "total": total
        })

    contexto = {
        "facturas_con_totales": facturas_con_totales,
        "fecha_filtro": fecha_filtro
    }

    return render(request, "facturas.html", contexto)

def exportar_factura_pdf(request, factura_id):
    # Asegúrate que el campo se llama 'usuario', cámbialo si es necesario
    carrito = Carrito.objects.get(id=factura_id)
    detalles = Detalle_carrito.objects.filter(carrito=carrito)
    total = detalles.aggregate(total=Sum('total'))['total'] or 0

    template_path = 'factura_pdf.html'
    context = {
        'factura': carrito,
        'detalles': detalles,
        'total': total,
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura_{carrito.id}.pdf"'

    template = get_template(template_path)
    html = template.render(context)
    pisa.CreatePDF(html, dest=response)

    return response

def enviar_correo_confirmacion(carrito):
    asunto = f"Confirmación de pago - Pedido #{carrito.id}"
    destinatario = carrito.usuario.email

    mensaje_html = render_to_string('correo_confirmacion.html', {
        'carrito': carrito,
        'detalles': carrito.detalles.all(),
        'total': sum(detalle.total for detalle in carrito.detalles.all()),
    })

    send_mail(
        asunto,
        '',  # mensaje en texto plano (opcional)
        settings.EMAIL_HOST_USER,
        [destinatario],
        html_message=mensaje_html
    )


def confirmar_pago(request, carrito_id):
    # Obtener el carrito solo si pertenece al usuario autenticado
    logueado = request.session.get("auth")
    carrito = get_object_or_404(Carrito, id=carrito_id, usuario=logueado["id"])

    # Cambiar estado a "Pagado" (2)
    carrito.estado = 2
    carrito.save()

    # Enviar el correo después de guardar los cambios
    enviar_correo_confirmacion(carrito)

    # Redirigir a una vista de éxito o mensaje
    messages.success(request, "Factura enviada a tu correo, graicas por tu compra... ")
    request.session['carrito'] = {}
    del request.session['carrito_id']
    return redirect('index')  