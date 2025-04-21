from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator, MinValueValidator
from django.utils import timezone
# Create your models here.
class User(models.Model):
    foto = models.ImageField(upload_to="usuarios", default="usuarios/default.jpg")
    nombre= models.CharField(max_length= 100,  validators=[MinLengthValidator(2)])
    apellido= models.CharField(max_length= 100, validators=[MinLengthValidator(2)])
    celular= models.CharField(max_length=10)
    email= models.EmailField(max_length= 254, unique=True)
    password=  models.CharField(max_length= 100)
    direccion=  models.CharField(max_length= 120, blank=True, null=True)
    ROLES=(
        (1, 'Empleados'),
        (2, 'Clientes'),
    )
    rol= models.IntegerField(choices= ROLES, default=2)
    token = models.CharField(max_length=100, blank=True, null=True)
    verificado = models.BooleanField(default=False)
    def __str__(self):
        return f'{self.nombre} {self.apellido}'


class Proveedor(models.Model):
    nombre = models.CharField(max_length=100) 
    telefono = models.CharField(max_length=10)
    correo = models.EmailField(max_length=254)
    password = models.CharField(max_length=254)
    catalogoProductos = models.CharField(max_length=100)
    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

class Metodo_pago(models.Model):
    nombre = models.CharField(max_length=120)
    DISPONIBILIDAD = (
        ("SI", "Disponible"),
        ("NO", "No Disponible")
    )
    disponibilidad = models.CharField(max_length=2, choices=DISPONIBILIDAD, default="SI")

    class Meta:
        verbose_name = "Metodo Pago"
        verbose_name_plural = "Metodos de pago"

    def __str__(self):
        return f"{self.nombre}, {self.disponibilidad}"


class Categoria(models.Model):
       nombre= models.CharField(max_length=100)
       descripcion= models.TextField(null=True,blank=True)
       ESTADOS=(
             (1, "Activo"),
             (2, "Inactivo"),
       )

       def __str__(self):
           return f"{self.nombre}"
    

class Producto(models.Model):
    foto = models.ImageField(upload_to="productos" ,default="productos/pan9.jpeg")    
    nombre = models.CharField(max_length=120)
    descripcion = models.CharField(max_length=120)
    cantidad = models.IntegerField(default=100)
    precio  = models.FloatField(validators=[MinValueValidator(0.01)])
    DISPONIBILIDAD = (
        ("SI", "Disponible"),
        ("NO", "No Disponible")
    )
    disponibilidad = models.CharField(max_length=2, choices=DISPONIBILIDAD, default="SI")
    

    def __str__(self):
        return f"{self.nombre}, {self.precio} {self.disponibilidad}"
    
class ProductoCategoria(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.DO_NOTHING, related_name='fk2_producto_categoria')  
    categoria = models.ForeignKey(Categoria, on_delete=models.DO_NOTHING, related_name='fk3_producto_categoria')  

    def __str__(self):
        return f"{self.producto.nombre} - {self.categoria.nombre}"
   

class Detalle_carrito(models.Model):
    carrito = models.ForeignKey('Carrito', on_delete=models.CASCADE, related_name='detalles', null=True)
    cantidad= models.IntegerField()
    total= models.FloatField(validators=[MinValueValidator(0)])
    producto= models.ForeignKey('Producto', on_delete=models.DO_NOTHING, related_name='fk4_detalle_carrito_producto')
    class Meta:
        verbose_name = "Detalle Carrito"
        verbose_name_plural = "Detalle Del Carrito"

    def __str__(self):
        return f"{self.producto} {self.cantidad} {self.total}  "

class Carrito(models.Model):
    
    SERVICIOS = (
        (1, "Domicilio"),
        (2, "Reserva")
    )
    ESTADOS = (
        (1, "Pendiente"),
        (2, "Pagado")
    )
    METODOS_PAGOS = (
        (1, "Nequi"),
        (2, "Bancolombia"),
        (3, "Tarjeta de Crédito"),
        (4, "Efectivo")
    )
    servicio= models.IntegerField(choices=SERVICIOS, default=1)
    usuario= models.ForeignKey('User', on_delete=models.DO_NOTHING, related_name='fk5_carrito_usuario')
    fecha = models.DateTimeField(default=timezone.now)
    cantidad= models.IntegerField()
    estado = models.IntegerField(choices=ESTADOS, default=1)
    metodo_pago = models.IntegerField(choices=METODOS_PAGOS, default=4)
    nombre_destinatario = models.CharField(max_length=150, null=True)
    fecha_reserva = models.DateTimeField(null=True)

    def __str__(self):
        return f"{self.usuario} {self.cantidad}"
    
    class Meta:
        get_latest_by = 'fecha'


class Inventario(models.Model):
    fecha = models.DateTimeField()
    stock = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    producto= models.ForeignKey('Producto', on_delete=models.DO_NOTHING, related_name='fk7_detalle_carrito_producto')
    proveedor = models.ForeignKey("Proveedor", on_delete=models.DO_NOTHING, related_name='fk8_entrada_proveedor')

    def __str__(self):
        return f"{self.producto} {self.proveedor} {self.stock} {self.fecha}"
    
class Catalogo_inventario(models.Model):
    nombre= models.CharField(max_length=120)
    precio= models.FloatField(validators=[MinValueValidator(0)])
    marca= models.CharField(max_length=50)
    class Meta:
        verbose_name = "Catalogo inventario"
        verbose_name_plural = "Catalogo inventarios"

    def __str__(self):
        return f"{self.nombre} {self.precio} {self.marca}"
