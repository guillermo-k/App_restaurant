import json
import cryptocode
import os

from datetime import datetime
from flask import (flash,
                   Flask,
                   make_response,
                   redirect,
                   render_template,
                   request, session,
                   send_from_directory,)
from flaskext.mysql import MySQL

import database

app = Flask(__name__)

app.secret_key = '123Prueba!'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['CARPETA'] = os.path.join('fotos')
app.config['CANTIDAD_DE_MESAS'] = int()
app.config['USUARIO'] = None


mysql = MySQL()
mysql.init_app(app)

database.create(mysql)
database.create_default_users(mysql, app.secret_key)
database.define_default_category(mysql)


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
    app.config['USUARIO'] = cursor.fetchone()
    conn.commit()
    usuario, clave, superusuario = app.config['USUARIO']
    if usuario != ():
        if password == cryptocode.decrypt(clave, app.secret_key):
            session['username'] = usuario
            if superusuario:
                session['super'] = superusuario
            return redirect('/mesas')
        else:
            flash('Usuario o contraseña erroneos')
            return redirect('/')
    else:
        flash('Usuario o contraseña erroneos')
        return redirect('/')


@app.route('/mesas/')
def mesas():
    """Listado de mesas, carga de pedidos por mesa, y cierre de mesa
    mesas =[
        {
            'nro_mesa': int,
            'pedido': {
                        'plato': [...],
                        'cantidad': [...],
                        'subtotales': [...]
                      },
            'total': float
        },
    ]
    """

    cookie = request.cookies.get('mesas')
    if cookie:
        app.config['CANTIDAD_DE_MESAS'] = int(cookie)

    if 'username' in session:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT `id_mesa`,`pedidos` FROM `my_resto`.`mesas`")
        mesas_backend = cursor.fetchall()
        mesas = list()
        for mesa in mesas_backend:
            mesa_dict = dict()
            pedido_dict = dict()

            nro_mesa = mesa[0]
            pedido = mesa[1]
            suma = 0

            subtotales_list = list()
            plato_list = list()
            cantidad_list = list()
            if pedido:
                pedido = json.loads(pedido)  # mesa[1] trae un json
                for plato, cantidad in pedido.items():
                    cursor.execute("""SELECT `precio` FROM `my_resto`.`platos`
                                   WHERE `nombre` LIKE %s;""", (plato))
                    precio_unitario = cursor.fetchone()[0]
                    subtotal_por_plato = precio_unitario * int(cantidad)
                    suma += subtotal_por_plato

                    plato_list.append(plato)
                    cantidad_list.append(cantidad)
                    subtotales_list.append(subtotal_por_plato)
            else:
                plato_list = ['Sin pedidos']
                cantidad_list = ['']
                subtotales_list = ['']

            pedido_dict['plato'] = plato_list
            pedido_dict['cantidad'] = cantidad_list
            pedido_dict['subtotales'] = subtotales_list

            mesa_dict['nro_mesa'] = nro_mesa
            mesa_dict['pedido'] = pedido_dict
            mesa_dict['total'] = suma
            mesas.append(mesa_dict)

        # Acotamos la cantidad de mesas al número indicado por el usuario
        mesas = mesas[:app.config['CANTIDAD_DE_MESAS']]

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
        cursor.execute("""SELECT* FROM `my_resto`.`platos`,
                            `my_resto`.`categorias` WHERE
                            `categorias`.`id_categoria`=
                            `platos`.`id_categoria`
                            ORDER BY `categoria`;""")
        platos = cursor.fetchall()
        cursor.execute("SELECT* FROM `my_resto`.`categorias`;")
        categorias = cursor.fetchall()
        conn.commit()
        """Renderizamos administracion.html
        pasando el menu y la cantidad de mesas seleccionadas"""
        return render_template(
                'administracion.html',
                platos=platos,
                cantidad=app.config['CANTIDAD_DE_MESAS'],
                categorias=categorias)
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
        fila = cursor.fetchone()[0]
        borrar_foto(fila)
        sql = "DELETE FROM `my_resto`.`platos` WHERE id_plato=%s"
        cursor.execute(sql, (id))
        conn.commit()
        return redirect('/administracion')
    else:
        return redirect('/')


@app.route('/destroyCategoria/<int:id>')
def destroyCategoria(id):
    """Borrado de categoria por ID"""

    if 'username' in session:
        conn = mysql.connect()
        cursor = conn.cursor()
        sql1 = """SELECT `id_plato` FROM `my_resto`.`platos`
            WHERE `id_categoria` LIKE %s"""
        cursor.execute(sql1, id)
        platos = cursor.fetchall()
        sql2 = """UPDATE `my_resto`.`platos` SET `id_categoria`=1
            WHERE id_plato=%s"""
        for plato in platos:
            cursor.execute(sql2, plato[0])
        sql3 = "DELETE FROM `my_resto`.`categorias` WHERE id_categoria=%s"
        cursor.execute(sql3, (id))
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
        sql = """SELECT* FROM `my_resto`.`platos`,
                `my_resto`.`categorias` WHERE
                `categorias`.`id_categoria`=`platos`.`id_categoria` AND
                id_plato=%s"""
        cursor.execute(sql, (id))
        plato = list(cursor.fetchone())
        cursor.execute("SELECT* FROM `my_resto`.`categorias`;")
        categorias = cursor.fetchall()
        conn.commit()
        return render_template('edit.html', plato=plato,
                               categorias=categorias)
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
        categoria = request.form['txtCategoria']
        now = datetime.now()
        tiempo = now.strftime('%Y%H%M%S_')
        extension = foto.filename.split('.')
        if foto.filename != '':
            nuevoNombreFoto = tiempo+nombre+'.'+extension[1]
            foto.save('App_restaurant/fotos/'+nuevoNombreFoto)
            if id_plato:
                sql = 'SELECT foto FROM `my_resto`.`platos` WHERE id_plato=%s'
                cursor.execute(sql, id_plato)
                fotoVieja = cursor.fetchall()[0][0]
                borrar_foto(fotoVieja)
        else:
            nuevoNombreFoto = request.form['viejoNombreFoto']
            if nuevoNombreFoto == '':
                nuevoNombreFoto = 'Sin foto'
        dato = [nombre, descripcion_plato, precio, nuevoNombreFoto, categoria]
        if id_plato:
            dato.append(id_plato)
            sql = """UPDATE `my_resto`.`platos`
            SET `nombre`=%s,
            `descripcion_plato`=%s,
            `precio`=%s,
            `foto`=%s,
            `id_categoria`=%s
            WHERE id_plato=%s"""
        else:
            sql = """INSERT `my_resto`.`platos`
            (`nombre`,`descripcion_plato`, `precio`, `foto`,`id_categoria`)
            VALUES(%s,%s,%s,%s,%s)"""
        cursor.execute(sql, dato)
        conn.commit()
        return redirect('/administracion')
    else:
        return redirect('/')


@app.route('/updateCategoria', methods=['POST'])
@app.route('/updateCategoria/<int:id_categoria>', methods=['POST'])
def updateCategoria(id_categoria=None):
    """Categorias
    Alta y modificaciones
    """

    if 'username' in session:
        conn = mysql.connect()
        cursor = conn.cursor()
        cat = request.form['txtCategoria'].capitalize().replace(' ', '_')
        datos = [cat]
        if id_categoria:
            datos.append(id_categoria)
            sql = """UPDATE `my_resto`.`categorias`
            SET `categoria`=%s
            WHERE id_categoria=%s"""
        else:
            sql = """INSERT `my_resto`.`categorias`
            (`categoria`)
            VALUES(%s)"""
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
        nuevo_usuario = request.form['txtUsuario']
        nuevo_password = cryptocode.encrypt(request.form['txtPassword'], app.secret_key)
        super = request.form.get('superUsuario')
        datos_usuario = nuevo_usuario, nuevo_password, super
        sql = """INSERT INTO `my_resto`.`usuarios` (
            `usuario`, `password`, `super_usuario`) VALUES (%s, %s,%s)"""
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT `usuario` FROM `my_resto`.`usuarios` ;")
        usuarios_backend = cursor.fetchall()
        usuarios_registrados = set(i[0] for i in usuarios_backend)
        if nuevo_usuario not in usuarios_registrados:
            cursor.execute(sql, datos_usuario)
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
        nuevo_nombre = request.form['txtUsuario']
        nuevo_password = request.form['txtPassword']
        nuevo_password = cryptocode.encrypt(nuevo_password, app.secret_key)
        usuario_modificado = nuevo_nombre, nuevo_password, session['username']
        sql = """UPDATE `my_resto`.`usuarios`
        SET `usuario`= %s, `password`= %s WHERE `usuario`=%s;"""
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT `usuario` FROM `my_resto`.`usuarios` ;")
        usuarios_backend = cursor.fetchall()
        usuarios_registrados = set(i[0] for i in usuarios_backend)
        if not (nuevo_nombre in usuarios_registrados and nuevo_nombre == session['username']):
            cursor.execute(sql, usuario_modificado)
            session['username'] = nuevo_nombre
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
        sql = "UPDATE `my_resto`.`mesas`SET`hora_abre`=%s WHERE `id_mesa`=%s;"
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

    app.config['CANTIDAD_DE_MESAS'] = int(request.form['cantidad_mesas'])
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM `my_resto`.`mesas`")
    mesas = int(cursor.fetchone()[0])
    """Mientras que la cantidad de mesas existentes sea menor
    que la indicada por el usuario"""
    while mesas < app.config['CANTIDAD_DE_MESAS']:
        cursor.execute("INSERT `my_resto`.`mesas`(`pedidos`) VALUES(NULL)")
        mesas += 1
    conn.commit()
    respuesta = make_response(redirect('/administracion'))
    respuesta.set_cookie('mesas', str(app.config['CANTIDAD_DE_MESAS']))
    return respuesta


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
        if len(ventas) > 0:
            fechasMin = (str((ventas[0][2]))).split(' ')[0]
        else:
            fechasMin = datetime.today().strftime('%Y-%m-%d')
        fechasMax = datetime.today().strftime('%Y-%m-%d')
        cursor.execute("SELECT count(*) FROM `my_resto`.`mesas`")
        totalMesas = cursor.fetchone()[0]
        listaMesas = []
        for i in range(1, totalMesas+1):
            listaMesas.append(i)
        if desde and hasta:
            sql = """SELECT * FROM `my_resto`.`ventas`
            WHERE `hora_abre` BETWEEN %s AND %s"""
            if mesa:
                if mesa != 'Todas':
                    sql += ' AND `mesa` LIKE %s'
                    datos.append(int(mesa))
            else:
                mesa = 'Todas'
            cursor.execute(sql, datos)
            ventas = list(cursor.fetchall())
            fechasMin = desde
            fechasMax = hasta
        else:
            mesa = 'Todas'
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
                               listaMesas=listaMesas,
                               mesa=mesa)
    flash('Usuario no autorizado a ver el historial')
    return redirect('/mesas')


@app.route('/seleccion_mesas/')
def seleccionmesas():
    app.config['CANTIDAD_DE_MESAS'] = int(request.form['cantidad_mesas'])
    return redirect('/mesas')


def borrar_foto(nombre):
    """Borra la foto de 'App_restaurant/fotos' pasada por parametro"""
    try:
        os.remove('App_restaurant/fotos/' + nombre)
    except FileNotFoundError:
        print('Archivo no encontrado')


if __name__ == '__main__':
    # DEBUG is SET to TRUE. CHANGE FOR PROD
    app.run(debug=True)
