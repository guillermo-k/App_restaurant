import json
from flask import Flask, redirect, render_template, request, session, flash
from flaskext.mysql import MySQL
from datetime import datetime
import os  # Nos permite acceder a los archivos
from flask import send_from_directory  # Acceso a las carpetas
import cryptocode

cantidad_mesas = 3

app = Flask(__name__)

app.secret_key = '123Prueba!'
mysql = MySQL()
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''


mysql.init_app(app)  # Inicialización de SQL
CARPETA = os.path.join('fotos')  # Referencia a la carpeta
app.config['CARPETA'] = CARPETA  # Indicamos ruta de la carpeta

# CREACION DE BASE DE DATOS Y TABLAS
conn = mysql.connect()  # Creamos la conexión
cursor = conn.cursor()  # Establecemos la conexión
# Creamos la base de datos
cursor.execute("CREATE DATABASE IF NOT EXISTS `my_resto`;")

"""Creamos la tabla platos(menu con nombre, descripcion, precio y foto)"""
cursor.execute("""CREATE TABLE IF NOT EXISTS `my_resto`.`platos` (
    `id_plato` INT(10) NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(255) NOT NULL ,
    `descripcion_plato` VARCHAR(5000) NOT NULL ,
    `precio` FLOAT NOT NULL ,
    `foto` VARCHAR(5000) NOT NULL,
    PRIMARY KEY (`id_plato`) );""")

""" Creamos la tabla mesas (mesas del restaurant con numero de mesa,
hora y fecha en que se inicia la mesa(se toma el primer pedido) y pedidos
(donde se van a ir cargando los pedidos que realicen los clientes)) """
cursor.execute("""CREATE TABLE IF NOT EXISTS `my_resto`.`mesas` (
    `id_mesa` INT(10) NOT NULL AUTO_INCREMENT,
    `pedidos` JSON DEFAULT ('{ }'),
    `hora_abre` DATETIME,
    PRIMARY KEY (`id_mesa`));""")

# Creamos la tabla usuarios con password y opcion de super usuario
cursor.execute("""CREATE TABLE IF NOT EXISTS `my_resto`.`usuarios`(
    `usuario` VARCHAR(255) NOT NULL,
    `password` VARCHAR(500) NOT NULL,
    `super_usuario` BOOLEAN NULL DEFAULT FALSE,
    PRIMARY KEY (`usuario`))""")

"""Creamos la tabla ventas (registro de las ventas de todo el comercio,
    con numero de mesa, hora de inicio y cierre de atencion, lista de pedidos,
    y total facturado)"""
cursor.execute("""CREATE TABLE IF NOT EXISTS `my_resto`.`ventas`(
    `id_venta` INT(20) NOT NULL AUTO_INCREMENT,
    `mesa`INT(10),
    `hora_abre` DATETIME ,
    `hora_cierra` DATETIME,
    `consumo` JSON NOT NULL DEFAULT ('{ }'),
    `total` INT(10),
    PRIMARY KEY (`id_venta`));""")

# Obtenemos la cantidad de usuarios registrados
cursor.execute("SELECT count(*) FROM `my_resto`.`usuarios`")
# Asignamos lo obtenido en una variable
cantidadDeUsuarios = cursor.fetchone()[0]

if cantidadDeUsuarios == 0:  # Si no hay ningun usuario registrado
    clave = cryptocode.encrypt('admin', app.secret_key)  # Encriptamos el pasw
    # Creamos un super usuario admin : admin para poder iniciar la aplicacion
    cursor.execute("""INSERT `my_resto`.`usuarios`(
        `usuario`,`password`,`super_usuario`)
        VALUES ('admin', %s, 1);""", (clave))
conn.commit()  # Cerramos conexión con DB


@app.route('/')
def login():
    return render_template('/index.html')


@app.route('/ingresar', methods=['POST'])  # Recibimos datos del formulario
def ingresar():
    # Obtenemos desde el form los datos correspondientes
    nombre = request.form['txtUsuario']
    password = request.form['txtPassword']
    # Definimos la busqueda los datos del usuario según el nombre de usuario
    sql = "SELECT * FROM `my_resto`.`usuarios` WHERE `usuario` LIKE %s"
    conn = mysql.connect()  # Creamos la conexión
    cursor = conn.cursor()  # Establecemos la conexión
    cursor.execute(sql, nombre)  # Ejecutamos la busqueda
    global usuario  # Declaramos la asignación de variable usuario es global
    usuario = cursor.fetchall()  # Asignamos el resultado de la busqueda
    conn.commit()  # Cerramos conexión
    if usuario != ():  # Si se encontró el nombre de usuario en la DB
        # Desencriptamos lel password obtenido de la DB
        clave2 = cryptocode.decrypt(usuario[0][1], app.secret_key)
        # Si el password ingresado coincide con el correspondiente en la DB
        if password == clave2:
            session['username'] = usuario[0][0]  # Creamos la cookie
            if usuario[0][2]:  # Si el usuario es super usuario
                # Creamos la cookie para de super usuario
                session['super'] = usuario[0][2]
            global cantidad_mesas
            cantidad_mesas = int(request.form['cantidad_mesas'])
            return redirect('/mesas')
        else:  # Si no es un usuario registrado
            flash('Usuario o contraseña erroneos')  # Escribimos un mensaje
            return redirect('/')  # Y lo redireccionamos a la pagina de login
    else:  # Si no se encontró el nombre de usuario en la DB
        flash('Usuario o contraseña erroneos')  # Escribimos un mensaje
        return redirect('/')  # Lo redireccionamos a la pagina de login


@app.route('/mesas/')
def mesas():
    """
    Listado de mesas, carga de pedidos por mesa, y cierre de mesa
    """

    if 'username' in session:  # Si es usuario registrado
        conn = mysql.connect()  # Creamos la conexión
        cursor = conn.cursor()  # Establecemos la conexión
        # Traemos el numero de las mesas y los pedidos de las mismas
        cursor.execute("SELECT `id_mesa`,`pedidos` FROM `my_resto`.`mesas`")
        mesas = cursor.fetchall()  # Lo almacenamos en variable
        mesas = list(mesas)  # Convertimos la tupla en lista
        for indexMesa in range(len(mesas)):
            suma = 0  # Establecemos la cuenta(monto a pagar) = 0
            # Convertimos la tupla en lista
            mesas[indexMesa] = list(mesas[indexMesa])
            # Limpiamos los datos para obtener los pedidos
            mesas[indexMesa][1] = (str(mesas[indexMesa][1])[1:-1]).split(',')
            # Para cada pedido dentro de la lista, tomamos el indice
            for indicePedido in range(len(mesas[indexMesa][1])):
                # Separamos el nombre del plato y la cantidad
                plato = mesas[indexMesa][1][indicePedido].split(': ')
                # Obtenemos el precio individual del plato por su nombre
                cursor.execute("""SELECT `precio` FROM `my_resto`.`platos`
                WHERE `nombre` LIKE %s;""", (plato[0].strip()[1:-1]))
                precio = cursor.fetchall()  # Lo almacenamos en variable
                # Si ya hay pedidos cargados
                if len(mesas[indexMesa][1][indicePedido]) > 3:
                    # Agregamos el monto a la lista para pasarla al HTML
                    i = mesas[indexMesa][1]
                    i[indicePedido] = (
                        i[indicePedido], precio[0][0]*int(plato[1]))
                    # Calculamos el monto de los pedidos acumulados
                    suma += precio[0][0]*int(plato[1])
                else:  # Si no hay pedidos previos
                    # Modificamos el item pedidos para mostrar algo en el HTML
                    mesas[indexMesa][1][indicePedido] = ['Sin pedidos', 0]
            # Agregamos el monto total a la lista para mostrarlo en el HTML
            mesas[indexMesa].append(suma)
        # Acotamos la cantidad de mesas a el numero indicado por el usuario
        mesas = mesas[:cantidad_mesas]
        # Renderizamos mesas.html y pasamos los datos a mostrar
        return render_template('/mesas.html', mesas=mesas)
    # Si los datos ingresados no corresponden con el de un usuario registrado
    else:
        flash('Debe registrarse antes')  # Escribimos un mensaje al usuario
        return redirect('/')  # y lo enviamos a la pagina de login


@app.route('/logout/')
def logout():
    session.pop('username', None)  # Borramos la cookie
    session.pop('super', None)  # Borramos la cookie
    return redirect('/')  # Redireccionamos a la pagina de inicio, LOGIN


@app.route('/platos/<int:id_mesa>/')
def platos(id_mesa):
    """
    Listado del menu disponible
    Agregar o quitar platos al pedido
    """

    if 'username' in session:  # Si es usuario registrado
        conn = mysql.connect()  # Creamos la conexión
        cursor = conn.cursor()  # Establecemos la conexión
        cursor.execute("SELECT * FROM `my_resto`.`platos`;")  # Traemos menu
        platos = cursor.fetchall()  # Lo almacenamos en variable
        conn.commit()  # Cerramos conexion
        # Renderizamos platos.html pasando el menu y el numero de mesa
        return render_template('platos.html', platos=platos, mesa=id_mesa)
    else:  # Si no es usuario registrado
        return redirect('/')  # Redireccionamos a la pagina de inicio,LOGIN


@app.route('/administracion/')
def administracion():
    """
    Agrega y edita usuarios
    Agrega o elimina plato del menú
    Configura la cantidad de mesas
    """

    if 'username' in session:  # Si es usuario registrado
        conn = mysql.connect()  # Creamos la conexión
        cursor = conn.cursor()  # Establecemos la conexión
        cursor.execute("SELECT* FROM `my_resto`.`platos`;")  # Traemos el menu
        platos = cursor.fetchall()  # Lo almacenamos en variable
        conn.commit()  # Cerramos conexión
        """Renderizamos administracion.html
        pasando el menu y la cantidad de mesas seleccionadas"""
        return render_template(
                'administracion.html', platos=platos, cantidad=cantidad_mesas)
    else:  # Si NO es usuario registrado
        return redirect('/')  # Redireccionamos a inicio


@app.route('/destroy/<int:id>')  # Recibe como parámetro el id del producto
def destroy(id):
    """
    Borrado de plato por ID
    """
    if 'username' in session:  # Si es usuario registrado
        conn = mysql.connect()  # Creamos la conexión
        cursor = conn.cursor()  # Establecemos la conexión
        # Buscamos el nombre de la foto
        cursor.execute("""SELECT foto FROM `my_resto`.`platos`
        WHERE id_plato=%s""", id)
        fila = cursor.fetchall()  # Almacenamos en variable
        borrarFoto(fila[0][0])
        # Eliminamos el producto de la DB por su ID
        sql = "DELETE FROM `my_resto`.`platos` WHERE id_plato=%s"
        cursor.execute(sql, (id))
        conn.commit()  # Cerramos la conexión
        # Volvemos a la pagina de administración
        return redirect('/administracion')
    else:  # Si NO es usuario registrado
        return redirect('/')  # Redireccionamos a Inicio


@app.route('/edit/<int:id>')  # Recibe como parámetro el id del plato
def edit(id):
    """
    Formulario para editar el plato
    """

    if 'username' in session:  # Si es usuario registrado
        conn = mysql.connect()  # Creamos la conexión
        cursor = conn.cursor()  # Establecemos la conexión
        sql = "SELECT * FROM `my_resto`.`platos` WHERE id_plato=%s"
        cursor.execute(sql, (id))  # Buscamos el plato de la DB por su id
        plato = list(cursor.fetchone())  # Almacenamos en variable
        conn.commit()  # Cerramos la conexión
        # Renderizar edit.html con la información obtenida
        return render_template('edit.html', plato=plato)
    else:  # Si NO es usuario registrado
        return redirect('/')  # Redireccionamos a Inicio


@app.route('/update', methods=['POST'])
@app.route('/update/<int:id_plato>', methods=['POST'])
def update(id_plato=None):
    """
    Ingreso en tabla de un nuevo plato,
    o las modificaciones de uno existente
    """

    if 'username' in session:  # Si es usuario registrado
        conn = mysql.connect()  # Creamos la conexión
        cursor = conn.cursor()  # Establecemos la conexión
        # Obtenemos los datos correspondientes desde el form y los almacenamos
        nombre = request.form['txtNombre'].capitalize().replace(' ', '_')
        descripcion_plato = request.form['txtDescripcionPlato'].capitalize()
        precio = float(request.form['txtPrecio'])
        foto = request.files['txtFoto']
        # Obtenemos la fecha y hora para asignarla al nombre de la foto
        now = datetime.now()
        # Obtenemos de la fecha el año, la hora, los minutos y segundos
        tiempo = now.strftime('%Y%H%M%S_')
        # Obtenemos la extensión del archivo de la foto
        extension = foto.filename.split('.')
        if foto.filename != '':  # Si el campo foto no esta vacío
            # Creamos el nombre de la foto
            nuevoNombreFoto = tiempo+nombre+'.'+extension[1]
            # Guardamos la foto en la carpeta correspondiente
            foto.save('App_restaurant/fotos/'+nuevoNombreFoto)
            # Buscamos el nombre de la foto vieja
            sql = 'SELECT `foto` FROM `my_resto`.`platos` WHERE id_plato=%s'
            cursor.execute(sql, id_plato)
            fotoVieja = cursor.fetchall()[0][0]
            borrarFoto(fotoVieja)

        else:  # Si no se adjunto un archivo
            nuevoNombreFoto = request.form['viejoNombreFoto']
            if nuevoNombreFoto == '':
                # Ingresamos texto a mostrar en lugar de la foto
                nuevoNombreFoto = 'Sin foto'
        # Agrupamos los datos para la sentencia SQL
        datos = [nombre, descripcion_plato, precio, nuevoNombreFoto]
        if id_plato is not None:  # Si se paso un ID de plato
            datos.append(id_plato)  # Lo agregamos a los datos
            # Creamos la sentencia para editar el plato en DB
            sql = """UPDATE `my_resto`.`platos`
            SET `nombre`=%s,
            `descripcion_plato`=%s,
            `precio`=%s,
            `foto`=%s
            WHERE id_plato=%s"""
        else:  # Si se paso un ID de plato
            # Creamos la sentencia para crear el plato en DB
            sql = """INSERT `my_resto`.`platos`
            (`nombre`,`descripcion_plato`, `precio`, `foto`)
            VALUES(%s,%s,%s,%s)"""
        # Ejecutamos la sentencia, ya sea para creacion o edicion del plato
        cursor.execute(sql, datos)
        conn.commit()  # Cerramos la conexión
        return redirect('/administracion')  # Volvemos a administración
    else:  # Si NO es usuario registrado
        return redirect('/')  # Redireccionamos a inicio


@app.route('/fotos/<nombreFoto>')
def uploads(nombreFoto):
    """
    Guardado de las fotos en la carpeta correspondiente
    """
    # Guardamos la foto en la carpeta destinada, con su nombre correspondiente
    return send_from_directory(app.config['CARPETA'], nombreFoto)


@app.route('/crear_usuario/', methods=['POST'])
def crear_usuario():
    """
    Creacion de nuevo usuario. Requiere ser super usuario
    """

    if 'super' in session:  # Si es un super usuario
        nuevoUsuario = request.form['txtUsuario']  # Nombre de nuevo usuario
        nuevoPassword = request.form['txtPassword']  # Password
        super = request.form.get('superUsuario')  # Valor de super usuario
        # Encriptamos el password
        nuevoPassword = cryptocode.encrypt(nuevoPassword, app.secret_key)
        usuario1 = nuevoUsuario, nuevoPassword, super  # Agrupamos los datos
        # Creamos la sentencia de creacion de nuevo usuario
        sql = """INSERT INTO `my_resto`.`usuarios` (
            `usuario`, `password`, `super_usuario`) VALUES (%s, %s,%s)"""
        conn = mysql.connect()  # Creamos la conexión
        cursor = conn.cursor()  # Establecemos la conexión
        # Buscamos los nombres de usuarios registrados
        cursor.execute("SELECT `usuario` FROM `my_resto`.`usuarios` ;")
        usuarios1 = cursor.fetchall()
        usuarios = []
        # Creamos una lista de nombres de usuarios ya registrados
        for usuarioj in usuarios1:
            usuarios.append(usuarioj[0])
        # Si el nuevo nombre de usuario no existe en la tabla(debe ser único)
        if nuevoUsuario not in usuarios:
            cursor.execute(sql, usuario1)  # Creamos el usuario
        else:  # Si el nombre ya existe, solicitamos que use otro
            flash('Nombre de usuario no disponible')
        conn.commit()  # Cerramos conexión
        return redirect('/administracion')  # Retornamos a administracion
    else:
        flash('Usted no tiene los permisos para agregar un nuevo usuario')
        return redirect('/')  # Redireccionamos a la pagina de login


@app.route('/modificar_usuario/', methods=['POST'])
def modificar_usuario():
    """
    Edicion datos usuario (propios)
    """

    if 'username' in session:  # Si es un usuario registrado
        nuevoNombre = request.form['txtUsuario']  # Nuevo nombre de usuario
        nuevoPassword = request.form['txtPassword']  # Nuevo passw de usuario
        # Encriptamos el password
        nuevoPassword = cryptocode.encrypt(nuevoPassword, app.secret_key)
        # Agrupamos los datos, junto al nombre viejo del usuario
        usuario1 = (nuevoNombre, nuevoPassword, usuario[0][0])
        # Armamos la sentencia para la actualización del usuario
        sql = """UPDATE `my_resto`.`usuarios`
        SET `usuario`= %s, `password`= %s WHERE `usuario`=%s;"""
        conn = mysql.connect()  # Creamos la conexión
        cursor = conn.cursor()  # Establecemos la conexión
        # Buscamos todos los nombres de usuarios registrados
        cursor.execute("SELECT `usuario` FROM `my_resto`.`usuarios` ;")
        usuarios = cursor.fetchall()  # Almacenamos los datos en una tupla
        # Si el nuevo nombre de usuario no existe, o es igual al nombre viejo
        if nuevoNombre not in usuarios or nuevoNombre == usuario[0][0]:
            cursor.execute(sql, usuario1)  # Actualizamos del usuario
        # Si el nuevo nombre de usuario existe, y no es igual al nombre viejo
        else:
            flash('Nombre de usuario no disponible')  # Escribimos un mensaje
        conn.commit()  # Cerramos la conexión
        return redirect('/administracion')  # Retornamos a administracion


@app.route('/cargarPedido/<int:mesa>', methods=['POST'])
def cargarPedido(mesa):
    """
    Cargar pedidos a una mesa
    """

    conn = mysql.connect()  # Creamos la conexión
    cursor = conn.cursor()  # Establecemos la conexión
    sql = "SELECT `pedidos` FROM `my_resto`.`mesas` WHERE `id_mesa` LIKE %s ;"
    cursor.execute(sql, mesa)  # Buscamos los pedidos previos de la mesa
    pedidos = cursor.fetchall()[0][0]  # Almacenamos en variable
    if bool(pedidos):  # Si ya habia pedidos
        pedidos = json.loads(str(pedidos))  # Convertimos en diccionario
    else:  # Si es el primer pedido
        hora = datetime.now()  # Obtenemos la hora actual
        # Agrupamos la hora y el Id de mesa par pasarlo a la sentencia SQL
        datos = [hora, mesa]
        sql = "UPDATE `my_resto`.`mesas`SET `hora_abre`=%s WHERE `id_mesa`=%s;"
        # Cargamos la hora actual en la mesa en la DB
        cursor.execute(sql, datos)
        pedidos = {}  # Creamos el diccionario para almacenar los pedidos
    # Listamos los nombres de los platos de los pedidos existentes
    keysDB = pedidos.keys()
    # Traemos los nuevos pedidos y los almacenamos en un diccionario
    datosForm = request.form
    # Listamos los nombres de los platos de los nuevos pedidos
    keysForm = datosForm.keys()
    # Recorremos el diccionario de pedidos pasados desde el form
    for keyForm in keysForm:
        # Si el valor es distinto de 0(se agrego o quito algun plato)
        if int(datosForm[keyForm]) != 0:
            valor = int(datosForm[keyForm])  # Convertimos el valor en entero
            """Si el pedido pasado por form es de un plato que
            ya se ha pedido previamente"""
            if keyForm in keysDB:
                # Evitamos platos con cantidad negativa
                if (int(pedidos[keyForm]) + valor) > 0:
                    # Sumamos el pedido previo con el nuevo
                    pedidos[keyForm] = int(pedidos[keyForm]) + valor
                else:  # Si la cantidad resultante es 0 o menor
                    pedidos.pop(keyForm)  # Borramos el plato de la lista
            # Si el pedido es un plato nuevo y la cantidad es positiva
            elif valor > 0:
                # Agregamos el plato y cantidad al diccionario que almacenara
                pedidos.setdefault(keyForm, datosForm[keyForm])
        for key in pedidos:  # Iteramos el diccionario
            # Nos aseguramos que los valores sean enteros
            pedidos[key] = int(pedidos[key])
    # Creamos la sentencia que actualiza la lista de pedidos de la mesa
    sql = "UPDATE `my_resto`.`mesas` SET `pedidos`=%s WHERE `id_mesa`=%s;"
    # Agrupamos datos(convirtiendo el diccionario en Json para almacenamiento)
    valores = (json.dumps(pedidos), mesa)
    cursor.execute(sql, valores)  # Ejecutamos la sentencia
    conn.commit()  # Cerramos la conexion
    return redirect('/mesas/')  # Redirecionamos a mesas


@app.route('/cantidad_mesas/', methods=['POST'])
def cantidadMesas():
    """
    Cantidad de mesas del negocio
    """

    # Declaramos que la variable cantidad_mesas es a nivel global
    global cantidad_mesas
    # Traemos la cantidad de mesas seleccionada por el usuario desde el form
    cantidad_mesas = int(request.form['cantidad_mesas'])
    conn = mysql.connect()  # Creamos la conexión
    cursor = conn.cursor()  # Establecemos la conexión
    # Contamos la cantidad de mesas existentes en la tabla de la DB
    cursor.execute("SELECT count(*) FROM `my_resto`.`mesas`")
    # Lo almacenamos como entero en una variable
    mesas = int(cursor.fetchone()[0])
    """Mientras que la cantidad de mesas existentes sea menor
    que la indicada por el usuario"""
    while mesas < cantidad_mesas:
        # Creamos una nueva mesa
        cursor.execute("INSERT `my_resto`.`mesas`(`pedidos`) VALUES(NULL)")
        mesas += 1  # Incrementamos la cantidad de mesas existentes
    conn.commit()  # Cerramos conexion
    return redirect('/administracion')  # Redireccionamos a administracion


@app.route('/cerrar_cuenta/<int:mesa>/')
def cerrarCuenta(mesa):
    """
    Cerrar la cuenta de la mesa
    """

    conn = mysql.connect()  # Creamos la conexión
    cursor = conn.cursor()  # Establecemos la conexión
    sql = """SELECT `pedidos`,`hora_abre` FROM `my_resto`.`mesas`
    WHERE `id_mesa` LIKE %s"""
    # Traemos la lista de pedidos, y la hora de apertura de la mesa
    cursor.execute(sql, mesa)
    extracto = cursor.fetchall()[0]  # Lo almacenamos en variable
    pedidos, horaAbre = extracto  # Separamos los datos
    # Creamos un diccionario a partir de pedidos
    pedidosBorrar = json.loads(pedidos)
    resumen = []  # Creamos una lista para pasar al HTML
    suma = 0  # Creamos una la variable que sera el monto a abonar
    # Si el intento de crear un diccionario con los pedidos tuvo exito
    if type(pedidosBorrar) == dict:
        for key in pedidosBorrar:  # Por cada plato dentro de pedidos
            # Almacenamos la cantidad pedida del plato
            cant = pedidosBorrar[key]
            sql2 = """SELECT `precio` FROM `my_resto`.`platos`
                WHERE `nombre` LIKE %s;"""
            cursor.execute(sql2, key)  # Buscamos el precio unitario del plato
            precio = int(cursor.fetchone()[0])  # Almacenamos el precio
            monto = precio*cant  # Calculamos el sub-total por plato
            suma += monto  # Sumamos el sub-total a la cuenta
            # Agrupamos los datos para pasarlos al HTML
            plato = (key, cant, monto)
            resumen.append(plato)  # Agregamos esos datos a la lista
        resumen.append(suma)  # Agregamos el monto total a la lista
        # Creamos la sentencia para resetear los datos en la mesa
        sqlBorrar = """UPDATE `my_resto`.`mesas`
        SET `pedidos`=NULL, `hora_abre`=NULL
        WHERE `id_mesa`=%s;"""
        cursor.execute(sqlBorrar, mesa)  # Ejecutamos el reset
        horaCierra = datetime.now()  # Obtenemos la hora actual
        # Agrupamos los datos
        datosVenta = [mesa, horaAbre, horaCierra, pedidos, suma]
        # Creamos la sentencia para guardar la venta en la DB
        sqlventa = """INSERT `my_resto`.`ventas`
        (`mesa`, `hora_abre`, `hora_cierra`, `consumo`, `total`)
        VALUES(%s, %s, %s, %s, %s);"""
        cursor.execute(sqlventa, datosVenta)  # Ejecutamos el guardado
        conn.commit()  # Cerramos conexion
        # Renderizamos el HTML con el resumen de la cuenta
        return render_template('/resumen.html', resumen=resumen)
    else:  # Si la lista de pedidos estaba vacia
        # Creamos un mensaje de avertencia
        flash('La mesa no contenia ningun pedido')
        return redirect('/mesas')  # Redireccionamos a mesas


@app.route('/ventas/')
def ventas():
    """
    Listado de todas las ventas históricas
    """

    if 'super' in session:  # Si es un super usuario
        conn = mysql.connect()  # Creamos la conexión
        cursor = conn.cursor()  # Establecemos la conexión
        # Traemos el historial de ventas
        cursor.execute("SELECT * FROM `my_resto`.`ventas`")
        # Lo almacenamos en variable y transformamos en lista
        ventas = list(cursor.fetchall())
        total = 0  # Establecemos la variable del total cobrado por las ventas
        for i in range(len(ventas)):  # Iteramos el diccionario
            # Convertimos en lista cada uno de los items
            ventas[i] = list(ventas[i])
            # De los pedidos, limpiamos el texto, y lo separamos por plato
            ventas[i][4] = ventas[i][4][1:-1].split(',')
            # Sumamos el monto abonado en esta venta al acumulado
            total += ventas[i][5]
        conn.commit()  # Cerramos conexion
        # Renderizamos el HTML y pasamos los datos para la misma
        return render_template('ventas.html', ventas=ventas, total=total)
    # Si no es super usuario creamos un mensaje
    flash('Usuario no autorizado a ver el historial')
    return redirect('/mesas')  # Redirigimos a mesas


@app.route('/seleccion_mesas/')
def seleccionmesas():
    global cantidad_mesas
    cantidad_mesas = int(request.form['cantidad_mesas'])
    return redirect('/mesas')


def borrarFoto(nombre):
    """Borra la foto de 'App_restaurant/fotos' pasada por parametro"""
    try:
        # Elimina la foto de la carpeta
        os.remove('App_restaurant/fotos/' + nombre)
    except FileNotFoundError:
        print('Archivo no encontrado')


if __name__ == '__main__':
    # DEBUG is SET to TRUE. CHANGE FOR PROD
    app.run(debug=True)
