#Urls de la app spa
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("contactanos/", views.contactanos, name="contactanos"),
    path("about/", views.about, name="about"),
    path("login/", views.login, name="login"),
    #path("recuperar_clave/", views.clave, name="recuperar_clave"),
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
    #path("cambiar_clave/", views.cambiar_clave, name="cambiar_clave"),
    path("agregar_categoria/", views.agregar_categoria, name="agregar_categoria"),  

    path("editar_producto/<int:producto_id>/", views.editar_producto, name="editar_producto"),
    path('eliminar-producto/<int:id_producto>/', views.eliminar_producto, name='eliminar_producto'),
    path('agregar-producto/', views.agregar_producto, name='agregar_producto'),

    
    path("eliminar_categoria/<int:id_categoria>/", views.eliminar_categoria, name="eliminar_categoria" ),
    path("editar_categoria/<int:categoria_id>/", views.editar_categoria, name="editar_categoria"),
    
    # usuarios desde admin
    path('eliminar_usuario_admin/<int:id_usuario>/', views.eliminar_usuario_admin, name='eliminar_usuario_admin'),
    path('crear_usuario_admin/', views.crear_usuario_admin, name='crear_usuario_admin'),
    path('editar_usuario_admin/<int:id_usuario>/', views.editar_usuario_admin, name='editar_usuario_admin'),

    #carrito
    path("carrito/<int:producto_id>/", views.agregar_carrito, name="agregar_carrito"),
    path('carrito/', views.ver_carrito_completo, name='ver_carrito_completo'),
    path('carrito/actualizar/<int:producto_id>/', views.actualizar_cantidad, name='actualizar_cantidad'),
    path('carrito/eliminar/<int:producto_id>/', views.eliminar_producto_carrito, name='eliminar_producto_carrito'),
    path('carrito/vaciar/', views.vaciar_carrito, name='vaciar_carrito'),

    #reservas
    path("formulario-reserva/", views.formulario_pago_reserva, name='reservar'),
    path("mis_reservas", views.reservas_pendientes, name='reservas_pendientes'),
    #path("procesar-pedido-reserva/", views.procesar_pedido_reserva, name='procesar_pedido_reserva'),
    
    #pagos
    path("formulario-pago/", views.formulario_pago, name='formulario_pago'),
    path("procesar-pedido/", views.procesar_pedido, name='procesar_pedido'),

    #Facturas
    path('mis-facturas/', views.facturas_usuario, name='facturas_usuario'),
    path('factura/<int:factura_id>/exportar/', views.exportar_factura_pdf, name='exportar_factura_pdf'),

    #Correos
    path('confirmar-pago/<int:carrito_id>/', views.confirmar_pago, name='confirmar_pago'),
    path('privacidad/', views.politica_privacidad, name='politica_privacidad'),

    #path("cambiar_clave/", views.cambiar_clave, name="cambiar_clave"),

    # Tokens:

    path("verificar-codigo/", views.verificar_codigo, name="verificar_codigo" ),
    path("reenviar-token/", views.reenviar_token, name="reenviar_token" ),
    
    #Recuperar clave
    path("recuperar/", views.solicitar_recuperacion, name="solicitar_recuperacion"),
    path("verificar-codigo-recuperacion/", views.verificar_token_recuperacion, name="verificar_token_recuperacion"),
    path("nueva-password/", views.establecer_nueva_password, name="establecer_nueva_password"),
]