import json
from flask import Flask,redirect,render_template,request,session,flash
from flaskext.mysql import MySQL
from datetime import datetime
import os #Nos permite acceder a los archivos
from flask import send_from_directory #Acceso a las carpetas
import cryptocode
os.system("c:/xampp/xampp_start.exe")


cantidad_mesas=0

app=Flask(__name__)

app.secret_key="123Prueba!"
mysql = MySQL()
app.config['MYSQL_DATABASE_HOST']='localhost' # Configuración de host DB
app.config['MYSQL_DATABASE_USER']='root' # Configuración de usuario DB
app.config['MYSQL_DATABASE_PASSWORD']='' # Contraseña DB


mysql.init_app(app) # Inicialización de SQL
CARPETA= os.path.join('fotos') # Referencia a la carpeta
app.config['CARPETA']=CARPETA # Indicamos que vamos a guardar esta ruta de la carpeta

#CREACION DE BASE DE DATOS Y TABLAS
conn = mysql.connect() #Creamos la conexión
cursor = conn.cursor() # Establecemos la conexión
cursor.execute("CREATE DATABASE IF NOT EXISTS `my_resto`;") # Creamos la base de datos

cursor.execute("CREATE TABLE IF NOT EXISTS `my_resto`.`platos` ( `id_plato` INT(10) NOT NULL AUTO_INCREMENT , `nombre` VARCHAR(255) NOT NULL , `descripcion_plato` VARCHAR(5000) NOT NULL , `precio` FLOAT NOT NULL , `foto` VARCHAR(5000) NOT NULL , PRIMARY KEY (`id_plato`) );") # Creamos la tabla platos(platos ofrecidos con nombre, descripcion precio y foto)

cursor.execute("CREATE TABLE IF NOT EXISTS `my_resto`.`mesas` ( `id_mesa` INT(10) NOT NULL AUTO_INCREMENT , `pedidos` JSON DEFAULT '{ }', `hora_abre` DATETIME , PRIMARY KEY (`id_mesa`));") # Creamos la tabla mesas (mesas del restaurant con numero de mesa,hora y fecha en que se inicia la mesa(se toma el primer pedido)y pedidos(donde se van a ir cargando los pedidos que realicen los clientes))

cursor.execute("CREATE TABLE IF NOT EXISTS `my_resto`.`usuarios`( `usuario` VARCHAR(255) NOT NULL , `password` VARCHAR(500) NOT NULL, `super_usuario` BOOLEAN NULL DEFAULT FALSE, PRIMARY KEY (`usuario`))") # Creamos la tabla usuarios(usuarios registrados con password y opcion de super usuario)

cursor.execute("CREATE TABLE IF NOT EXISTS `my_resto`.`ventas`(`id_venta` INT(20) NOT NULL AUTO_INCREMENT ,`mesa`INT(10), `hora_abre` DATETIME , `hora_cierra` DATETIME, `consumo` JSON DEFAULT '{ }', `total` INT(10), PRIMARY KEY (`id_venta`));")# Creamos la tabla ventas(registro de las ventas de todo el comercio, con numero de mesa, hora de inicio y cierre de atencion, lista de pedidos, y total facturado)

cursor.execute("SELECT count(*) FROM `my_resto`.`usuarios`") # Obtenemos la cantidad de usuarios registrados
cantidadDeUsuarios=cursor.fetchone()[0] # Asignamos lo obtenido en una variable

if cantidadDeUsuarios==0: # Si no hay ningun usuario registrado
    clave=cryptocode.encrypt("admin",app.secret_key) # Encriptamos el password para guardarlo en DB
    cursor.execute("INSERT `my_resto`.`usuarios`(`usuario`,`password`,`super_usuario`) VALUES ('admin', %s, 1);",(clave)) # Creamos un super usuario admin : admin para poder iniciar la aplicacion(luego se podra editar)
conn.commit() # Cerramos conexión con DB


# Renderizacion de pagina de ingreso(LOGIN)
@app.route('/')
def login():
   return render_template("/index.html")

# Procesado del login
@app.route('/ingresar', methods=['POST']) # Recibimos los datos del formulario correspondiente
def ingresar():
    # Obtenemos desde el form los datos correspondientes
    nombre=request.form["txtUsuario"]
    password=request.form["txtPassword"]
    sql="SELECT * FROM `my_resto`.`usuarios` WHERE `usuario` LIKE %s" # Definimos la busqueda los datos del usuario según el nombre de usuario
    conn = mysql.connect() #Creamos la conexión
    cursor = conn.cursor() # Establecemos la conexión
    cursor.execute(sql,nombre) # Ejecutamos la busqueda
    global usuario # Declaramos que la siguiente asignación de la variable usuario es a nivel global
    usuario=cursor.fetchall() # Asignamos el resultado de la busqueda en la DB
    conn.commit() # Cerramos conexión
    if usuario!=(): # Si se encontró el nombre de usuario en la DB
        clave2=cryptocode.decrypt(usuario[0][1],app.secret_key) # Desencriptamos lel password obtenido de la DB
        if password==clave2: # Si el password ingresado coincide con el correspondiente en la DB
            session["username"]=usuario[0][0] # Creamos la cookie para validar que es un usuario registrado
            if usuario[0][2]: # Si el usuario es super usuario
                session["super"]=usuario[0][2] # Creamos la cookie para validar que es un super usuario
            return redirect("/mesas")
        else: # Si los datos ingresados no se corresponden con el de un usuario registrado
            flash("Usuario o contraseña erroneos") # Escribimos un mensaje al usuario
            return redirect("/") # y lo enviamos a la pagina de login
    else: # Si no se encontró el nombre de usuario en la DB
        flash("Usuario o contraseña erroneos") # Escribimos un mensaje al usuario
        return redirect("/") # Lo enviamos a la pagina de login

# Renderizado de la pagina Mesas, listado de las mesas con acceso a cargar pedidos y cerrar mesa
@app.route('/mesas')
def mesas():
    if "username" in session: # Si es usuario registrado
        conn = mysql.connect() #Creamos la conexión
        cursor = conn.cursor() # Establecemos la conexión
        cursor.execute("SELECT `id_mesa`,`pedidos` FROM `my_resto`.`mesas`") # Traemos el numero de las mesas y los pedidos de las mismas
        mesas=cursor.fetchall() # Lo almacenamos en variable
        mesas=list(mesas) # Convertimos la tupla en lista para poder manejar los datos
        for indiceMesa in range(len(mesas)): # Para cada mesa dentro de la lista, tomamos el indice
            suma=0 # Establecemos la cuenta(monto a pagar or el cliente) en 0
            mesas[indiceMesa]=list(mesas[indiceMesa]) # Convertimos la tupla en lista para poder manejar los datos
            mesas[indiceMesa][1]=(str(mesas[indiceMesa][1])[1:-1]).split(",") # Limpiamos los datos para obtener los pedidos
            for indicePedido in range(len(mesas[indiceMesa][1])): # Para cada pedido dentro de la lista, tomamos el indice
                plato=mesas[indiceMesa][1][indicePedido].split(": ") # Separamos el nombre del plato y la cantidad
                cursor.execute("SELECT `precio` FROM `my_resto`.`platos` WHERE `nombre` LIKE %s;",(plato[0].strip()[1:-1])) # Obtenemos el precio individual del plato por su nombre
                precio=cursor.fetchall() # Lo almacenamos en variable
                if len(mesas[indiceMesa][1][indicePedido])>3: # Si ya hay pedidos cargados
                    mesas[indiceMesa][1][indicePedido]=(mesas[indiceMesa][1][indicePedido],precio[0][0]*int(plato[1])) # Agregamos el monto ( obtenido multiplicando la cantidad por el precio) a la lista para pasarla al HTML
                    suma+=precio[0][0]*int(plato[1]) # Calculamos el monto de los pedidos acumulados
                else: # Si no hay pedidos previos
                    mesas[indiceMesa][1][indicePedido]=["Sin pedidos",0] # Modificamos el item pedidos para mostrar algo en el HTML
            mesas[indiceMesa].append(suma) # Agregamos el monto total a la lista para mostrarlo en el HTML
        mesas=mesas[:cantidad_mesas] # Acotamos la cantidad de mesas a el numero indicado por el usuario
        return render_template("/mesas.html",mesas=mesas) # Renderizamos mesas.html y pasamos los datos a mostrar
    else: # Si los datos ingresados no se corresponden con el de un usuario registrado
        flash("Debe registrarse antes") # Escribimos un mensaje al usuario
        return redirect("/") # y lo enviamos a la pagina de login

#procesamiento de logout
@app.route('/logout')
def logout():
   session.pop("username", None)#Borramos la cookie
   session.pop("super", None)#Borramos la cookie
   return redirect("/") #Redireccionamos a la pagina de inicio,LOGIN


# Renderizado de la pagina platos(listado del menu disponible, con nombre, descripcion, precio y foto de cada plato(desde la cual se podran agregar o restar platos al pedido de la mesa pasada por parametro))
@app.route("/platos/<int:id_mesa>")
def platos(id_mesa):
    if "username" in session: # Si es usuario registrado
        sql=("SELECT `pedidos` FROM `my_resto`.`mesas` WHERE`id_mesa` LIKE %s ;") # Traemos la lista de pedidos de la mesa en cuestion
        conn = mysql.connect() #Creamos la conexión
        cursor = conn.cursor() # Establecemos la conexión
        cursor.execute(sql,id_mesa) # Ejecutamos la sentencia
        pedidos=cursor.fetchone() # Lo almacenamos en variable
        cursor.execute("SELECT * FROM `my_resto`.`platos`;") # Traemos la el menu
        platos=cursor.fetchall() # Lo almacenamos en variable
        conn.commit() # Cerramos conexion
        return render_template("platos.html",platos=platos, mesa=id_mesa) # Renderizamos platos.html pasando el menu y el numero de mesa
    else: # Si no es usuario registrado
        return redirect("/") #Redireccionamos a la pagina de inicio,LOGIN


"""Renderizado de administracion.HTML(Desde donde se podra: editar los datos de usuario, agrgar uno nuevo; editar, eliminar, o agregar un plato al menu; y configurar la cantidad de mesas)"""
@app.route("/administracion")
def administracion():
    if "username" in session: # Si es usuario registrado
        conn = mysql.connect() #Creamos la conexión# Se conecta a la conexión mysql.init_app(app)
        cursor = conn.cursor() # Establecemos la conexión 
        cursor.execute("SELECT * FROM `my_resto`.`platos`;") # Traemos el menu
        platos=cursor.fetchall() # Lo almacenamos en variable
        conn.commit() # Cerramos conexión
        return render_template("administracion.html",platos=platos,cantidad=cantidad_mesas) # Renderizamos administracion.html pasando el menu y la cantidad de mesas seleccionadas al momento
    else: # Si NO es usuario registrado
        return redirect('/') # Redireccionamos a inicio
"""Borrado de plato por ID"""
@app.route('/destroy/<int:id>') # Recibe como parámetro el id del producto
def destroy(id):
    if "username" in session: # Si es usuario registrado
        conn = mysql.connect() #Creamos la conexión
        cursor = conn.cursor() # Establecemos la conexión
        cursor.execute("SELECT foto FROM `my_resto`.`platos` WHERE id_plato=%s",id) # Buscamos el nombre de la foto
        fila= cursor.fetchall() # Almacenamos en variable
        os.remove(os.path.join(app.config['CARPETA'], fila[0][0])) # Elimina la foto de la carpeta
        cursor.execute("DELETE FROM `my_resto`.`platos` WHERE id_plato=%s", (id)) # Eliminamos el producto de la DB por su ID
        conn.commit() # Cerramos la conexión
        return redirect('/administracion') # Volvemos a la pagina de administración
    else: # Si NO es usuario registrado
        return redirect('/') # Redireccionamos a Inicio
"""Renerizado de edit.HTML(Formulario para editar el plato con el ID pasado por parametro)"""
@app.route('/edit/<int:id>') # Recibe como parámetro el id del plato
def edit(id):
    if "username" in session: # Si es usuario registrado
        conn = mysql.connect() #Creamos la conexión
        cursor = conn.cursor() # Establecemos la conexión
        cursor.execute("SELECT * FROM `my_resto`.`platos` WHERE id_plato=%s", (id)) # Buscamos el plato de la DB por su id
        plato=list(cursor.fetchone()) # Almacenamos en variable
        conn.commit() #Cerramos la conexión
        return render_template('edit.html',plato=plato) # Renderizar edit.html con la información obtenida
    else: # Si NO es usuario registrado
        return redirect('/') # Redireccionamos a Inicio

"""Realizar el ingreso en tabla de un nuevo plato, o las modificaciones de uno existente"""
@app.route("/update/", methods=['POST']) # Recibimos los datos desde el formulario de creacion
@app.route('/update/<int:id_plato>', methods=['POST']) # Recibimos los datos desde el formulario de edición, del producto a editar
def update(id_plato=None):
    if "username" in session: # Si es usuario registrado
        # Obtenemos los datos correspondientes desde el form y los almacenamos
        nombre=request.form['txtNombre'].capitalize().replace(" ","_")
        descripcion_plato=request.form['txtDescripcionPlato'].capitalize()
        precio=float(request.form['txtPrecio'])
        foto=request.files['txtFoto']
        now=datetime.now() # Obtenemos la fecha y hora para asignarla al nombre de la foto
        tiempo=now.strftime("%Y%H%M%S_") # Obtenemos de la fecha el año, la hora, los minutos y segundos
        extension=foto.filename.split(".") # Obtenemos la extensión del archivo de la foto
        if foto.filename !="": # Si el campo foto no esta vacío
            nuevoNombreFoto=tiempo+nombre+"."+extension[1] # Creamos el nombre de la foto
            foto.save("fotos/"+nuevoNombreFoto) # Guardamos la foto en la carpeta correspondiente
        else: # Si no se adjunto un archivo
            nuevoNombreFoto=request.form['viejoNombreFoto'] #
            if nuevoNombreFoto=="":
                nuevoNombreFoto="Sin foto" # Ingresamos texto a mostrar en lugar de la foto
        datos=[nombre,descripcion_plato,precio,nuevoNombreFoto] # Agrupamos los datos para la sentencia SQL
        if id_plato!=None: # Si se paso un ID de plato
            datos.append(id_plato) # Lo agregamos a los datos para la sentencia SQL
            sql="UPDATE `my_resto`.`platos` SET `nombre`=%s,`descripcion_plato`=%s, `precio`=%s, `foto`=%s WHERE id_plato=%s" # Creamos la sentencia para editar el plato en DB
        else: # Si se paso un ID de plato
            sql="INSERT `my_resto`.`platos` (`nombre`,`descripcion_plato`, `precio`, `foto`) VALUES(%s,%s,%s,%s)" # Creamos la sentencia para crear el plato en DB
        conn = mysql.connect() #Creamos la conexión
        cursor = conn.cursor() # Establecemos la conexión 
        cursor.execute(sql,datos) # Ejecutamos la sentencia, ya sea ara creacion o edicion del plato
        conn.commit() #Cerramos la conexión
        return redirect('/administracion')  # Volvemos a la pagina de administración de DB
    else: # Si NO es usuario registrado
        return redirect('/') # Redireccionamos a inicio

"""Guardado de las fotos en la carpeta correspondiente"""
@app.route('/fotos/<nombreFoto>') #Recibimos como parametro el nombre de la foto
def uploads(nombreFoto):
    return send_from_directory(app.config['CARPETA'], nombreFoto) # Guardamos la foto en la carpeta destinada a tal fin, con su nombre correspondiente

"""Creacion de nuevo usuario, para hacerlo, es necesario ser super usuario"""
@app.route('/crear_usuario', methods=['POST']) # Recibimos los datos del formulario
def crear_usuario():
    if "super" in session: # Si es un super usuario
        nuevoUsuario=request.form["txtUsuario"] # Nombre de nuevo usuario
        nuevoPassword=request.form['txtPassword'] # Password de nuevo usuario
        super=request.form.get("superUsuario") # Valor de super usuario
        nuevoPassword=cryptocode.encrypt(nuevoPassword,app.secret_key) # Encriptamos el password
        usuario1=nuevoUsuario,nuevoPassword,super #Agrupamos los datos
        sql="INSERT INTO `my_resto`.`usuarios` (`usuario`, `password`,`super_usuario`) VALUES (%s, %s,%s)" # Creamos la sentencia de creacion de nuevo usuario
        conn = mysql.connect() #Creamos la conexión
        cursor = conn.cursor() # Establecemos la conexión
        cursor.execute("SELECT `usuario` FROM `my_resto`.`usuarios` ;") # Buscamos los nombres de usuarios registrados
        usuarios1=cursor.fetchall()
        usuarios=[]
        # Creamos una lista de nombres de usuarios ya registrados a partir de una tupla de tuplas
        for usuarioj in usuarios1:
            usuarios.append(usuarioj[0])
        if nuevoUsuario not in usuarios: # Si el nuevo nombre de usuario no existe en la tabla(ya que debe ser único)
            cursor.execute(sql,usuario1) # Creamos el usuario
        else: # Si el nombre ya existe, solicitamos que use otro
            flash("Nombre de usuario no disponible")
        conn.commit() # Cerramos conexión
        return redirect('/administracion') # Retornamos a administracion
    else:
        flash("Usted no tiene los permisos para agregar un nuevo usuario")
        return redirect('/') #Redireccionamos a la pagina de login

"""Edicion datos usuario(propios)"""
@app.route("/modificar_usuario", methods=['POST']) # recibimos los datos del formulario correspondiente
def modificar_usuario():
    if "username" in session: # Si es un usuario registrado
        nuevoNombre=request.form["txtUsuario"] # Nuevo nombre de usuario
        nuevoPassword=request.form['txtPassword'] # Nuevo password de usuario
        nuevoPassword=cryptocode.encrypt(nuevoPassword,app.secret_key) # Encriptamos el password
        usuario1=(nuevoNombre,nuevoPassword,usuario[0][0]) # Agrupamos los datos, junto al nombre viejo del usuario
        sql="UPDATE `my_resto`.`usuarios` SET `usuario`= %s, `password`= %s WHERE `usuario`=%s;" # Armamos la sentencia para la actualización del usuario
        conn = mysql.connect() #Creamos la conexión
        cursor = conn.cursor() # Establecemos la conexión
        cursor.execute("SELECT `usuario` FROM `my_resto`.`usuarios` ;") # Buscamos todos los nombres de usuarios registrados
        usuarios=cursor.fetchall() # Almacenamos los datos en una tupla
        if nuevoNombre not in usuarios or nuevoNombre==usuario[0][0]: # Si el nuevo nombre de usuario no existe en la tabla, o si es igual al nombre viejo
            cursor.execute(sql,usuario1) # Hacemos la actualización del usuario
        else: # Si el nuevo nombre de usuario existe en la tabla, y no es igual al nombre viejo
            flash("Nombre de usuario no disponible") # Escribimos un mensaje al usuario
        conn.commit() # Cerramos la conexión
        return redirect('/administracion') # Retornamos a la pagina administracion


"""Cargar pedidos a una mesa"""
@app.route('/cargarPedido/<int:mesa>', methods=['POST'])
def cargarPedido(mesa):
    conn = mysql.connect() #Creamos la conexión
    cursor = conn.cursor() # Establecemos la conexión
    cursor.execute("SELECT `pedidos` FROM `my_resto`.`mesas` WHERE `id_mesa` LIKE %s ;",(mesa)) # Buscamos los pedidos previos de la mes
    pedidos=cursor.fetchall()[0][0] # Almacenamos en variable
    if bool(pedidos): # Si ya habia pedidos
        pedidos=json.loads(str(pedidos)) # Convertimos los pedidos en un diccionario
    else: # Si es el primer pedido
        hora=datetime.now() # Obtenemos la hora actual
        datos=[hora,mesa] # Agrupamos la hora y el Id de mesa par pasarlo a la sentencia SQL
        cursor.execute("UPDATE `my_resto`.`mesas` SET `hora_abre`=%s WHERE `id_mesa`=%s;",(datos)) # Cargamos la hora actual en la mesa en la DB
        pedidos={} # Creamos el diccionario para almacenar los pedidos
    keysDB=pedidos.keys() # Listamos los nombres de los platos de los pedidos existentes(lista vacia si no habia pedidos)
    datosForm=request.form # Traemos los nuevos pedidos y los almacenamos en un diccionario
    keysForm=datosForm.keys() # Listamos los nombres de los platos de los nuevos pedidos
    for keyForm in keysForm: # Recorremos el diccionario de pedidos pasados desde el form
        if int(datosForm[keyForm]) !=0: # Si el valor es distinto de 0(se agrego o quito algun plato)
            valor=int(datosForm[keyForm]) # Convertimos el valor en entero
            if keyForm in keysDB: # Si el pedido pasado por form es de un plato que ya se ha pedido previamente
                if (int(pedidos[keyForm])+valor)>0: # Si la suma entre pedido del form con el pedido previo es mayor que 0(para evitar platos con cantidad negativa)
                    pedidos[keyForm]=int(pedidos[keyForm])+valor # Sumamos el pedido previo con el nuevo
                else: # Si la cantidad resultante es 0 o menor 
                    pedidos.pop(keyForm) # Borramos el plato de la lista de pedidos
            elif valor>0: # Si el pedido es un plato nuevo y la cantidad es positiva
                pedidos.setdefault(keyForm,datosForm[keyForm]) # Agregamos el plato y cantidad al diccionario que se pasara a DB
        for key in pedidos: # Iteramos el diccionario
            pedidos[key]=int(pedidos[key]) # Nos aseguramos que los valores sean enteros
    sql="UPDATE `my_resto`.`mesas` SET `pedidos`=%s WHERE `id_mesa`=%s;" # Creamos la sentencia que actualiza la lista de pedidos de la mesa
    valores=(json.dumps(pedidos),mesa) # Agrupamos los datos(convirtiendo el diccionario en Json para su almacenamiento)
    cursor.execute(sql,valores) # Ejecutamos la sentencia
    conn.commit() # Cerramos la conexion
    return redirect("/mesas") # Redirecionamos a mesas

"""Establecimiento de la cantidad de mesas del negocio"""
@app.route('/cantidad_mesas/', methods=['POST'])
def cantidadMesas():
    global cantidad_mesas # Declaramos que la siguiente asignación de la variable cantidad_mesas es a nivel global
    cantidad_mesas=int(request.form['cantidad_mesas']) # Traemos la cantidad de mesas seleccionada por el usuario desde el form
    conn = mysql.connect() #Creamos la conexión
    cursor = conn.cursor() # Establecemos la conexión
    cursor.execute("SELECT count(*) FROM `my_resto`.`mesas`") # Contamos la cantidad de mesas existentes en la tabla de la DB
    mesas=int(cursor.fetchone()[0]) # Lo almacenamos como entero en una variable
    while mesas<cantidad_mesas: # Mientras que la cantidad de mesas existentes sea menor que la indicada por el usuario
        cursor.execute("INSERT `my_resto`.`mesas`(`pedidos`) VALUES(NULL)") # Creamos una nueva mesa
        mesas+=1 # Incrementamos la cantidad de mesas existentes
    conn.commit() # Cerramos conexion
    return redirect('/administracion') # Redireccionamos a administracion

"""Cerrar la cuenta de la mesa pasada por parametro, entregando un resumen de lo consumido y el total a pagar, y guardando los mismos en el registro de ventas"""
@app.route('/cerrar_cuenta/<int:mesa>/')
def cerrarCuenta(mesa):
    conn = mysql.connect() #Creamos la conexión
    cursor = conn.cursor() # Establecemos la conexión
    cursor.execute("SELECT `pedidos`,`hora_abre` FROM `my_resto`.`mesas` WHERE `id_mesa` LIKE %s",(mesa)) # Traemos la lista de pedidos, y la hora de apertura de la mesa
    extracto=cursor.fetchall()[0] # Lo almacenamos en variable
    pedidos,horaAbre=extracto # Separamos los datos
    pedidosBorrar=json.loads(pedidos) # Creamos un diccionario a partir de pedidos
    resumen=[] # Creamos una lista para pasar al HTML
    suma=0 # Creamos una la variable que sera el monto a abonar
    if type(pedidosBorrar)==dict: # Si el intento de crear un diccionario con los pedidos tuvo exito
        for key in pedidosBorrar: # Por cada plato dentro de pedidos
            cant=pedidosBorrar[key] # Almacenamos la cantidad pedida del plato
            cursor.execute("SELECT `precio` FROM `my_resto`.`platos` WHERE `nombre` LIKE %s;",(key)) # Buscamos el precio unitario del plato
            precio=int(cursor.fetchone()[0]) # Almacenamos el precio del plato
            monto=precio*cant # Calculamos el sub-total por plato
            suma+=monto # Sumamos el sub-total a la cuenta
            plato=(key,cant,monto) # Agrupamos los datos para pasarlos al HTML
            resumen.append(plato) # Agregamos esos datos a la lista
        resumen.append(suma) # Agregamos el monto total a la lista
        sqlBorrar="UPDATE `my_resto`.`mesas` SET `pedidos`=NULL, `hora_abre`=NULL WHERE `id_mesa`=%s;" # Creamos la sentencia para resetear los datos en la mesa
        cursor.execute(sqlBorrar,mesa) # Ejecutamos el reset
        horaCierra=datetime.now() # Obtenemos la hora actual(hora de cierre de la mesa)
        datosVenta=[mesa,horaAbre,horaCierra,pedidos,suma] # Agrupamos los datos
        sqlventa="INSERT `my_resto`.`ventas` (`mesa`, `hora_abre`, `hora_cierra`, `consumo`, `total`) VALUES(%s,%s,%s,%s,%s);" # Creamos la sentencia para guardar la venta en la DB
        cursor.execute(sqlventa,datosVenta) # Ejecutamos el guardado
        conn.commit() # Cerramos conexion
        return render_template("/prueba.html",resumen=resumen) # Renderizamos el HTML con el resumen de la cuenta
    else: # Si la lista de pedidos estaba vacia
        flash("La mesa no contenia ningun pedido") # Creamos un mensaje con la avertencia
        return redirect("/mesas") # Redireccionamos a mesas


if __name__ == '__main__':
    #DEBUG is SET to TRUE. CHANGE FOR PROD
    app.run(debug=True)

