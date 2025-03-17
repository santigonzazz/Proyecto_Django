from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator, MinValueValidator

# Create your models here.
class User(models.Model):
    nombre= models.CharField(max_length= 100,  validators=[MinLengthValidator(2)])
    apellido= models.CharField(max_length= 100, validators=[MinLengthValidator(2)])
    celular= models.CharField(max_length=10)
    email= models.EmailField(max_length= 254)
    password=  models.CharField(max_length= 100)
    direccion=  models.CharField(max_length= 120)
    ROLES=(
        (1, 'Empleados'),
        (2, 'Clientes'),
    )
    rol= models.IntegerField(choices= ROLES, default=2)
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
             ("Postres"),
             ("Helados"),
             ("Sin Gluten"),
             ("Bolleria"),
             ("Bebidas")
       )

       def __str__(self):
           return f"{self.nombre}"
    

class Producto(models.Model):
    foto = models.FileField()
    nombre = models.CharField(max_length=120)
    descripcion = models.CharField(max_length=120)
    precio  = models.FloatField(validators=[MinValueValidator(0.01)])
    categoria= models.ForeignKey('Categoria', on_delete=models.DO_NOTHING, related_name='fk1_producto_categoria')
    DISPONIBILIDAD = (
        ("SI", "Disponible"),
        ("NO", "No Disponible")
    )
    disponibilidad = models.CharField(max_length=2, choices=DISPONIBILIDAD, default="SI")

    def __str__(self):
        return f"{self.nombre}, {self.precio} {self.categoria} {self.disponibilidad}"
   

class Detalle_carrito(models.Model):
    cantidad= models.IntegerField()
    total= models.FloatField(validators=[MinValueValidator(0)])
    servicio=models.CharField(max_length=150)
    producto= models.ForeignKey('Producto', on_delete=models.DO_NOTHING, related_name='fk2_detalle_carrito_producto')

    class Meta:
        verbose_name = "Detalle Carrito"
        verbose_name_plural = "Detalle Del Carrito"

    def __str__(self):
        return f"{self.producto} {self.cantidad} {self.total} {self.servicio} "

class Carrito(models.Model):
    cantidad= models.IntegerField()
    total= models.FloatField(validators=[MinValueValidator(0)])
    servicio=models.CharField(max_length=150)
    usuario= models.ForeignKey('User', on_delete=models.DO_NOTHING, related_name='fk3_carrito_usuario')
    Detalle_carrito=models.ForeignKey('Detalle_carrito', on_delete=models.DO_NOTHING, related_name='fk4_carrito_detalleCarrito')

    def __str__(self):
        return f"{self.usuario} {self.Detalle_carrito} {self.cantidad} {self.total}"


class Inventario(models.Model):
    fecha = models.DateTimeField()
    stock = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    producto= models.ForeignKey('Producto', on_delete=models.DO_NOTHING, related_name='fk5_detalle_carrito_producto')
    proveedor = models.ForeignKey("Proveedor", on_delete=models.DO_NOTHING, related_name='fk6_entrada_proveedor')

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


