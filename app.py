import json
from flask import Flask, redirect, render_template, request, session, flash
from flaskext.mysql import MySQL
from datetime import datetime
import os
from flask import send_from_directory
import cryptocode

cantidad_mesas = 3

app = Flask(__name__)

app.secret_key = '123Prueba!'
mysql = MySQL()
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''


mysql.init_app(app)
CARPETA = os.path.join('fotos')
app.config['CARPETA'] = CARPETA

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS `my_resto`;")

cursor.execute("""CREATE TABLE IF NOT EXISTS `my_resto`.`platos` (
    `id_plato` INT(10) NOT NULL AUTO_INCREMENT,
    `nombre` VARCHAR(255) NOT NULL ,
    `descripcion_plato` VARCHAR(5000) NOT NULL ,
    `precio` FLOAT NOT NULL ,
    `foto` VARCHAR(5000) NOT NULL,
    PRIMARY KEY (`id_plato`) );""")

cursor.execute("""CREATE TABLE IF NOT EXISTS `my_resto`.`mesas` (
    `id_mesa` INT(10) NOT NULL AUTO_INCREMENT,
    `pedidos` JSON DEFAULT ('{ }'),
    `hora_abre` DATETIME,
    PRIMARY KEY (`id_mesa`));""")

cursor.execute("""CREATE TABLE IF NOT EXISTS `my_resto`.`usuarios`(
    `usuario` VARCHAR(255) NOT NULL,
    `password` VARCHAR(500) NOT NULL,
    `super_usuario` BOOLEAN NULL DEFAULT FALSE,
    PRIMARY KEY (`usuario`))""")

cursor.execute("""CREATE TABLE IF NOT EXISTS `my_resto`.`ventas`(
    `id_venta` INT(20) NOT NULL AUTO_INCREMENT,
    `mesa`INT(10),
    `hora_abre` DATETIME ,
    `hora_cierra` DATETIME,
    `consumo` JSON NOT NULL DEFAULT ('{ }'),
    `total` INT(10),
    PRIMARY KEY (`id_venta`));""")

cursor.execute("SELECT count(*) FROM `my_resto`.`usuarios`")
cantidadDeUsuarios = cursor.fetchone()[0]

if cantidadDeUsuarios == 0:
    clave = cryptocode.encrypt('admin', app.secret_key)
    cursor.execute("""INSERT `my_resto`.`usuarios`(
        `usuario`,`password`,`super_usuario`)
        VALUES ('admin', %s, 1);""", (clave))
conn.commit()


@app.route('/')
def login():
    return render_template('/index.html')


@app.route('/ingresar', methods=['POST'])
def ingresar():
    nombre = request.form['txtUsuario']
    password = request.form['txtPassword']
    sql = "SELECT * FROM `my_resto`.`usuarios` WHERE `usuario` LIKE %s"
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sql, nombre)
    global usuario
    usuario = cursor.fetchall()
    conn.commit()
    if usuario != ():
        clave2 = cryptocode.decrypt(usuario[0][1], app.secret_key)
        if password == clave2:
            session['username'] = usuario[0][0]
            if usuario[0][2]:
                session['super'] = usuario[0][2]
            global cantidad_mesas
            cantidad_mesas = int(request.form['cantidad_mesas'])
            return redirect('/mesas')
        else:
            flash('Usuario o contraseña erroneos')
            return redirect('/')
    else:
        flash('Usuario o contraseña erroneos')
        return redirect('/')


@app.route('/mesas/')
def mesas():
    """Listado de mesas, carga de pedidos por mesa, y cierre de mesa"""

    if 'username' in session:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT `id_mesa`,`pedidos` FROM `my_resto`.`mesas`")
        mesas = cursor.fetchall()
        mesas = list(mesas)
        for indexMesa in range(len(mesas)):
            suma = 0
            mesas[indexMesa] = list(mesas[indexMesa])
            mesas[indexMesa][1] = (str(mesas[indexMesa][1])[1:-1]).split(',')
            for indicePedido in range(len(mesas[indexMesa][1])):
                plato = mesas[indexMesa][1][indicePedido].split(': ')
                cursor.execute("""SELECT `precio` FROM `my_resto`.`platos`
                WHERE `nombre` LIKE %s;""", (plato[0].strip()[1:-1]))
                precio = cursor.fetchall()
                if len(mesas[indexMesa][1][indicePedido]) > 3:
                    i = mesas[indexMesa][1]
                    i[indicePedido] = (
                        i[indicePedido], precio[0][0]*int(plato[1]))
                    suma += precio[0][0]*int(plato[1])
                else:
                    mesas[indexMesa][1][indicePedido] = ['Sin pedidos', 0]
            mesas[indexMesa].append(suma)
        mesas = mesas[:cantidad_mesas]
        return render_template('/mesas.html', mesas=mesas)
    else:
        flash('Debe registrarse antes')
        return redirect('/')


@app.route('/logout/')
def logout():
    session.pop('username', None)  # Borramos la cookie
    session.pop('super', None)  # Borramos la cookie
    return redirect('/')


@app.route('/platos/<int:id_mesa>/')
def platos(id_mesa):
    """Listado del menu disponible
    Agregar o quitar platos al pedido
    """

    if 'username' in session:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM `my_resto`.`platos`;")
        platos = cursor.fetchall()
        conn.commit()
        return render_template('platos.html', platos=platos, mesa=id_mesa)
    else:
        return redirect('/')


@app.route('/administracion/')
def administracion():
    """Administración
    Alta y edición de usuarios
    Platos
    Configura la cantidad de mesas
    """

    if 'username' in session:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT* FROM `my_resto`.`platos`;")
        platos = cursor.fetchall()
        conn.commit()
        """Renderizamos administracion.html
        pasando el menu y la cantidad de mesas seleccionadas"""
        return render_template(
                'administracion.html', platos=platos, cantidad=cantidad_mesas)
    else:
        return redirect('/')


@app.route('/destroy/<int:id>')  # Recibe como parámetro el id del producto
def destroy(id):
    """Borrado de plato por ID"""
    if 'username' in session:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("""SELECT foto FROM `my_resto`.`platos`
        WHERE id_plato=%s""", id)
        fila = cursor.fetchall()
        borrarFoto(fila[0][0])
        sql = "DELETE FROM `my_resto`.`platos` WHERE id_plato=%s"
        cursor.execute(sql, (id))
        conn.commit()
        return redirect('/administracion')
    else:
        return redirect('/')


@app.route('/edit/<int:id>')  # Recibe como parámetro el id del plato
def edit(id):
    """Formulario para editar el plato"""

    if 'username' in session:
        conn = mysql.connect()
        cursor = conn.cursor()
        sql = "SELECT * FROM `my_resto`.`platos` WHERE id_plato=%s"
        cursor.execute(sql, (id))
        plato = list(cursor.fetchone())
        conn.commit()
        return render_template('edit.html', plato=plato)
    else:
        return redirect('/')


@app.route('/update', methods=['POST'])
@app.route('/update/<int:id_plato>', methods=['POST'])
def update(id_plato=None):
    """Platos
    Alta y modificaciones
    """

    if 'username' in session:
        conn = mysql.connect()
        cursor = conn.cursor()
        nombre = request.form['txtNombre'].capitalize().replace(' ', '_')
        descripcion_plato = request.form['txtDescripcionPlato'].capitalize()
        precio = float(request.form['txtPrecio'])
        foto = request.files['txtFoto']
        now = datetime.now()
        tiempo = now.strftime('%Y%H%M%S_')
        extension = foto.filename.split('.')
        if foto.filename != '':
            nuevoNombreFoto = tiempo+nombre+'.'+extension[1]
            foto.save('App_restaurant/fotos/'+nuevoNombreFoto)
            if id_plato is not None:
                sql = 'SELECT foto FROM `my_resto`.`platos` WHERE id_plato=%s'
                cursor.execute(sql, id_plato)
                fotoVieja = cursor.fetchall()[0][0]
                borrarFoto(fotoVieja)
        else:
            nuevoNombreFoto = request.form['viejoNombreFoto']
            if nuevoNombreFoto == '':
                nuevoNombreFoto = 'Sin foto'
        datos = [nombre, descripcion_plato, precio, nuevoNombreFoto]
        if id_plato is not None:
            datos.append(id_plato)
            sql = """UPDATE `my_resto`.`platos`
            SET `nombre`=%s,
            `descripcion_plato`=%s,
            `precio`=%s,
            `foto`=%s
            WHERE id_plato=%s"""
        else:
            sql = """INSERT `my_resto`.`platos`
            (`nombre`,`descripcion_plato`, `precio`, `foto`)
            VALUES(%s,%s,%s,%s)"""
        cursor.execute(sql, datos)
        conn.commit()
        return redirect('/administracion')
    else:
        return redirect('/')


@app.route('/fotos/<nombreFoto>')
def uploads(nombreFoto):
    """Guardado de las fotos en la carpeta correspondiente"""
    return send_from_directory(app.config['CARPETA'], nombreFoto)


@app.route('/crear_usuario/', methods=['POST'])
def crear_usuario():
    """Creacion de nuevo usuario. Requiere ser super usuario"""

    if 'super' in session:
        nuevoUsuario = request.form['txtUsuario']
        nuevoPassword = request.form['txtPassword']
        super = request.form.get('superUsuario')
        nuevoPassword = cryptocode.encrypt(nuevoPassword, app.secret_key)
        usuario1 = nuevoUsuario, nuevoPassword, super
        sql = """INSERT INTO `my_resto`.`usuarios` (
            `usuario`, `password`, `super_usuario`) VALUES (%s, %s,%s)"""
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT `usuario` FROM `my_resto`.`usuarios` ;")
        usuarios1 = cursor.fetchall()
        usuarios = []
        for usuarioj in usuarios1:
            usuarios.append(usuarioj[0])
        if nuevoUsuario not in usuarios:
            cursor.execute(sql, usuario1)
        else:
            flash('Nombre de usuario no disponible')
        conn.commit()
        return redirect('/administracion')
    else:
        flash('Usted no tiene los permisos para agregar un nuevo usuario')
        return redirect('/')


@app.route('/modificar_usuario/', methods=['POST'])
def modificar_usuario():
    """Edicion datos usuario (propios)"""

    if 'username' in session:
        nuevoNombre = request.form['txtUsuario']
        nuevoPassword = request.form['txtPassword']
        nuevoPassword = cryptocode.encrypt(nuevoPassword, app.secret_key)
        usuario1 = (nuevoNombre, nuevoPassword, usuario[0][0])
        sql = """UPDATE `my_resto`.`usuarios`
        SET `usuario`= %s, `password`= %s WHERE `usuario`=%s;"""
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT `usuario` FROM `my_resto`.`usuarios` ;")
        usuarios = cursor.fetchall()  # Almacenamos los datos en una tupla
        if nuevoNombre not in usuarios or nuevoNombre == usuario[0][0]:
            cursor.execute(sql, usuario1)  # Actualizamos del usuario
        else:
            flash('Nombre de usuario no disponible')
        conn.commit()
        return redirect('/administracion')


@app.route('/cargarPedido/<int:mesa>', methods=['POST'])
def cargarPedido(mesa):
    """Cargar pedidos a una mesa"""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = "SELECT `pedidos` FROM `my_resto`.`mesas` WHERE `id_mesa` LIKE %s ;"
    cursor.execute(sql, mesa)
    pedidos = cursor.fetchall()[0][0]
    if bool(pedidos):
        pedidos = json.loads(str(pedidos))
    else:
        hora = datetime.now()
        datos = [hora, mesa]
        sql = "UPDATE `my_resto`.`mesas`SET `hora_abre`=%s WHERE `id_mesa`=%s;"
        cursor.execute(sql, datos)
        pedidos = {}
    keysDB = pedidos.keys()
    datosForm = request.form
    keysForm = datosForm.keys()
    for keyForm in keysForm:
        if int(datosForm[keyForm]) != 0:
            valor = int(datosForm[keyForm])
            if keyForm in keysDB:  # Pedido previamente
                if (int(pedidos[keyForm]) + valor) > 0:
                    pedidos[keyForm] = int(pedidos[keyForm]) + valor
                else:
                    pedidos.pop(keyForm)
            elif valor > 0:
                pedidos.setdefault(keyForm, datosForm[keyForm])
        for key in pedidos:
            pedidos[key] = int(pedidos[key])
    sql = "UPDATE `my_resto`.`mesas` SET `pedidos`=%s WHERE `id_mesa`=%s;"
    valores = (json.dumps(pedidos), mesa)
    cursor.execute(sql, valores)
    conn.commit()
    return redirect('/mesas/')


@app.route('/cantidad_mesas/', methods=['POST'])
def cantidadMesas():
    """Cantidad de mesas del negocio"""

    global cantidad_mesas
    cantidad_mesas = int(request.form['cantidad_mesas'])
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM `my_resto`.`mesas`")
    mesas = int(cursor.fetchone()[0])
    """Mientras que la cantidad de mesas existentes sea menor
    que la indicada por el usuario"""
    while mesas < cantidad_mesas:
        cursor.execute("INSERT `my_resto`.`mesas`(`pedidos`) VALUES(NULL)")
        mesas += 1
    conn.commit()
    return redirect('/administracion')


@app.route('/cerrar_cuenta/<int:mesa>/')
def cerrarCuenta(mesa):
    """Cerrar la cuenta de la mesa"""

    conn = mysql.connect()
    cursor = conn.cursor()
    sql = """SELECT `pedidos`,`hora_abre` FROM `my_resto`.`mesas`
    WHERE `id_mesa` LIKE %s"""
    cursor.execute(sql, mesa)
    extracto = cursor.fetchall()[0]
    pedidos, horaAbre = extracto
    pedidosBorrar = json.loads(pedidos)
    resumen = []
    suma = 0
    if type(pedidosBorrar) == dict:
        for key in pedidosBorrar:
            cant = pedidosBorrar[key]
            sql2 = """SELECT `precio` FROM `my_resto`.`platos`
                WHERE `nombre` LIKE %s;"""
            cursor.execute(sql2, key)  # Buscamos el precio unitario del plato
            precio = int(cursor.fetchone()[0])  # Almacenamos el precio
            monto = precio*cant
            suma += monto
            plato = (key, cant, monto)
            resumen.append(plato)
        resumen.append(suma)
        sqlBorrar = """UPDATE `my_resto`.`mesas`
        SET `pedidos`=NULL, `hora_abre`=NULL
        WHERE `id_mesa`=%s;"""
        cursor.execute(sqlBorrar, mesa)
        horaCierra = datetime.now()
        datosVenta = [mesa, horaAbre, horaCierra, pedidos, suma]
        sqlventa = """INSERT `my_resto`.`ventas`
        (`mesa`, `hora_abre`, `hora_cierra`, `consumo`, `total`)
        VALUES(%s, %s, %s, %s, %s);"""
        cursor.execute(sqlventa, datosVenta)
        conn.commit()
        return render_template('/resumen.html', resumen=resumen)
    else:
        flash('La mesa no contenia ningun pedido')
        return redirect('/mesas')


@app.route('/ventas/', methods=['GET'])
def ventas():
    """Listado de todas las ventas históricas"""

    if 'super' in session:
        desde = request.args.get('desde')
        hasta = request.args.get('hasta')
        mesa = request.args.get('mesa')
        datos = [desde, hasta]
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM `my_resto`.`ventas`")
        ventas = list(cursor.fetchall())
        fechasMin = (str((ventas[0][2]))).split(' ')[0]
        fechasMax = datetime.today().strftime('%Y-%m-%d')
        cursor.execute("SELECT count(*) FROM `my_resto`.`mesas`")
        totalMesas = cursor.fetchone()[0]
        listaMesas = []
        for i in range(1, totalMesas+1):
            listaMesas.append(i)
        if desde and hasta:
            sql = """SELECT * FROM `my_resto`.`ventas`
            WHERE `hora_abre` BETWEEN %s AND %s"""
            if mesa and mesa != 'todas':
                sql += ' AND `mesa` LIKE %s'
                datos.append(int(mesa))
            cursor.execute(sql, datos)
            ventas = list(cursor.fetchall())
            fechasMin = desde
            fechasMax = hasta
        fechasMinMax = (fechasMin, fechasMax)
        total = 0
        for i in range(len(ventas)):
            ventas[i] = list(ventas[i])
            ventas[i][4] = (ventas[i][4][1:-1]).split(',')
            total += ventas[i][5]
        conn.commit()
        return render_template('ventas.html',
                               ventas=ventas,
                               total=total,
                               fechasMinMax=fechasMinMax,
                               listaMesas=listaMesas)
    flash('Usuario no autorizado a ver el historial')
    return redirect('/mesas')


@app.route('/seleccion_mesas/')
def seleccionmesas():
    global cantidad_mesas
    cantidad_mesas = int(request.form['cantidad_mesas'])
    return redirect('/mesas')


def borrarFoto(nombre):
    """Borra la foto de 'App_restaurant/fotos' pasada por parametro"""
    try:
        os.remove('App_restaurant/fotos/' + nombre)
    except FileNotFoundError:
        print('Archivo no encontrado')


if __name__ == '__main__':
    # DEBUG is SET to TRUE. CHANGE FOR PROD
    app.run(debug=True)
