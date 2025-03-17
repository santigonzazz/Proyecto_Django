from django.contrib import admin
from.models import*

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'email', 'rol')
    search_fields = ('nombre', 'apellido', 'email')
    list_filter = ('rol',)
    list_editable=('rol',)

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre", "telefono", "correo", "catalogoProductos"]
    search_fields = ["nombre", "correo", "telefono", "catalogoProductos"]
    list_filter = ["catalogoProductos"]


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre", "descripcion", "precio", "disponibilidad"]
    search_fields = ["nombre", "disponibilidad"]
    list_filter = ["disponibilidad"]
    list_editable = ["disponibilidad"]


@admin.register(Metodo_pago)
class MetodoPagoAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre", "disponibilidad"]
    search_fields = ["nombre", "disponibilidad"]
    list_filter = ["disponibilidad"]
    list_editable = ["disponibilidad"]

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre", "descripcion"]
    search_fields = ["id", "fecha"]

@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ["id", "cantidad", "total", "servicio", "usuario"]
    search_fields = ["servicio", "usuario"]
    list_filter = ["usuario"]

@admin.register(Detalle_carrito)
class DetalleCarritoAdmin(admin.ModelAdmin):
    list_display = ["id", "cantidad", "total", "producto"]
    search_fields = ["producto"]
    list_filter = ["producto"]
    list_editable = ["cantidad", "total"]


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ["id", "fecha", "stock", "proveedor"]
    search_fields = ["proveedor"]
    list_filter = ["proveedor"]
    list_editable = ["fecha", "stock"]
    
@admin.register(Catalogo_inventario)
class Catalogo_inventarioAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre", "precio", "marca"]
    search_fields =["nombre", "marca"]
    list_filter = ["nombre", "marca"]
    list_editable = ["nombre", "precio"]

# Register your models here.
