Parte 1: *Registro de consultas*

prompt: esta hecho el models y el backend de los productos, necesito que agregues y conectes desde la sesion del admin un boton de edicion que permita cambiar
la url de la foto, el nombre, el stock, la categoria, etc... debe ser que cuando presionas el boton de editar te lleve a una vista con formulario
de edicion, tambien, agrega al html de la vista principal de administrador un formulario de agregar productos

resumen respuesta: agrego y creo el nuevo html con el formulario para editar productos

prompt: cree un models de usuario y su backend con django, necesito que me ayudes a hacer mas robusto el login de la pagina, quiero que el login ya no sea solo poner tu nombre si no que revise tu user y contraseña de los usuarios en la base de datos al logear, tambien que te lleve a la ventana de admin o user segun tu rol.

resumen respuesta:  realizó los cambios del login

prompt: ok, perfecto, ahora en la vista de admin, arriba en la navbar, cambia "administración" por "resumen" y que sea una nueva vista donde puedas ver datos como : la cantidad de articulos, el costo promedio, el stock por categoria y que estos calculos se realicen usando aggregate o annotate del orm de django, si algun calculo no se puede hacer con el orm, dimelo y vemos que hacer

resumen respuesta: creo  resumen_admin.py en views.py donde calcula los calculos pedidos y los pide con un request

prompt: cree un model llamado ConsultaCliente para que los clientes puedan consultar sobre productos, cree forms.py para crear el formulario por django y agregue alfinal en views.py una funcion con un metodo POST para enviar el formulario y que haga render de contacto.html

necesito que crees el archivo contacto html y sea una vista para el cliente y que tenga el formulario para ser enviado, que se pueda elegir producto opcionalmente y pida los datos que pide el formulario ya creado

resumen respuesta: creo contacto.html registro la ruta y creo en views.py crear consulta y lo unio a contacto.html

prompt: por ultimo, en la vista de admin, necesito que en la navbar agregues "solicitudes" y que sea una vista donde se pueden ver las consultas que han enviados los clientes

resumen respuesta: creo en views.py solicitudes_admin que consulta las entradas de el model consultaCliente
--------------------------------------fin parte 1-------------------------------------------

parte 2, *explicación del proceso*:

en esta tercera evaluacion tenia una base mucho mas solida de proyecto creada mas estable, y ya sabia manejarme con models, crear rutas con urls y hacer los metodos post get, etc... asique de esa forma realice lo relacionado a enviar y recibir datos desde la base de datos, para realizar el resto de la evaluación use la ia antigravity, que fue creando los htmls segun lo iba pidiendo y agregando algunas funcionalidades en views.py, al saber python y ya estar mas familiarizado con el backend, fue muy facil entender lo que estaba pasando en views.py para manejar los renders y las requests. 
En cuanto al html y css, esta 100% hecho con ia y no creo que entienda todo lo que esta hecho. 