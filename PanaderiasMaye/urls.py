#Urls de la app spa
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("categorias/", views.categorias, name="categorias"),
    path("contactanos/", views.contactanos, name="contactanos"),
    path("about/", views.about, name="about"),
    path("carrito/", views.carrito, name="carrito"),
    path("login/", views.login, name="login"),
    path("recuperar_clave/", views.clave, name="recuperar_clave"),
    path("admin-CRUD-categorias/",views.crud_categorias, name="crud_categoria"),
    path("admin-dashboard/", views.dashboardAdmin, name="admin_dashboard"),
    path("adminCRUDU/", views.CudUsuarios, name="adminCRUDU"),
    path("admin-CRUD-productos/",views.crud_productos, name="crud_productos"),
    path("facturas/", views.facturas, name="facturas"),
    path("register/", views.crear_usuario, name="register" )
]