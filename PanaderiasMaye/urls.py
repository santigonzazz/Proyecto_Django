#Urls de la app spa
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("contactanos/", views.contactanos, name="contactanos"),
    path("about/", views.about, name="about"),
    path("login/", views.login, name="login"),
    path("recuperar_clave/", views.clave, name="recuperar_clave"),
    path("admin-CRUD-categorias/",views.crud_categorias, name="crud_categoria"),
    path("admin-dashboard/", views.dashboardAdmin, name="admin_dashboard"),
    path("adminCRUDU/", views.CudUsuarios, name="adminCRUDU"),
    path("admin-CRUD-productos/",views.crud_productos, name="crud_productos"),
    path("facturas/", views.facturas, name="facturas"),
    path("register/", views.crear_usuario, name="register" ),
    path("logout/", views.logout, name="logout"),
    path("editar-perfil/", views.editar_perfil, name="editar-perfil"),
    path("eliminar-categoria/<int:id_categoria>/", views.eliminar_categoria, name="eliminar-categoria"),
    path("correo1/", views.correos1, name="correo"),
    path("correo2/", views.correos2, name="correo2"),
    path("cambiar_clave/", views.cambiar_clave, name="cambiar_clave"),
    path("agregar_categoria/", views.agregar_categoria, name="agregar_categoria"),  
]