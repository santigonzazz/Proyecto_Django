from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import *

from django.db.utils import IntegrityError
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .utils import *
# Create your views here.

def index(request):
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
        return redirect("index")
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
    fac = Carrito.objects.filter()
    contexto = {
        "facturas": fac
    }
    return render(request, "admin/admin-facturas.html", contexto) 

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

    

def CudUsuarios(request):
    if request.method == 'POST':
        nombre = request.POST.get("nombre")
        apellido = request.POST.get("apellido")
        rol = request.POST.get("rol")
        celular = request.POST.get("celular")
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirmar_password = request.POST.get('confirmar_password')
                # Asegúrate de que este campo esté en tu formulario

        if password == confirmar_password:
            try:
                # Crear el usuario usando tu modelo personalizado
                nuevo_usuario = User(
                    nombre=nombre,
                    apellido=apellido,
                    celular=celular,
                    email=email,
                    password=password,  # Recuerda que deberías encriptar la contraseña
                    rol=rol  # Asignar un rol por defecto, si es necesario
                )
                nuevo_usuario.save()  # Guardar el usuario en la base de datos
                messages.success(request, "Usuario creado correctamente!")
                return redirect("admin_dashboard")  # Cambia 'index' por la vista a la que quieras redirigir
            except Exception as e:
                messages.error(request, f"Error: {e}")
                return redirect("admin_dashboard")
        else:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect("admin_dashboard")
    else:
        return render(request, "admin/adminCRUDU.html")

def crud_categorias(request): 
    cate = Categoria.objects.all()
    contexto = {
        "categorias": cate
    }
    return render  (request, "admin/admin-CRUD-categorias.html", contexto)  

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
    p = Producto.objects.all()
    contexto = {
        "productos": p
    }
    return render (request,"admin/admin-CRUD-productos.html", contexto) 



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
                return redirect("index")  # Cambia 'index' por la vista a la que quieras redirigir
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

        logueado = request.session.get("auth", False)

        q = User.objects.get(pk=logueado["id"])


        try:
            q.nombre = request.POST.get("nombre")
            q.apellido = request.POST.get("apellido")
            q.celular = request.POST.get("celular")
            q.email = request.POST.get("email")
            q.rol = request.POST.get("rol")
            q.save()
            messages.success(request, "Datos actualizados correctamente")
            return redirect("index")
        except Exception as e:
            messages.error(request, f"Error {e} ")
            return redirect("editar-perfil")
    else:
        return render(request,"usuarios/user-Crud.html" )


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

    return redirect(request, "admin/admin-CRUD-categorias.html")