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
    path("adminCRUDU/", views.CrudUsuarios, name="adminCRUDU"),
    path("admin-CRUD-productos/",views.crud_productos, name="crud_productos"),
    path("facturas/", views.facturas, name="facturas"),
    path("register/", views.crear_usuario, name="register" ),
    path("logout/", views.logout, name="logout"),
    path("editar-perfil/", views.editar_perfil, name="editar-perfil"),
    path("eliminar-categoria/<int:id_categoria>/", views.eliminar_categoria, name="eliminar-categoria"),


    path("editar_usuario/<int:usuario_id>/", views.editar_usuario, name="editar_usuario"),
    path('eliminar_usuario/<int:id_usuario>/', views.eliminar_usuario, name='eliminar_usuario'),

    path("editar_categoria/<int:categoria_id>/", views.editar_categoria, name="editar_categoria"),
    
# Crud de productos
    
    path('eliminar-producto/<int:id_producto>/', views.eliminar_producto, name='eliminar_producto'),
    path("editar_producto/<int:producto_id>/", views.editar_producto, name="editar_producto"),

# CRUD de usuarios
    path("crear_usuario/", views.crear_usuario, name="usuario_nuevo"),
    path("cambiar_clave/", views.cambiar_clave, name="cambiar_clave"),
    path("agregar_categoria/", views.agregar_categoria, name="agregar_categoria")
]