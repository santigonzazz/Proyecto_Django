#Urls de la app spa
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("contactanos/", views.contactanos, name="contactanos"),
    path("about/", views.about, name="about"),
    path("login/", views.login, name="login"),
    path("recuperar_clave/", views.clave, name="recuperar_clave"),
    path("adminCRUDCategorias/",views.crud_categorias, name="crud_categoria"),
    path("admin-dashboard/", views.dashboardAdmin, name="admin_dashboard"),
    path("adminCRUDU/", views.CrudUsuarios, name="adminCRUDU"),
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

    path("editar_producto/<int:producto_id>/", views.editar_producto, name="editar_producto"),
    path('eliminar-producto/<int:id_producto>/', views.eliminar_producto, name='eliminar_producto'),
    path('agregar-producto/', views.agregar_producto, name='agregar_producto'),
    
    path("editar_categoria/<int:categoria_id>/", views.editar_categoria, name="editar_categoria"),
    path('eliminar_usuario/<int:id_usuario>/', views.eliminar_usuario, name='eliminar_usuario'),
    path("editar_usuario/<int:usuario_id>/", views.editar_usuario, name="editar_usuario"),
    path("eliminar_categoria/<int:id_categoria>/", views.eliminar_categoria, name="eliminar_categoria" ),

    #carrito
    path("carrito/<int:producto_id>/", views.agregar_carrito, name="agregar_carrito"),
    path("", views.ver_carrito, name="ver_carrito" ),
    path('eliminar_carrito/<int:producto_id>/', views.eliminar_producto_carrito, name='eliminar_producto_carrito'),
    path("carrito/", views.ver_carrito_completo, name="ver_carrito_completo"),
    path('carrito/actualizar/<int:producto_id>/', views.actualizar_cantidad, name='actualizar_cantidad'),

    #pagos

    path("formulario-pago/", views.formulario_pago, name='formulario_pago'),
    path("procesar-pedido/", views.procesar_pedido, name='procesar_pedido'),
    path("confirmar-pago/", views.confirmar_pago, name='confirmar_pago' )
]