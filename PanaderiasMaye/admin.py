from django.contrib import admin
from.models import*
from django.utils.html import mark_safe

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id",'foto', 'ver_foto', 'nombre', 'apellido', 'email', 'rol', "password")
    search_fields = ('nombre', 'apellido', 'email')
    list_filter = ('rol',)
    list_editable=('rol',)

    def ver_foto(self, obj):
        return mark_safe(f'<img src="{obj.foto.url}" width="40">')

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre", "telefono", "correo", "catalogoProductos"]
    search_fields = ["nombre", "correo", "telefono", "catalogoProductos"]
    list_filter = ["catalogoProductos"]


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre", "descripcion", "cantidad", "precio", "disponibilidad"]
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

class DetalleCarritoInline(admin.TabularInline):  
    model = Detalle_carrito
    extra = 0  # No agregar filas vacías por defecto
    readonly_fields = ('producto', 'cantidad', 'total')

@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ["id", "servicio", "usuario", "nombre_destinatario", "fecha_reserva", "estado", "metodo_pago", "direccion", "especificaciones_direccion"]
    search_fields = ["servicio", "usuario"]
    list_filter = ["usuario"]
    list_editable = ["estado"]
    inlines =[DetalleCarritoInline]

    def mostrar_productos(self, obj):
        detalles = obj.detalles.all()
        return ",".join([f"{detalle.producto} ({detalle.cantidad} X {detalle.total}) " for detalle in detalles ])
    
    mostrar_productos.short_description = "Productos... "


@admin.register(Detalle_carrito)
class DetalleCarritoAdmin(admin.ModelAdmin):
    list_display = ["id", "cantidad", "total", "producto", "carrito", "id_carrito"]
    search_fields = ["producto__nombre"]
    list_filter = ["producto"]
    list_editable = ["cantidad", "total"]

    def id_carrito(self, obj):
        return f"{obj.carrito.id}"


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

@admin.register(ProductoCategoria)
class AdminProductoCategoria(admin.ModelAdmin):
    list_display = ["id", "producto", "categoria"]

@admin.register(Pqrs)
class AdminPqrs(admin.ModelAdmin):
    list_display = ["id", "nombre", "correo", "tipo"]
    search_fields = ["nombre", "correo", "tipo"]
    list_filter = ["tipo"]
    

# Register your models here.