#from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import *

from django.db.utils import IntegrityError
from django.contrib import messages

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
            # Crear variable de sesión ========
            request.session["auth"] = {
                "id": q.id,
                "nombre": q.nombre,
                "rol": q.rol,
            }
            verificar = request.session.get("auth", False)
            if verificar :
                if verificar["rol"] == 1:
                    return redirect("admin_dashboard")
                else:
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



def contactanos(request):
    return render(request, 'contactanos.html')

def facturas(request): 
    return render  (request, "facturas.html") 

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
        return render(request, "index.html")
    
    else:
        messages.info(request, "Debe loguearse primero...")
        return redirect("login")

    

def CudUsuarios(request):
    return render(request, "admin/adminCRUDU.html")

def crud_categorias(request): 
    return render  (request, "admin/admin-CRUD-categorias.html")  

def crud_productos(request):
    return render (request,"admin/admin-CRUD-productos.html" )
# def index2(request):
#     return render(request, 'index2.html')

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
