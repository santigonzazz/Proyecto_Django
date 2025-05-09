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
import traceback


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
# from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError 
# Create your views here.

#principales-------------------------------------------------------------------------------------------------------------
def index(request): 
    cat_id = request.GET.get("cat")
    total = 0
    total_general = 0
    carrito_actual = None
    detalles = []
    producto_filtro = request.GET.get("busqueda_producto", "")

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
    
    if producto_filtro:
        productos = productos.filter(nombre__icontains=producto_filtro)

    sin_resultados = False
    if producto_filtro and not productos.exists():
        sin_resultados = True

    user = request.session.get("auth", {}).get("id")
    disponibilidad_carrito = []
    
    if user:
        try:
            user_obj = User.objects.get(id=user)
            carrito_actual = Carrito.objects.filter(usuario=user_obj, estado=1).latest('fecha')
            detalles = Detalle_carrito.objects.filter(carrito=carrito_actual)

            carrito_mini = []  # Para almacenar los productos visibles

            for item in detalles:
                if item.producto.disponibilidad == "SI":
                    item.total = item.cantidad * item.producto.precio
                    total_general += item.total

                    carrito_mini.append({
                        "nombre": item.producto.nombre,
                        "cantidad": item.cantidad,
                        "precio": item.producto.precio,
                        "total": item.total
                    })
                else:
                    disponibilidad_carrito.append(
                        f"El producto: {item.producto.nombre} que agregaste no se encuentra disponibile actualmente!! Producto eliminado de tu carrito "
                    )

            # Actualizamos el carrito mini en sesión
            request.session["carrito_mini"] = carrito_mini
            request.session["total_mini"] = total_general

        except Carrito.DoesNotExist:
            carrito_actual = None
            detalles = []
            total_general = 0
            request.session["carrito_mini"] = []
            request.session["total_mini"] = 0

    contexto = {
        "productoInfo": productos,
        "categorias": categorias,
        "carrito": detalles,
        "detalles": detalles,
        'total': total,
        "totalg": total_general,
        "producto_filtro": producto_filtro,
        "sin_resultados": sin_resultados,
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
    cat = Categoria.objects.all()
    carrito_mini = request.session.get("carrito_mini", [])
    total_mini = request.session.get("total_mini", 0)

    user = request.session.get("auth", {}).get("id")
    detalles = []
    total_general = 0

    if user:
        try:
            user_obj = User.objects.get(id=user)
            carrito_actual = Carrito.objects.filter(usuario=user_obj, estado=1).latest('fecha')
            detalles = Detalle_carrito.objects.filter(carrito=carrito_actual)

            for item in detalles:
                if item.producto.disponibilidad == "SI":
                    item.total = item.cantidad * item.producto.precio
                    total_general += item.total

        except Carrito.DoesNotExist:
            detalles = []
            total_general = 0

    return render(request, 'about.html', {
        'carrito': detalles,
        'detalles': detalles,
        'totalg': total_general,
        'carrito_items': carrito_mini,
        'total_general': total_mini,
        'categorias': cat,
    })



def contactanos(request):
    
    tipo_opciones = Pqrs.TIPOS
    carrito_mini = request.session.get("carrito_mini", [])
    total_mini = request.session.get("total_mini", 0)
    detalles = []
    total_general = 0
    
    if request.method == 'POST':
        user_id = request.session.get("auth", {}).get("id")
        if not user_id:
            messages.error(request, "Debes iniciar sesión para editar tu perfil.")
            return redirect("login")
        
        errores = []

        nombre = request.POST.get("nombre", "").strip()
        email_ingresado = request.POST.get("email", "").strip()
        email = request.session.get("auth", {}).get("email")
        mensaje = request.POST.get("mensaje", "").strip()
        tipo = request.POST.get("tipo")

        try:
            tipo=int(tipo)
        except (ValueError, TypeError):
            errores.append("Tipo de mensaje inválido.")
        else:
            valores_validos = [op[0] for op in Pqrs.TIPOS]

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
        
        if not tipo or tipo not in valores_validos:
            errores.append("Debes seleccionar el tipo del mensaje!! ")
        
        if email != email_ingresado:
            errores.append("No puedes cambiar tu correo si quieres enviar el mensaje!! ")

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
        user_id = request.session.get("auth", {}).get("id")
        if user_id:
            try:
                user_obj = User.objects.get(id=user_id)
                carrito_actual = Carrito.objects.filter(usuario=user_obj, estado=1).latest('fecha')
                detalles = Detalle_carrito.objects.filter(carrito=carrito_actual)

                for item in detalles:
                    if item.producto.disponibilidad == "SI":
                        item.total = item.cantidad * item.producto.precio
                        total_general += item.total

            except Carrito.DoesNotExist:
                detalles = []
                total_general = 0
        return render(request, 'contactanos.html', {"tipo_opciones": tipo_opciones,
                                                    'carrito': detalles,
                                                    'detalles': detalles,
                                                    'totalg': total_general,
                                                    'carrito_items': carrito_mini,
                                                    'total_general': total_mini})


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
def editar_perfil(request):
    carrito_mini = request.session.get("carrito_mini", [])
    total_mini = request.session.get("total_mini", 0)
    detalles = []
    total_general = 0
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
        
        if user_id:
            try:
                user_obj = User.objects.get(id=user_id)
                carrito_actual = Carrito.objects.filter(usuario=user_obj, estado=1).latest('fecha')
                detalles = Detalle_carrito.objects.filter(carrito=carrito_actual)

                for item in detalles:
                    if item.producto.disponibilidad == "SI":
                        item.total = item.cantidad * item.producto.precio
                        total_general += item.total

            except Carrito.DoesNotExist:
                detalles = []
                total_general = 0
        
        return render(request, "usuarios/user-Crud.html", {'carrito': detalles,
                                                    'detalles': detalles,
                                                    'totalg': total_general,
                                                    'carrito_items': carrito_mini,
                                                    'total_general': total_mini})

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


#CRUD categorias-----------------------------------------------------------------------------------

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

def agregar_categoria(request):
    verificar = request.session.get("auth", False)

    if verificar:
        if verificar["rol"] == 1:
            if request.method == "POST":
                nombre = request.POST.get("nombre", "").strip()
                descripcion = request.POST.get("descripcion", "").strip()

                if not nombre or not descripcion:
                    messages.error(request, "Todos los campos son obligatorios.")
                    return redirect("crud_categoria")
                
                if len(nombre) < 2:
                    messages.error(request, "El nombre debe tener al menos 2 caracteres.")
                    return redirect("crud_categoria")

                if not nombre.replace(" ", "").isalpha():
                    messages.error(request, "El nombre solo puede contener letras y espacios.")
                    return redirect("crud_categoria")

                try:
                    nueva_categoria = Categoria(nombre=nombre, descripcion=descripcion)
                    nueva_categoria.save()
                    messages.success(request, "Categoría añadida correctamente!")
                except Exception as e:
                    messages.error(request, f"Error al añadir categoría: {e}")

            return redirect("crud_categoria")
        else:
            messages.info(request, "Usted no tiene permisos para éste módulo...")
        return redirect( "index")
    
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")


def editar_categoria(request, categoria_id):
    verificar = request.session.get("auth", False)

    if verificar:
        if verificar["rol"] == 1:
            try:
                cate = Categoria.objects.get(pk=categoria_id)
                if request.method == 'POST':
                    nombre = request.POST.get("nombre", "").strip()
                    descripcion = request.POST.get("descripcion", "").strip()

                    if not nombre or not descripcion:
                        messages.error(request, "Todos los campos son obligatorios.")
                        return redirect("crud_categoria")

                    if len(nombre) < 2:
                        messages.error(request, "El nombre debe tener al menos 2 caracteres.")
                        return redirect("crud_categoria")

                    if not nombre.replace(" ", "").isalpha():
                        messages.error(request, "El nombre solo puede contener letras y espacios.")
                        return redirect("crud_categoria")

                    cate.nombre = nombre
                    cate.descripcion = descripcion
                    cate.save()
                    messages.success(request, "Categoría actualizada correctamente.")
                return redirect("crud_categoria")
            except Categoria.DoesNotExist:
                messages.error(request, "Categoría no encontrada.")
                return redirect("crud_categoria")
            except Exception as e:
                messages.error(request, f"Error al actualizar categoría: {e}")
                return redirect("crud_categoria")
        else:
            messages.info(request, "Usted no tiene permisos para éste módulo...")
        return redirect( "index")
    
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")


def eliminar_categoria(request, id_categoria):
    verificar = request.session.get("auth", False)

    if verificar:
        if verificar["rol"] == 1:
            try:
                categoria = Categoria.objects.get(pk=id_categoria)

                # verificar productos relacionados:
                if hasattr(categoria, 'producto_set') and categoria.producto_set.exists():
                    messages.warning(request, "No se puede eliminar la categoría porque tiene productos asociados.")
                    return redirect("crud_categoria")

                categoria.delete()
                messages.success(request, "Categoría eliminada correctamente.")
            except Categoria.DoesNotExist:
                messages.error(request, "La categoría no existe o ya fue eliminada.")
            except ProtectedError:
                messages.warning(request, "No se puede eliminar esta categoría porque está protegida por relaciones.")
            except IntegrityError:
                messages.warning(request, "No se puede eliminar esta categoría debido a restricciones de la base de datos.")
            except Exception as e:
                messages.error(request, f"Error inesperado: {e}")
            
            return redirect("crud_categoria")
        else:
            messages.info(request, "Usted no tiene permisos para éste módulo...")
        return redirect( "index")
    
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")



#CRUD productos-----------------------------------------------------------------------------------

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
    verificar = request.session.get("auth", False)

    if verificar:
        if verificar["rol"] == 1:
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
        else:
            messages.info(request, "Usted no tiene permisos para éste módulo...")
        return redirect( "index")
    
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")


def editar_producto(request, producto_id):
    verificar = request.session.get("auth", False)
    if verificar:
        if verificar["rol"] == 1:
            p = get_object_or_404(Producto, pk=producto_id)
            categorias_existentes = Categoria.objects.all()

            if request.method == 'POST':
                nombre = request.POST.get("nombre", "").strip()
                precio_str = request.POST.get("precio", "").strip()
                stock_str = request.POST.get("stock", "").strip()
                descripcion = request.POST.get("descripcion", "").strip()
                disponibilidad_str = request.POST.get("disponibilidad")
                nuevas_categorias_ids = request.POST.getlist("categorias")
                foto_nueva = request.FILES.get("foto")
                errores = {}

                # Validaciones Backend
                if not nombre:
                    errores["nombre"] = "El nombre es obligatorio."
                elif len(nombre) < 2:
                    errores["nombre"] = "El nombre debe tener al menos 2 caracteres."
                elif not all(char.isalpha() or char.isspace() or char in 'ñÑ' for char in nombre):
                    errores["nombre"] = "El nombre solo puede contener letras y espacios."

                if not precio_str:
                    errores["precio"] = "El precio es obligatorio."
                else:
                    try:
                        precio = float(precio_str)
                        if precio < 0:
                            errores["precio"] = "El precio no puede ser negativo."
                    except ValueError:
                        errores["precio"] = "El precio debe ser un número válido."
                    else:
                        p.precio = precio

                if stock_str == "":
                    errores["stock"] = "El stock es obligatorio."
                else:
                    try:
                        stock = int(stock_str)
                        if stock < 0:
                            errores["stock"] = "El stock no puede ser negativo."
                    except ValueError:
                        errores["stock"] = "El stock debe ser un número entero válido."
                    else:
                        p.cantidad = stock

                if not descripcion:
                    errores["descripcion"] = "La descripción es obligatoria."

                if foto_nueva:
                    if not foto_nueva.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                        errores["foto"] = "Solo se permiten archivos JPG y PNG."
                    # Aquí podrías añadir validaciones adicionales para el tamaño del archivo si es necesario
                    else:
                        p.foto = foto_nueva
                
                if disponibilidad_str not in ["SI", "NO"]:
                    errores["disponibilidad"] = "Debe seleccionar una opción válida."

                if not nuevas_categorias_ids:
                    errores["categorias"] = "Debe seleccionar al menos una categoría."
                else:
                    nuevas_categorias = []
                    for cat_id in nuevas_categorias_ids:
                        try:
                            categoria = Categoria.objects.get(id=cat_id)
                            nuevas_categorias.append(categoria)
                        except Categoria.DoesNotExist:
                            errores["categorias"] = f"La categoría con ID {cat_id} no existe."

                if errores:
                    contexto = {
                        "producto": p,
                        "catProduct": categorias_existentes,
                        "categorias_producto": p.fk2_producto_categoria.all(),
                        "errores": errores,
                    }
                    return render(request, "admin/admin-CRUD-productos.html", contexto)
                else:
                    p.nombre=nombre
                    p.precio=precio
                    p.cantidad=stock
                    p.descripcion=descripcion
                    p.disponibilidad=disponibilidad_str
                    p.save()

                    # Actualizar las categorías
                    ProductoCategoria.objects.filter(producto=p).delete()
                    for categoria in nuevas_categorias:
                        ProductoCategoria.objects.create(producto=p, categoria=categoria)

                    messages.success(request, "Producto actualizado correctamente.")
                    return redirect("crud_productos")

            else:
                contexto = {
                    "producto": p,
                    "catProduct": categorias_existentes,
                    "categorias_producto": p.fk2_producto_categoria.all()
                }
                return render(request, "admin/admin-CRUD-productos.html", contexto) 
        else:
                    messages.info(request, "Usted no tiene permisos para éste módulo...")
                    return redirect("index")
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")


def agregar_producto(request):
    verificar = request.session.get("auth", False)

    if verificar:
        if verificar["rol"] == 1:
            categorias_existentes = Categoria.objects.all()

            if request.method == 'POST':
                nombre = request.POST.get("nombre", "").strip()
                cantidad_str = request.POST.get("cantidad", "").strip()
                descripcion = request.POST.get("descripcion", "").strip()
                precio_str = request.POST.get("precio", "").strip()
                disponibilidad_str = request.POST.get("disponibilidad")
                nuevas_categorias_ids = request.POST.getlist("categorias")
                foto = request.FILES.get("foto")
                errores = {}

                # Validaciones Backend
                if not nombre:
                    errores["nombre"] = "El nombre es obligatorio."
                elif len(nombre) < 2:
                    errores["nombre"] = "El nombre debe tener al menos 2 caracteres."
                elif not all(char.isalpha() or char.isspace() or char in 'ñÑ' for char in nombre):
                    errores["nombre"] = "El nombre solo puede contener letras y espacios."

                if not cantidad_str:
                    errores["cantidad"] = "La cantidad es obligatoria."
                else:
                    try:
                        cantidad = int(cantidad_str)
                        if cantidad < 1:
                            errores["cantidad"] = "La cantidad debe ser mayor o igual a 1."
                    except ValueError:
                        errores["cantidad"] = "La cantidad debe ser un número entero válido."
                    else:
                        cantidad = cantidad # Usar la cantidad convertida

                if not descripcion:
                    errores["descripcion"] = "La descripción es obligatoria."

                if not precio_str:
                    errores["precio"] = "El precio es obligatorio."
                else:
                    try:
                        precio = float(precio_str)
                        if precio < 0:
                            errores["precio"] = "El precio no puede ser negativo."
                    except ValueError:
                        errores["precio"] = "El precio debe ser un número válido."
                    else:
                        precio = precio # Usar el precio convertido

                if not disponibilidad_str or disponibilidad_str not in ["SI", "NO"]:
                    errores["disponibilidad"] = "La disponibilidad es obligatoria."

                if not nuevas_categorias_ids:
                    errores["categorias"] = "Debe seleccionar al menos una categoría."
                else:
                    nuevas_categorias = []
                    for cat_id in nuevas_categorias_ids:
                        try:
                            categoria = Categoria.objects.get(id=cat_id)
                            nuevas_categorias.append(categoria)
                        except Categoria.DoesNotExist:
                            errores["categorias"] = f"La categoría con ID {cat_id} no existe." # Mensaje más específico

                if not foto:
                    errores["foto"] = "La foto es obligatoria."
                elif not foto.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    errores["foto"] = "Solo se permiten archivos JPG y PNG."
                # Aquí podrías añadir validaciones adicionales para el tamaño del archivo si es necesario

                if errores:
                    contexto = {
                        "catProduct": categorias_existentes,
                        "errores": errores,
                        "nombre": nombre,
                        "cantidad": cantidad_str,
                        "descripcion": descripcion,
                        "precio": precio_str,
                        "disponibilidad_seleccionada": disponibilidad_str,
                        "categorias_seleccionadas": nuevas_categorias_ids,
                    }
                    return render(request, "admin/admin-CRUD-productos.html", contexto)
                else:
                    # Crear el nuevo producto
                    nuevo_producto = Producto.objects.create(
                        nombre=nombre,
                        cantidad=cantidad,
                        descripcion=descripcion,
                        precio=precio,
                        disponibilidad=disponibilidad_str,
                        foto=foto
                    )

                    # Asignar las categorías
                    for categoria in nuevas_categorias:
                        ProductoCategoria.objects.create(producto=nuevo_producto, categoria=categoria)

                    messages.success(request, "Producto añadido correctamente.")
                    return redirect("crud_productos") # Asegúrate de que esta URL exista

            else:
                contexto = {
                    "catProduct": categorias_existentes
                }
                return render(request, "admin/admin-CRUD-productos.html", contexto)
        else:
                    messages.info(request, "Usted no tiene permisos para éste módulo...")
                    return redirect("index")
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")
    
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
    verificar = request.session.get("auth", False)

    if verificar:
        if verificar["rol"] == 1:
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
        else:
            messages.info(request, "Usted no tiene permisos para éste módulo...")
        return redirect( "index")
    
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")

def eliminar_usuario(request, id_usuario):
    verificar = request.session.get("auth", False)

    if verificar:
        if verificar["rol"] == 1:
            try:
                usuario = User.objects.get(pk=id_usuario)
                usuario.delete()
                messages.success(request, "Usuario eliminado correctamente.")
            except IntegrityError:
                messages.warning(request, "Error: No puede eliminar el usuario, está en uso.")
            except Exception as e:
                messages.error(request, f"Error: {e}")

            return redirect("adminCRUDU")
        else:
            messages.info(request, "Usted no tiene permisos para éste módulo...")
        return redirect( "index")
    
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")

def crear_usuario_admin(request):
    verificar = request.session.get("auth", False)
    if verificar:
        if verificar["rol"] == 1:
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
        else:
                messages.info(request, "Usted no tiene permisos para éste módulo...")
                return redirect( "index")
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")
    

def editar_usuario_admin(request, id_usuario):
    verificar = request.session.get("auth", False)
    if verificar:
        if verificar["rol"] == 1:
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
        else:
            messages.info(request, "Usted no tiene permisos para éste módulo...")
        return redirect( "index")
    
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")

def eliminar_usuario_admin(request, id_usuario):
    verificar = request.session.get("auth", False)
    if verificar:
        if verificar["rol"] == 1:
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
        else:
            messages.info(request, "Usted no tiene permisos para éste módulo...")
        return redirect( "index")
    
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")

#metodos de pago

def metodo_pago(request):
    metodo = Metodo_pago.objects.all()
    verificar = request.session.get("auth", False)

    if verificar:
        if verificar["rol"] == 1:
            contexto = {
                "metodo_pago": metodo
            }
        else:
            messages.info(request, "Usted no tiene permisos para éste módulo...")
            return redirect( "index")
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")
    return render(request, "admin/admin-metodo-pago.html", contexto)

def crear_metodo_pago(request):
    verificar = request.session.get("auth", False)
    if verificar:
        if verificar["rol"] == 1:
            if request.method == 'POST':
                nombre = request.POST.get("nombre", "").strip()
                disponibilidad = request.POST.get("disponibilidad", "")

                errores = []

                if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ ]{2,}$', nombre):
                    errores.append("El nombre solo puede contener letras y debe tener al menos 2 caracteres.")

                if not disponibilidad:
                    errores.append("Debe seleccionar la disponibilidad del producto")
                try:
                    disponibilidad= disponibilidad
                except (ValueError, TypeError):
                    errores.append("Tipo de mensaje inválido.")
                else:
                    valores_validos = [op[0] for op in Metodo_pago.DISPONIBILIDAD]
                
                if not disponibilidad or disponibilidad not in valores_validos:
                    errores.append("Debes seleccionar la disponibilidad Correcta ")
                if errores:
                    for error in errores:
                        messages.error(request, error)
                    return redirect("metodo_pago")

                try:
                    nuevo_usuario = Metodo_pago(
                        nombre=nombre,
                        disponibilidad=disponibilidad
                    )
                    nuevo_usuario.save()
                    messages.success(request, "Categoría creada correctamente.")
                except Exception as e:
                    messages.error(request, f"Error al crear usuario: {e}")

                return redirect("metodo_pago")
            else:
                return render(request, "admin/admin-metodo-pago.html")
        else:
                messages.info(request, "Usted no tiene permisos para éste módulo...")
                return redirect("index")
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")
    
def eliminar_metodo_pago(request, id_metodo_pago):
    verificar = request.session.get("auth", False)
    try:
        if verificar["rol"] == 1:
            if request.method == 'POST':
                metodo_pago = get_object_or_404(Metodo_pago, pk=id_metodo_pago)

                metodo_pago.delete()
                messages.success(request, "Metodo de pago eliminado correctamente.")
            else:
                    messages.info(request, "Usted no tiene permisos para éste módulo...")
                    return redirect("index")
        else:
            messages.info(request, "Debe loguearse primero...")
            return redirect("login")
    except Metodo_pago.DoesNotExist:
        messages.error("El metodo de pago no existe.")
        return redirect('metodo_pago')
    except Exception as e:
        messages.error(request, f"Error inesperado: {e}")
    
    return redirect("metodo_pago")
    

def editar_metodo_pago(request, id_metodo_pago):
    try:    
        verificar = request.session.get("auth", False)
        if verificar:
            if verificar["rol"] == 1:
                mp = get_object_or_404(Metodo_pago, pk=id_metodo_pago)

                if request.method == 'POST':
                    nombre = request.POST.get("nombre", "").strip()
                    disponibilidad = request.POST.get("disponibilidad", "")

                    errores = []

                    if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ ]{2,}$', nombre):
                        errores.append("El nombre solo puede contener letras y debe tener al menos 2 caracteres.")

                    if errores:
                        for error in errores:
                            messages.error(request, error)
                        return redirect("metodo_pago")
                    else:

                        mp.nombre = nombre
                        mp.disponibilidad = disponibilidad
                        mp.save()

                        messages.success(request, "Metodo pago actualizado correctamente.")
                        return redirect("metodo_pago")

                else:
                    return redirect('metodo_pago') 
            else:
                        messages.info(request, "Usted no tiene permisos para éste módulo...")
                        return redirect("index")
        else:
            messages.info(request, "Debe loguearse primero...")
            return redirect("login")
    except Metodo_pago.DoesNotExist:
        messages.error("El metodo de pago no existe.")
        return redirect('metodo_pago')
    except Exception as e:
        messages.error(request, "Error al editar el metodo de pago")
        return redirect('metodo_pago')
    
    
def reservas_admin(request):
    reserva = Detalle_carrito.objects.filter(carrito__servicio=2).exclude(carrito__estado=3)
    verificar = request.session.get("auth", False)

    if verificar:
        if verificar["rol"] == 1:
            contexto = {
                "reserva": reserva
            }
        else:
            messages.info(request, "Usted no tiene permisos para éste módulo...")
            return redirect( "index")
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")
    return render(request, "admin/admin-reservas.html", contexto)

def reserva_pagada(request, id_carrito):
    verificar = request.session.get("auth", False)
    try:
        carrito = get_object_or_404(Carrito, id=id_carrito)

        if carrito.estado == 3:
            messages.error(request, "Esta reserva ya fue pagada")
            return redirect("reservas_admin")

        if verificar:
            if verificar["rol"] == 1:
                carrito.estado = 3
                carrito.save()
                enviar_correo_confirmacion(carrito)

                messages.success(request, "Reserva marcada como finalizada correctamente.")
                return redirect("reservas_admin")
            else:
                messages.info(request, "Usted no tiene permisos para éste módulo...")
                return redirect( "index")
        else:
            messages.info(request, "Debe loguearse primero...")
            return redirect("login")
    except Carrito.DoesNotExist:
        messages.error(request, "No se encontró la reserva.")
        return redirect("reservas_admin")
    except Exception as e:
        messages.error(request, "Error al cargar la pagina")
        return redirect("reservas_admin")

#funciones del sistema------------------------------------------------------------------------------------

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

def ver_carrito_completo(request):

    logueado = request.session.get("auth")
    if not logueado:
        messages.error(request, "Inicia sesión para ver el carrito.")
        return redirect("login")

    usuario = get_object_or_404(User, id=logueado["id"])
    try:
        carrito = Carrito.objects.filter(usuario=usuario, estado=1).latest()
        detalles = carrito.detalles.all()
        productos_no_disponibles = []
        for item in detalles:
            if item.producto.disponibilidad == "NO":
                productos_no_disponibles.append(item.producto.nombre)
                item.delete()

        if productos_no_disponibles:
            for nombre in productos_no_disponibles:
                messages.error(request,f"El producto {nombre} que seleccionaste anteriormente no se encuentra disponible actualmente")
            carrito.cantidad = sum(dc.cantidad for dc in carrito.detalles.all())
            carrito.save()
            return redirect("ver_carrito_completo")
        
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

def actualizar_cantidad(request, producto_id):
    if request.method == "POST":
        logueado = request.session.get("auth")
        if not logueado:
            return redirect("login")
        
        usuario = get_object_or_404(User, id=logueado["id"])
        nueva_cantidad = request.POST.get("cantidad")
        if not nueva_cantidad:
            messages.error(request, "No puedes dejar este campo vacío")
            return redirect("ver_carrito_completo")
        

        if not re.fullmatch(r"\d+", nueva_cantidad):
            messages.error(request, "Solo se permiten números positivos!! ")
            return redirect("ver_carrito_completo")
        nueva_cantidad = int(nueva_cantidad)  
        try:
            carrito = Carrito.objects.filter(usuario=usuario, estado=1).latest()
        except Carrito.DoesNotExist:
            messages.error(request, "NO tienes un carrito activo actualmente ")
            return redirect("ver_carrito_completo")
        
        detalle = get_object_or_404(Detalle_carrito, carrito=carrito, producto_id=producto_id)
        if nueva_cantidad < 1:
            messages.error(request, "La cantidad debe ser al menos 1 ")
        elif nueva_cantidad > detalle.producto.cantidad:
            messages.error(request, "No hay suficiente stock disponible!!  ")
        else:
            detalle.cantidad = nueva_cantidad
            detalle.total = nueva_cantidad * detalle.producto.precio
            detalle.save()
            carrito.cantidad = sum(dc.cantidad for dc in carrito.detalles.all())
            carrito.save()
            messages.success(request, "Cantidad actualizada con éxito!! ")
    return redirect("ver_carrito_completo")

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
    
    return redirect("index")

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

#Facturas y PAGOS 

def formulario_pago(request):
    logueado = request.session.get("auth")
    if not logueado:
        messages.error(request, "Debes iniciar sesión para usar el formulario de pago.")
        return redirect("login")
    
    try:
        carrito = Carrito.objects.filter(usuario_id=logueado["id"], estado=1).latest()
    except Carrito.DoesNotExist:
        messages.error(request, "No se encontraron carritos por pagar.")
        return redirect("ver_carrito_completo")
    
    detalles = carrito.detalles.all()
    productos_no_disponibles = []
    total_general = sum(dc.total for dc in detalles if dc.producto.disponibilidad == "SI")

    for item in detalles:
        if item.producto.disponibilidad == "NO":
            productos_no_disponibles.append(item.producto.nombre)
            item.delete()
    
    if productos_no_disponibles:
        for nombre in productos_no_disponibles:
            messages.error(request, f"El producto: {nombre} que seleccionaste anteriormente, no se encuentra disponible actualmente!! ")
        carrito.cantidad = sum(dc.cantidad for dc in carrito.detalles.all())
    
    total_general = sum(dc.total for dc in carrito.detalles.all())

    if request.method == "POST":
        errores = []

        metodo_id = request.POST.get('metodo_pago')
        metodo_instancia = None

        if not metodo_id or not metodo_id.isdigit(): 
            errores.append("Debe seleccionar un método de pago válido.")
        else:
            try:
                metodo_instancia = Metodo_pago.objects.get(pk=int(metodo_id))
                carrito.metodo_pago = metodo_instancia
            except Metodo_pago.DoesNotExist:
                errores.append("El método de pago seleccionado no existe.")

        nombre_destinatario = request.POST.get('nombre_destinatario')
        direccion = request.POST.get('direccion')
        especificaciones_direccion = request.POST.get('especificaciones')

        if not nombre_destinatario:
            errores.append("El parámetro 'Nombre' debe tener un valor.")
        elif not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ ]+", nombre_destinatario):
            errores.append("Nombre inválido. Solo se permiten letras y espacios.")

        if not direccion:
            errores.append("El parámetro 'Dirección' debe tener un valor.")

        if errores:
            for error in errores:
                messages.warning(request, error)
            return redirect("formulario_pago")

        carrito.nombre_destinatario = nombre_destinatario
        carrito.direccion = direccion
        carrito.especificaciones_direccion = especificaciones_direccion
        carrito.servicio = 1
        carrito.estado = 3 
        carrito.save()

        enviar_correo_confirmacion(carrito)

        messages.success(request, "¡Pago exitoso!")
        return redirect("facturas_usuario")

    metodos_pago = Metodo_pago.objects.all()

    contexto = {
        "carrito": carrito,
        "total_general": total_general,
        "detalles": detalles,
        "metodo_pago": metodos_pago
    }

    return redirect('confirmar_pago', carrito_id = carrito.id)


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
    
    try:
        carrito = get_object_or_404(Carrito, id=carrito_id, usuario=logueado["id"])
        detalles = Detalle_carrito.objects.filter(carrito=carrito)
        total_general = sum(detalle.producto.precio * detalle.cantidad for detalle in detalles if detalle.producto.disponibilidad == "SI")
        metodos_pago = Metodo_pago.objects.all()

        if carrito.estado == 3:
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

            carrito.estado = 3

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
    except Exception as e:
        messages.error(request, "No se puede acceder ")
        return redirect("index")

#FACTURAS-----------------------------------------------------------------------------------------------------------------

def facturas_usuario(request):
    logueado = request.session.get("auth")
    carrito_mini = request.session.get("carrito_mini", [])
    total_mini = request.session.get("total_mini", 0)
    detalles = []
    total_general = 0
    if not logueado:
        messages.error(request, "Debes iniciar sesión para ver tus facturas.")
        return redirect("login")

    usuario_id = logueado["id"]
    fecha_filtro = request.GET.get("fecha", "")

    facturas = Carrito.objects.filter(usuario_id=usuario_id).order_by("-fecha")

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

    if usuario_id:
            try:
                user_obj = User.objects.get(id=usuario_id)
                carrito_actual = Carrito.objects.filter(usuario=user_obj, estado=1).latest('fecha')
                detalles = Detalle_carrito.objects.filter(carrito=carrito_actual)

                for item in detalles:
                    if item.producto.disponibilidad == "SI":
                        item.total = item.cantidad * item.producto.precio
                        total_general += item.total

            except Carrito.DoesNotExist:
                detalles = []
                total_general = 0
    contexto = {
        "facturas_con_totales": facturas_con_totales,
        "fecha_filtro": fecha_filtro,
        'carrito': detalles,
        'detalles': detalles,
        'totalg': total_general,
        'carrito_items': carrito_mini,
        'total_general': total_mini
    }

    return render(request, "usuarios/facturas.html", contexto)

def exportar_factura_pdf(request, factura_id):
    # Asegúrate que el campo se llama 'usuario', cámbialo si es necesario
    try:
        if factura_id:
            logueado = request.session.get("auth")
            carrito = Carrito.objects.get(id=factura_id)
            detalles = Detalle_carrito.objects.filter(carrito=carrito)
            total = detalles.aggregate(total=Sum('total'))['total'] or 0

            if carrito.usuario_id != logueado["id"]:
                messages.error(request,"No tienes acceso a esta factura!! ")
                return redirect("index")

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
    except Carrito.DoesNotExist :
        messages.error(request, "Factura no encontrada")
        return redirect("index")


def enviar_correo_confirmacion(carrito):
    asunto = f"Confirmación de pago - Pedido #{carrito.id}"
    destinatario = carrito.usuario.email

    try:
        mensaje_html = render_to_string('correo_confirmacion.html', {
            'carrito': carrito,
            'detalles': carrito.detalles.all(),
            'total': sum(detalle.producto.precio * detalle.cantidad for detalle in carrito.detalles.all()),
        })

        send_mail(
            asunto,
            '',
            settings.EMAIL_HOST_USER,
            [destinatario],
            html_message=mensaje_html
        )
        print("Correo enviado correctamente")
    except Exception as e:
        print("Error al enviar el correo:")
        print(traceback.format_exc())

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

        errores = []
        metodo_instancia = None

        if not metodo or not metodo.isdigit():
            errores.append("Debe seleccionar un metodo de pago para continuar!!! ")
        else:
            try:
                metodo_instancia = Metodo_pago.objects.get(pk=metodo)
                carrito.metodo_pago = metodo_instancia
            except Metodo_pago.DoesNotExist:
                errores.append("El método de pago seleccionado no existe.")

        if metodo_instancia:
            carrito.servicio = 2
            carrito.estado = 1 if metodo_instancia.id != 2 else 2

        carrito.fecha_reserva = fecha_reserva
        carrito.nombre_destinatario = nombre_destinatario

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

        if errores:
            for error in errores:
                messages.warning(request, error)
            return redirect("reservar")
        
        carrito.save()

        messages.success(request, "¡Pago exitoso!")
        return redirect('reservas_pendientes')
    
    contexto = {
        "carrito": carrito,
        "total_general": total_general,
        "detalles": detalles,
        "metodo_pago": metodo_pago
    }

    return render(request, 'usuarios/reservas.html', contexto)

def reservas_pendientes(request):
    logueado = request.session.get("auth")
    
    if not logueado:
        messages.error(request, "Debes iniciar sesión para ver tus facturas.")
        return redirect("login")

    usuario_id = logueado["id"]
    fecha_filtro = request.GET.get("fecha", "")

    facturas = Carrito.objects.filter(usuario_id=usuario_id).order_by("-fecha")

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

    return render(request, "usuarios/reservas_pendientes.html", contexto)

#Recupeara contraseña 

def solicitar_recuperacion(request):
    if request.method == "POST":
        email = request.POST.get("email")
        if not email:
            messages.error(request, "Debes ingresar un correo")
            return redirect('solicitar_recuperacion')
        try:
            usuario = User.objects.get(email=email)
            token = str(uuid.uuid4()).split('-')[0]
            usuario.token = token
            usuario.save()

            request.session['correo_recuperacion'] = email
            request.session['intentos_recuperacion'] = 0

            asunto = "Recuperación de contraseña"
            mensaje = f"Tu código para recuperar la contraseña es: {token}"
            remitente = settings.EMAIL_HOST_USER
            destinatarios = [email]
            send_mail(asunto, mensaje, remitente, destinatarios)

            messages.success(request, "Código de recuperación enviado a tu correo.")
            return redirect("verificar_token_recuperacion")
        except User.DoesNotExist:
            messages.error(request, "No existe una cuenta con ese correo.")
    return render(request, "recuperar_clave.html")

def verificar_token_recuperacion(request):
    email = request.session.get("correo_recuperacion")
    if not email:
        messages.error(request, "Debes ingresar un correo ")
        return redirect("solicitar_recuperacion")

    if request.method == "POST":
        codigo = request.POST.get("codigo")
        intentos = request.session.get("intentos_recuperacion", 0)

        try:
            usuario = User.objects.get(email=email)
            if usuario.token == codigo:
                request.session['verificado_token_password'] = True
                messages.success(request, "Código verificado. Ahora puedes establecer una nueva contraseña.")
                return redirect("establecer_nueva_password")
            else:
                intentos += 1
                request.session['intentos_recuperacion'] = intentos
                if intentos >= 3:
                    messages.error(request, "Demasiados intentos. Solicita un nuevo código.")
                    return redirect("solicitar_recuperacion")
                messages.warning(request, f"Código incorrecto. Intentos: {intentos}/3")
        except User.DoesNotExist:
            messages.error(request, "Usuario no encontrado.")
            return redirect("solicitar_recuperacion")

    return render(request, "verificar_token_clave.html")

def establecer_nueva_password(request):
    email = request.session.get("correo_recuperacion")
    verificado = request.session.get("verificado_token_password", False)

    if not (email and verificado):
        messages.error(request, "Acceso no autorizado.")
        return redirect("solicitar_recuperacion")

    if request.method == "POST":
        nueva_pass = request.POST.get("password")
        confirmar = request.POST.get("confirmar")

        if not nueva_pass:
            messages.error(request, "Debes ingresar una nueva contraseña")
        if not confirmar:
            messages.error(request,"Debes ingresar Confirmar Contraseña")    
        elif nueva_pass != confirmar:
            messages.error(request, "Las contraseñas no coinciden.")
        elif len(nueva_pass) < 6:
            messages.warning(request, "La contraseña debe tener al menos 6 caracteres.")
        else:
            usuario = User.objects.get(email=email)
            usuario.password = hash_password(nueva_pass)
            usuario.token = None
            usuario.save()

            # Limpiar sesiones
            request.session.pop("correo_recuperacion", None)
            request.session.pop("verificado_token_password", None)
            request.session.pop("intentos_recuperacion", None)

            messages.success(request, "Contraseña actualizada correctamente.")
            return redirect("login")

    return render(request, "nueva_clave.html")
