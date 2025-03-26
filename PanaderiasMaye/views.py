from django.http import HttpResponse
from django.shortcuts import render
from .models import *

# Create your views here.

def index(request):
    prducto = Producto.objects.all()
    cat = Categoria.objects.all()
    contexto = {
        "productoInfo": prducto,
        "categoria": cat,
    }
    return render(request, 'index.html', contexto)

def login(request):

    prducto = Producto.objects.all()
    contexto = {
        "productoInfo": prducto
    }
    
    if request.method == 'POST':
        username = request.POST.get("email")
        password = request.POST.get("password")
      
        try:
            user = User.objects.get(email=username)
            clave = User.objects.get(password=password)
            return render(request, 'index.html', contexto)
        except User.DoesNotExist:
            return render(request, 'login.html')
    else:
        return render(request, 'login.html')
        

     


        

       

def categorias(request):
    categoria = Categoria.objects.all()
    producto = Producto.objects.all()
    contexto = {
        "categoria": categoria,
        "productoCategoria": producto
    }

    return render(request, 'categorias.html', contexto)


def contactanos(request):
    return render(request, 'contactanos.html')

def facturas(request): 
    return render  (request, "facturas.html") 

def about(request):
    return render(request, 'about.html')

def carrito(request):
    return render(request, 'carrito.html')


def register(request):
    return render(request, 'register.html')

def clave (request):
    return render(request, 'recuperarclave.html')

def dashboardAdmin(request):
    return render(request, "admin/admin-DashBoard.html")

def CudUsuarios(request):
    return render(request, "admin/adminCRUDU.html")

def crud_categorias(request): 
    return render  (request, "admin/admin-CRUD-categorias.html")  

def crud_productos(request):
    return render (request,"admin/admin-CRUD-productos.html" )
# def index2(request):
#     return render(request, 'index2.html')
