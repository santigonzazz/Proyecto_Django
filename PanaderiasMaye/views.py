from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.utils.dateparse import parse_date
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware
from django.db.models import Sum
import re
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from xhtml2pdf import pisa
from django.template.loader import get_template
from django.template.loader import render_to_string

from django.db.utils import IntegrityError
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .utils import *
from django.contrib.auth.hashers import make_password
import uuid
from django.contrib.auth.decorators import login_required
# Create your views here.

#principales-------------------------------------------------------------------------------------------------------------
def index(request):
    cat_id = request.GET.get("cat")   
    total = 0
    total_general = 0
    carrito_actual = None
    detalles = []


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
    
  
    user = request.session.get("auth", {}).get("id")
    if user:
        try:
            user_obj = User.objects.get(id=user)
            carrito_actual = Carrito.objects.filter(usuario=user_obj, estado=1).latest('fecha')
            detalles = Detalle_carrito.objects.filter(carrito=carrito_actual)
            for item in detalles:
                item.total = item.cantidad * item.producto.precio
                total_general += item.cantidad * item.producto.precio
        except Carrito.DoesNotExist:
            carrito_actual = None
            detalles = []
            total_general = 0

    contexto = {
        "productoInfo": productos,
        "categorias": categorias,  
        "carrito": detalles,
        "detalles": detalles,
        'total': total,
        "totalg": total_general
    }
    return render(request, 'index.html', contexto)


def login(request):
    # autenticación
    if request.method == "POST":
        usuario = request.POST.get("email")
        passwd = request.POST.get("password")
        try:
            q = User.objects.get(email=usuario)
            if not verify_password(passwd, q.password):
                messages.error(request, "Contraseña o Correo invalidao.. ")
                return redirect("login")
            
            if not q.verificado:
                messages.error(request, "Debes verificar tu cuenta antes para acceder a la web... ")
                return redirect("login")
            
            if verify_password(passwd, q.password):
                request.session["auth"] = {
                    "id": q.id,
                    "foto": q.foto.url,
                    "nombre": q.nombre,
                    "apellido":q.apellido,
                    "email": q.email,
                    "celular": q.celular,
                    "rol": q.rol,
                    "verificado": q.verificado
                }
            verificar = request.session.get("auth", False)

            if verificar :
                if verificar["rol"] == 1:
                    return redirect("admin_dashboard")
                else:
                    return redirect("index")
            return redirect("index")
        except User.DoesNotExist:
            messages.warning(request, "Correo o contraseña no válidos..")
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
    
def about(request):
    return render(request, 'about.html')

def contactanos(request):
    
    tipo_opciones = Pqrs.TIPOS

    if request.method == 'POST':
        user_id = request.session.get("auth", {}).get("id")
        if not user_id:
            messages.error(request, "Debes iniciar sesión para editar tu perfil.")
            return redirect("login")
        
        errores = []

        nombre = request.POST.get("nombre", "").strip()
        email = request.POST.get("email", "").strip()
        mensaje = request.POST.get("mensaje", "").strip()
        tipo = request.POST.get("tipo")

        if not nombre or nombre == "":
            errores.append("El campo nombre no puede estar vacío ")
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ ]+", nombre):
                    errores.append("Nombre Invalido. Solo se permiten letras y espacios... ")
        if not email:
            errores.append("El parametro Correo debe tener un valor!! ")
        else:      
            try:
                validate_email(email)
                print(f"Correo  {email} ")
            except ValidationError:
                errores.append("Correo electrónico inválido.")
        if not mensaje or mensaje == "":
            errores.append("Debe tener un mensaje ")
        elif len(mensaje) < 20:
            errores.append("El mensaje debe tener minimo 20 caracteres!! ")
        
        if not tipo:
            errores.append("Debes seleccionar el tipo del mensaje!! ")
            

        if errores:
                for error in errores:
                    messages.error(request, error)
                return redirect("contactanos")
        
        q = Pqrs(
            nombre = nombre,
            correo = email,
            mensaje = mensaje,
            tipo=tipo
        )
        q.save()
        
        messages.success(request, "Gracias por compartir tu opinión con nosotros. Mensaje enviado con éxito!! ")
        return redirect("contactanos")
    else:
        return render(request, 'contactanos.html', {"tipo_opciones": tipo_opciones})

# def validacion_contactanos(request):
#     if request.method == 'POST':

#         user_id = request.session.get("auth", {}).get("id")
#         if not user_id:
#             messages.error(request, "Debes iniciar sesión para editar tu perfil.")
#             return redirect("login")
        
#         errores = []

#         nombre = request.POST.get("nombre", "").strip()
#         email = request.POST.get("email", "").strip()
#         mensaje = request.POST.get("mensaje", "").strip()

#         if not nombre:
#             errores.append("El parametro Nombre debe tener un valor!! ")
#         else:
#             if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ ]+", nombre):
#                 errores.append("Nombre Invalido. Solo se permiten letras y espacios... ")


#facturas--------------------------------------------------------------------------------------

def facturas(request): 
    verificar = request.session.get("auth", False)

    if verificar:
        if verificar["rol"] == 1:
            facturas_raw = Carrito.objects.all().prefetch_related('detalles')  

            facturas = []
            for f in facturas_raw:
                total = sum(detalle.total for detalle in f.detalles.all())
                facturas.append({
                    "id": f.id,
                    "usuario": f.usuario,
                    "servicio": f.get_servicio_display(),  # muestra el nombre del servicio
                    "cantidad": f.cantidad,
                    "total": total
                })

            contexto = {
                "facturas": facturas
            }
            return render(request, "admin/admin-facturas.html", contexto) 
        else:
            messages.info(request, "Usted no tiene permisos para este módulo...")
            return redirect("index")
    
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")

#funciones de usuario-------------------------------------------------------------------------

def cambiar_clave(request):
    if request.method == "POST":
        clave_actual = request.POST.get("clave_actual")
        nueva = request.POST.get("nueva")
        repite_nueva = request.POST.get("repite_nueva")
        logueado = request.session.get("auth")

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
        return render(request, "cambiar_clave.html")

def clave (request):
    return render(request, 'recuperarclave.html')

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

            if q.email != email:
                messages.error(request, "No puedes cambiar el correo ")
                return redirect("editar-perfil")
            
            errores = []

            if not nombre:
                errores.append("El Parametro Nombre debe tener un valor ")
            else:
                if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ ]+", nombre):
                    errores.append("Nombre Invalido. Solo se permiten letras y espacios... ") 
            
            if not apellido:
                errores.append("El Parametro Apellido debe tener un valor ")
            else:
                if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ ]+", apellido):
                    errores.append("Apellido Invalido. Solo se permiten letras y espacios... ") 

            if not celular:
                errores.append("El parametro Celular debe tener un valor ")
            else:
                if len(celular) < 10 or len(celular) > 10:
                    errores.append("El celular solo es de 10 digitos... ")
                elif not re.fullmatch(r"\d{10}", celular):
                    errores.append("Número de Celular invalido. Solo numeros!! ")

            if errores:
                for error in errores:
                    messages.error(request, error)
                return redirect("editar-perfil")


            q.nombre = nombre
            q.apellido = apellido
            q.celular = celular
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

#funciones del administrador-----------------------------------------------------------------------------------

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

#categorias

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

#productos

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

def eliminar_producto(request, id_producto):
    try:
        producto = Producto.objects.get(id=id_producto)  
        ProductoCategoria.objects.filter(producto=producto).delete()
        producto.delete()
        messages.success(request, "Producto eliminado correctamente.")
    except IntegrityError:
        messages.warning(request, "Error: No puede eliminar el producto.")
    except Exception as e:
        messages.error(request, f"Error: {e}")
    return redirect("crud_productos")


def editar_producto(request, producto_id):
    try:
        p = Producto.objects.get(pk=producto_id)

        if request.method == 'POST':
            # Obtener los datos del formulario
            p.nombre = request.POST.get("nombre", p.nombre)
            p.precio = request.POST.get("precio", p.precio)
            p.stock = request.POST.get("stock")
            p.descripcion = request.POST.get("descripcion", p.descripcion)
            p.disponibilidad = request.POST.get("disponibilidad", p.disponibilidad)
            foto_nueva = request.FILES.get("foto")
            if foto_nueva:
                p.foto = foto_nueva

            p.save()

            # 🔁 Actualizar las categorías
            nuevas_categorias = request.POST.getlist("categorias")
            ProductoCategoria.objects.filter(producto=p).delete()  # Elimina las relaciones actuales
            for cat_id in nuevas_categorias:
                categoria = Categoria.objects.get(id=cat_id)
                ProductoCategoria.objects.create(producto=p, categoria=categoria)

            messages.success(request, "Producto actualizado correctamente.")
            return redirect("crud_productos")

        else:
            contexto = {
                "producto": p,
                "catProduct": Categoria.objects.all(),  # 👈 necesario si vas a renderizar categorías
                "categorias_producto": p.fk2_producto_categoria.all()
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
    
#usuarios

def crear_usuario(request):
    if request.method == 'POST':
        nombre = request.POST.get("nombre", "").strip()
        apellido = request.POST.get("apellido", "").strip()
        celular = request.POST.get("celular", "").strip()
        email = request.POST.get('email', "").strip()
        password = request.POST.get('password')
        confirmar_password = request.POST.get('confirmar_password')
        direccion = request.POST.get('direccion', "").strip()  

        errores = []
        
        if not nombre:
            errores.append("El parametro Nombre debe tener un valor!! ")
        else:
            if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ ]+", nombre):
                errores.append("Nombre Invalido. Solo se permiten letras y espacios... ")

        if not apellido:
            errores.append("El parametro Apellido debe tener un valor!!")
        else:
            if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ ]+", apellido):
                errores.append("Apellido Invalido. Solo se permiten letras y espacios... ")

        if not celular:
            errores.append("El parametro Celular debe tener un valor ")
        else:
            if len(celular) < 10 or len(celular) > 10:
                errores.append("El celular solo es de 10 digitos... ")
            elif not re.fullmatch(r"\d{10}", celular):
                errores.append("Número de Celular invalido. Solo numeros!! ")

        if not email:
            errores.append("El parametro Correo debe tener un valor!! ")
        else:
                
            try:
                validate_email(email)
                print(f"Correo  {email} ")

            except ValidationError:
                errores.append("Correo electrónico inválido.")

        if not password:
            errores.append("El parametro Contraseña debe tener un valor!! ")
        else:
            if len(password) < 6:
                errores.append("La contraseña debe tener al menos 6 caracteres.")

        if not confirmar_password:
            errores.append("El parametro Confirmar Contraseña debe tener un valor!! ")
        else:
            if password != confirmar_password:
                errores.append("Las contraseñas no coinciden.")


        if errores:
            for error in errores:
                messages.error(request, error)
            return redirect("register")


        if password == confirmar_password:
            try:
                token = str(uuid.uuid4()).split('-')[0]
                q = User(
                    nombre=nombre,
                    apellido=apellido,
                    celular=celular,
                    email=email,
                    password=hash_password(password),  
                    direccion=direccion,
                    rol=2,
                    token = token,
                    verificado = False  
                )
                q.save()  

                enviar_token(email, token)
                request.session['correo_verificacion'] = email
                messages.success(request, "Token enviado correctamente!")
                return redirect("verificar_codigo")  
            except Exception as e:
                messages.error(request, f"Error: {e}")
                return redirect("register")
        else:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect("register")
    else:
        return render(request, "register.html")

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
            #usuario.email = request.POST.get('email')
            password = request.POST.get('password')
            
        
            
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

def crear_usuario_admin(request):
    if request.method == 'POST':
        nombre = request.POST.get("nombre", "").strip()
        apellido = request.POST.get("apellido", "").strip()
        rol = request.POST.get("rol", "")
        celular = request.POST.get("celular", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirmar_password = request.POST.get("confirmar_password", "")

        errores = []

        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ ]{2,}$', nombre):
            errores.append("El nombre solo puede contener letras y debe tener al menos 2 caracteres.")


        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ ]{2,}$', apellido):
            errores.append("El apellido solo puede contener letras y debe tener al menos 2 caracteres.")


        if rol not in ["1", "2"]:
            errores.append("Debe seleccionar un rol válido entre 1 o 2.")


        if not re.match(r'^\d{10}$', celular):
            errores.append("El número de celular debe tener exactamente 10 dígitos.")


        try:
            validate_email(email)
        except ValidationError:
            errores.append("Correo electrónico inválido.")

        if User.objects.filter(email=email).exists():
            errores.append("El correo electrónico ya está registrado.")

        if len(password) < 8:
            errores.append("La contraseña debe tener al menos 8 caracteres.")
        if password != confirmar_password:
            errores.append("Las contraseñas no coinciden.")


        if errores:
            for error in errores:
                messages.error(request, error)
            return redirect("adminCRUDU")


        try:
            nuevo_usuario = User(
                nombre=nombre,
                apellido=apellido,
                rol=rol,
                celular=celular,
                email=email,
                password=make_password(password),
            )
            nuevo_usuario.save()
            messages.success(request, "Usuario creado correctamente.")
        except Exception as e:
            messages.error(request, f"Error al crear usuario: {e}")

        return redirect("adminCRUDU")
    else:
        return render(request, "admin/adminCRUDU.html")
    

def editar_usuario_admin(request, id_usuario):
    usuario = get_object_or_404(User, pk=id_usuario)

    if request.method == 'POST':
        nombre = request.POST.get("nombre", "").strip()
        apellido = request.POST.get("apellido", "").strip()
        celular = request.POST.get("celular", "").strip()
        rol = request.POST.get("rol", "").strip()

        errores = []

        # Validar nombre y apellido
        patron_letras = r'^[A-Za-zÁÉÍÓÚáéíóúñÑ ]{2,}$'
        if not re.match(patron_letras, nombre):
            errores.append("El nombre solo puede contener letras y debe tener al menos 2 caracteres.")
        if not re.match(patron_letras, apellido):
            errores.append("El apellido solo puede contener letras y debe tener al menos 2 caracteres.")

        # Validar celular
        if not re.match(r'^\d{10}$', celular):
            errores.append("El número de celular debe tener exactamente 10 dígitos.")

        # Validar rol
        if rol not in ["1", "2"]:
            errores.append("Debe seleccionar un rol válido.")

        if errores:
            for error in errores:
                messages.error(request, error)
            return redirect("adminCRUDU")  # o a donde renderices la lista

        # Si pasa validación, guardar cambios
        usuario.nombre = nombre
        usuario.apellido = apellido
        usuario.celular = celular
        usuario.rol = rol
        usuario.save()

        messages.success(request, "Usuario actualizado correctamente.")
        return redirect("adminCRUDU")

    # Si viene por GET
    return redirect("adminCRUDU")

def eliminar_usuario_admin(request, id_usuario):
    try:
        usuario = get_object_or_404(User, pk=id_usuario)

        if str(usuario.rol) == "1":
            messages.warning(request, "No puedes eliminar un administrador.")
            return redirect("adminCRUDU")

        usuario.delete()
        messages.success(request, "Usuario eliminado correctamente.")
    except IntegrityError:
        messages.warning(request, "Error: No puedes eliminar este usuario porque está en uso en otra parte del sistema.")
    except Exception as e:
        messages.error(request, f"Error inesperado: {e}")

    return redirect("adminCRUDU")

#funciones del sistema------------------------------------------------------------------------------

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

#Carrito---------------------------------------------------------------------------------------------------------------
 
def agregar_carrito(request, producto_id):
    logueado = request.session.get("auth")

    if not logueado:
        messages.error(request, "Inicia sesión para añadir productos al carrito.")
        return redirect("login")

    producto = get_object_or_404(Producto, id=producto_id)
    # carrito = request.session.get("carrito", {})
    producto_id_str = str(producto.id)
    usuario = get_object_or_404(User, id=logueado["id"])
    if producto.disponibilidad == "NO":
        messages.error(request, f"El producto: {producto.nombre} no esta disponible")
        return redirect("index")
    try:
        carrito = Carrito.objects.filter(usuario=usuario, estado=1).latest()
        metodo_pago = Metodo_pago.objects.get(id=3)
    except Carrito.DoesNotExist:
        carrito = Carrito.objects.create(
            usuario=usuario,
            cantidad = 0,
            estado=1,
            servicio = 1,
            metodo_pago = None
        )
    
    detalle, creado = Detalle_carrito.objects.get_or_create(
        carrito = carrito,
        producto = producto,
        defaults={'cantidad': 1, 'total': producto.precio}
    )

    if not creado:
        if detalle.cantidad < producto.cantidad:
            detalle.cantidad += 1
            detalle.total = detalle.cantidad * producto.precio
            detalle.save()
        else:
            messages.error(request, f"No hay mas unidades disponibles de {producto.nombre}")
            return redirect("ver_carrito_completo")
        
    carrito.cantidad = sum(dc.cantidad for dc in carrito.detalles.all())
    carrito.save()

    messages.success(request, f"{producto.nombre} agregado correctamente al carrito ")
    return redirect("index")
    
    # if producto_id_str in carrito:
    #     if carrito[producto_id_str]["cantidad"] < producto.cantidad:
    #         carrito[producto_id_str]["cantidad"] += 1
    #     else:
    #         messages.warning(request, f"No hay más unidades disponibles de {producto.nombre}.")
    #         return redirect("ver_carrito_completo")
    # else:
    #     carrito[producto_id_str] = {
    #         "id": producto.id,
    #         "foto": producto.foto.url,
    #         "nombre": producto.nombre,
    #         "precio": float(producto.precio),
    #         "cantidad": 1,
    #         "stock": producto.cantidad, # stock de "cantidad"
    #         "total": 0
    #     }

    # carrito[producto_id_str]["total"] = round(
    #     carrito[producto_id_str]["cantidad"] * carrito[producto_id_str]["precio"], 2
    # )

    # request.session["carrito"] = carrito
    # messages.success(request, f"{producto.nombre} agregado correctamente al carrito.")
    # return redirect("index")


def ver_carrito_completo(request):

    logueado = request.session.get("auth")
    if not logueado:
        messages.error(request, "Inicia sesión para ver el carrito.")
        return redirect("login")

    usuario = get_object_or_404(User, id=logueado["id"])
    try:
        carrito = Carrito.objects.filter(usuario=usuario, estado=1).latest()
        detalles = carrito.detalles.all()
        total_general = sum( dc.total for dc in detalles if dc.producto.disponibilidad == "SI")

        
    except Carrito.DoesNotExist:
        carrito = None
        detalles = []
        total_general = 0

    contexto = {
        #"carrito": carrito,
        "detalles": detalles,
        "total": round(total_general, 2)
    }
    return render(request, "carrito.html", contexto)

    # for key, item in carrito.items():
    #     try:
    #         cantidad = int(item.get("cantidad", 1))
    #         precio = float(item.get("precio", 0))
    #         total = round(cantidad * precio, 2)

    #         item["cantidad"] = cantidad
    #         item["precio"] = precio
    #         item["total"] = total

    #         total_general += total
    #     except (ValueError, TypeError):
    #         messages.warning(request, f"Error en el producto del carrito: {item.get('nombre', 'desconocido')}")
    #         continue


    # request.session["carrito"] = carrito

    # contexto = {
    #     "carrito": carrito,
    #     "total": round(total_general, 2)
    # }
    
    # return render(request, "carrito.html", contexto)

def actualizar_cantidad(request, producto_id):
    if request.method == "POST":
        logueado = request.session.get("auth")
        if not logueado:
            return redirect("login")
        
        usuario = get_object_or_404(User, id=logueado["id"])
        nueva_cantidad = int(request.POST.get("cantidad"))

        if not nueva_cantidad:
            messages.error(request, "No puedes dejar este campo vacio")
            return redirect("ver_carrito_completo")

        try:
            carrito = Carrito.objects.filter(usuario=usuario, estado=1).latest()
        except Carrito.DoesNotExist:
            messages.error(request, "NO tienes un carrito activo actualmente ")
            return redirect("ver_carrito_completo")
        
        detalle = get_object_or_404(Detalle_carrito, carrito=carrito, producto_id=producto_id)

        if nueva_cantidad < 1:
            messages.error(request,"La cantidad debe ser al menos 1 ")
        elif nueva_cantidad > detalle.producto.cantidad:
            messages.error(request, "No hay suficiente stock disponible!!  ")

        else:
            detalle.cantidad = nueva_cantidad
            detalle.total = nueva_cantidad * detalle.producto.precio
            detalle.save()
            carrito.cantidad = sum(dc.cantidad for dc in carrito.detalles.all())
            carrito.save()
            messages.success(request, "Cantidad actualizada con exito!! ")

    return redirect("ver_carrito_completo")
    #     try:
    #         cantidad_raw = request.POST.get("cantidad", "")
    #         nueva_cantidad = int(cantidad_raw)

    #         if nueva_cantidad < 1:
    #             messages.warning(request, "La cantidad debe ser al menos 1.")
    #             return redirect("ver_carrito_completo")

    #     except ValueError:
    #         messages.error(request, "Cantidad inválida. Debe ser un número entero.")
    #         return redirect("ver_carrito_completo")

    #     carrito = request.session.get("carrito", {})

    #     if str(producto_id) not in carrito:
    #         messages.error(request, "El producto no se encuentra en el carrito.")
    #         return redirect("ver_carrito_completo")

    #     precio = float(carrito[str(producto_id)]['precio'])
    #     carrito[str(producto_id)]['cantidad'] = nueva_cantidad
    #     carrito[str(producto_id)]['total'] = round(precio * nueva_cantidad, 2)

    #     request.session["carrito"] = carrito
    #     messages.success(request, "Cantidad actualizada correctamente.")
    #     return redirect("ver_carrito_completo")

    # return redirect("ver_carrito_completo")

def eliminar_producto_carrito(request, producto_id):
    logueado = request.session.get("auth")
    if not logueado:
        messages.error(request,"Debes estar logueado para elimniar productos del carrito ")
        return redirect("login")
    
    usuario = get_object_or_404(User, id=logueado["id"])

    try:
        carrito = Carrito.objects.filter(usuario=usuario, estado=1).latest()
        detalle = Detalle_carrito.objects.filter(carrito=carrito, producto_id=producto_id).first()
        if detalle:
            detalle.delete()
            carrito.cantidad = sum(dc.cantidad for dc in carrito.detalles.all())
            carrito.save()
            messages.success(request, "Producto eliminado correctamente ")
        else:
            messages.error(request, "El producto no se encuentra el carrito.")
    except Carrito.DoesNotExist:
        messages.error(request, "NO hay un carrito activo actualmente ")
    
    return redirect("ver_carrito_completo")

    # if str(producto_id) in carrito:
    #     del carrito[str(producto_id)]
    #     request.session["carrito"] = carrito
    #     messages.success(request, "Producto eliminado del carrito.")
    # else:
    #     messages.warning(request, "El producto no se encuentra en el carrito.")

    # return redirect("ver_carrito_completo")

def vaciar_carrito(request):

    logueado = request.session.get("auth")
    if not logueado:
        return redirect("login")
    
    usuario = get_object_or_404(User, id=logueado["id"])

    try:
        carrito = Carrito.objects.filter(usuario=usuario, estado=1).latest()
        carrito.detalles.all().delete()
        carrito.cantidad = 0
        carrito.save()
        messages.success(request, "Carrito vaciado correctamnete!! ")
    except Carrito.DoesNotExist:
        messages.error("NO tienes carrito para vaciar!!  ")

    return redirect("ver_carrito_completo")

    # request.session["carrito"] = {}
    # messages.success(request, "Carrito vaciado correctamente.")
    # return redirect("ver_carrito_completo")

#Facturas y PAGOS 

def formulario_pago(request):
    logueado = request.session.get("auth")
    if not logueado:
        messages.error(request, "Debes iniciar sesión para usar el formulario de pago ")
        return redirect("login")
    
    try:
        carrito = Carrito.objects.filter(usuario_id=logueado["id"], estado=1).latest()
    except Carrito.DoesNotExist:
        messages.error(request, "NO se encontraron carritos por pagar!!")
        return redirect("ver_carrito_completo")
    
    detalles = carrito.detalles.all()
    total_general = sum(dc.total for dc in detalles)

    if request.method == "POST":    
        try:
            metodo_id = request.POST.get('metodo_pago')  
            metodo = Metodo_pago.objects.get(id=metodo_id) 
            nombre_destinatario = request.POST.get('nombre_destinatario')
            direccion = request.POST.get('direccion')
            especificaciones_direccion = request.POST.get('especificaciones')

            carrito.metodo_pago = metodo
            carrito.estado = 2
            carrito.servicio = 1
            carrito.nombre_destinatario = nombre_destinatario
            carrito.direccion = direccion
            carrito.especificaciones_direccion = especificaciones_direccion



            carrito.save()

        except Carrito.DoesNotExist:
            messages.error(request, "La factura no existe.")
            return redirect('ver_carrito_completo')
        
        print("metodo pago", carrito.metodo_pago)

        messages.success(request, "¡Pago exitoso!")
        return redirect('facturas_usuario')
    
    metodo = Metodo_pago.objects.all()

    contexto = {
        "carrito": carrito,
        "total_general": total_general,
        "detalles": detalles,
        "metodo_pago": metodo
    }

    return redirect('confirmar_pago', carrito_id = carrito.id)
    return render(request, 'usuarios/pago.html', contexto)


def procesar_pedido(request):
    logueado = request.session.get("auth")

    if not logueado:
        messages.error(request, "Debes loguearte primero para continuar... ")
        return redirect("login")
    
    usuario = get_object_or_404(User, id=logueado["id"])

    try:
        carrito = Carrito.objects.filter(usuario=usuario, estado=1).latest()
    except Carrito.DoesNotExist:
        messages.error(request, "Tu carrito esta vacio. ")
        return redirect("ver_carrito_completo")

    # Validación de stock
    for detalle in carrito.detalles.all():
        producto = detalle.producto
        if detalle.cantidad > producto.cantidad:
            messages.error(request, f"No hay suficiente stock para: {producto.nombre} ")
            return redirect('ver_carrito_completo')

    messages.success(request, "Tu pedido ha sido procesado correctamente.")
    return redirect('formulario_pago')

def confirmar_pago(request, carrito_id):
    logueado = request.session.get("auth")
    if not logueado:
        messages.error(request,"Debes iniciar sesion primero ")
        return redirect("login")
    
    carrito = get_object_or_404(Carrito, id=carrito_id, usuario=logueado["id"])
    detalles = Detalle_carrito.objects.filter(carrito=carrito)
    total_general = sum(detalle.producto.precio * detalle.cantidad for detalle in detalles)
    metodos_pago = Metodo_pago.objects.all()

    if carrito.estado == 2:
        messages.info(request, "Este pedido ya ha sido pagado.")
        return redirect("facturas_usuario")

    # Descontar productos del inventario
    if request.method  == 'POST':
        for detalle in carrito.detalles.all():
            producto = detalle.producto
            if detalle.cantidad > producto.cantidad:
                messages.error(request, f"No hay suficiente stock para {producto.nombre}.")
                return redirect("formulario_pago")

            producto.cantidad -= detalle.cantidad
            producto.save()

        carrito.estado = 2
        carrito.save()

        enviar_correo_confirmacion(carrito)
        messages.success(request, "Factura enviada a tu correo, gracias por tu compra... ")
        return redirect("facturas_usuario")
    contexto = {
        "carrito": carrito,
        "detalles": detalles,
        "total_general": total_general,
        "metodo_pago": metodos_pago
    }
    return render(request, "usuarios/pago.html", contexto)

#FACTURAS-----------------------------------------------------------------------------------------------------------------

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

    return render(request, "usuarios/facturas.html", contexto)

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

def politica_privacidad(request):
    return render(request, 'politica_privacidad.html')

#Enviar TOKENS

def enviar_token(email, token):
    asunto = "Verifica tu cuenta"
    mensaje = f"Tu código de verificación es: {token} "
    remitente = settings.EMAIL_HOST_USER
    destinatarios = [email]

    send_mail(asunto, mensaje, remitente, destinatarios)

def verificar_codigo(request):
    email = request.session.get('correo_verificacion')
    if not email:
        return redirect('register')
    
    if request.method == 'POST':
        codigo = request.POST.get("codigo")
        intentos = request.session.get('intentos', 0)

        try:
            usuario = User.objects.get(email=email)
            if usuario.token == codigo:
                usuario.verificado = True
                usuario.token = None
                usuario.save()
                messages.success(request,"Cuenta verificada correctamente!!  ")
                request.session.pop('correo_verificacion', None)
                request.session.pop('intentos', None)
                return redirect("login")
            else:
                intentos +=1
                request.session['intentos'] =  intentos
                if intentos >= 3:
                    messages.error(request, "Demasiados Intentos. Solicita un nuevo Código ")
                    return redirect("reenviar_token")
                messages.warning(request, f"Codigo Incorrecto. Te quedan {intentos}/3 ")
        except User.DoesNotExist:
            messages.error(request, "Usuario no encontrado")
            return redirect("register")
    return render(request, "verificar_codigo.html")

def reenviar_token(request):
    email = request.session.get("correo_verificacion")
    if not email:
        return redirect("register")
    
    try:
        usuario = User.objects.get(email=email)
        nuevo_token = str(uuid.uuid4()).split('-')[0]
        usuario.token = nuevo_token
        usuario.save()
        enviar_token(email, nuevo_token)
        request.session['intentos'] = 0
        messages.success(request, "Nuevo codigo enviado al correo!! ")
    except User.DoesNotExist:
            messages.error(request, "No se encontró el usuario ")
    
    return redirect("verificar_codigo")

#reservas-------------------------------------------------------------------------------------------------------

def formulario_pago_reserva(request):
    metodo_pago = Metodo_pago.objects.all()
    logueado = request.session.get("auth")
    if not logueado:
        messages.error(request, "Debes iniciar sesión para usar el formulario de pago ")
        return redirect("login")
    
    try:
        carrito = Carrito.objects.filter(usuario_id=logueado["id"], estado=1).latest('id')
    except Carrito.DoesNotExist:
        messages.error(request, "NO se encontraron carritos por pagar!!")
        return redirect("ver_carrito_completo")
    
    detalles = carrito.detalles.all()
    total_general = sum(dc.total for dc in detalles)

    if request.method == "POST":    
            
        metodo = request.POST.get('metodo_pago')
        nombre_destinatario = request.POST.get('nombre_destinatario')
        fecha_reserva = request.POST.get('fecha-reserva')

        carrito.fecha_reserva = fecha_reserva
        carrito.nombre_destinatario = nombre_destinatario
        carrito.servicio = 2
        carrito.estado = 1
        carrito.metodo_pago = metodo

        errores = []

        if not fecha_reserva:
            errores.append("El parametro de la fecha debe tener un valor!! ")
        else:
            fecha_obj = parse_datetime(fecha_reserva)

            if not fecha_obj:
                errores.append("Asegurate de llenar la fecha correctamente")
            else:
                ahora = timezone.now()
                if timezone.is_naive(fecha_obj):
                    fecha_obj = make_aware(fecha_obj)

                if fecha_obj < ahora + timezone.timedelta(hours=24):
                    errores.append("La fecha de reserva debe ser al menos 24 horas después de la actual.")
        
        if not nombre_destinatario:
            errores.append("El parametro Nombre debe tener un valor!! ")
        else:
            if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ ]+", nombre_destinatario):
                errores.append("Nombre Invalido. Solo se permiten letras y espacios... ")

        if not metodo or metodo == "":
            errores.append("Debe seleccionar un metodo de pago para continuar!!! ")

        carrito.save()

        if errores:
            for error in errores:
                messages.warning(request, error)
            return redirect("reservar")
        


        messages.success(request, "¡Pago exitoso!")
        return redirect('facturas_usuario')
    
    contexto = {
        "carrito": carrito,
        "total_general": total_general,
        "detalles": detalles,
        "metodo_pago": metodo_pago
    }

    return render(request, 'usuarios/reservas.html', contexto)