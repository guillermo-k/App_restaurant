import cryptocode


def create(mysql):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS `my_resto`;")

    cursor.execute("""CREATE TABLE IF NOT EXISTS `my_resto`.`categorias` (
        `id_categoria` INT(10) NOT NULL AUTO_INCREMENT,
        `categoria` VARCHAR(255) NOT NULL,
        PRIMARY KEY (`id_categoria`))""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS `my_resto`.`platos` (
        `id_plato` INT(10) NOT NULL AUTO_INCREMENT,
        `nombre` VARCHAR(255) NOT NULL ,
        `descripcion_plato` VARCHAR(5000) NOT NULL ,
        `precio` FLOAT NOT NULL ,
        `foto` VARCHAR(5000) NOT NULL,
        `id_categoria` INT(10) NOT NULL,
        PRIMARY KEY (`id_plato`),
        FOREIGN KEY (`id_categoria`) REFERENCES `my_resto`.`categorias`(
        `id_categoria`));""")

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

    conn.commit()


def create_admin_user(mysql, secret_key):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM `my_resto`.`usuarios`")
    cantidad_de_usuarios = cursor.fetchone()[0]
    if cantidad_de_usuarios == 0:
        clave = cryptocode.encrypt('admin', secret_key)
        cursor.execute("""INSERT `my_resto`.`usuarios`(
            `usuario`,`password`,`super_usuario`)
            VALUES ('admin', %s, 1);""", (clave))
    conn.commit()


def define_default_category(mysql):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM `my_resto`.`categorias`")
    cantidad_de_categorias = cursor.fetchone()[0]
    if cantidad_de_categorias == 0:
        cursor.execute("""INSERT IGNORE `my_resto`.`categorias` (`categoria`)
        VALUES('Sin categoria')""")
    conn.commit()


def load_test_data(mysql):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM `my_resto`.`categorias`")
    test_data_count = cursor.fetchone()[0]
    if test_data_count <= 1:
        cursor.execute("""
        INSERT INTO
            my_resto.categorias (categoria)
        VALUES
            ('tabla'),
            ('bebida s/a'),
            ('bebida c/a'),
            ('minuta');
        """)

        cursor.execute("""
        INSERT INTO
            my_resto.platos (nombre,descripcion_plato,precio,foto,id_categoria)
        VALUES
            ('Tabla Clásica',
             'Salame, queso, aceitumas, jamón crudo
                y cocido',2000,'Sin foto',2),

            ('Tabla Ahumados',
             'Ciervo, cordero, jabalí, trucha, queso
                ahumado, cherrys, gouda paté y aceitunas',2500,'Sin foto',2),

            ('Coca Cola','500ml',300,'Sin foto',3),

            ('Agua','600ml',280,'Sin foto',3),

            ('Sidra Pera','750ml',550,'Sin foto',4),

            ('Milanesa Maryland',
             'Milanesa con bananas fritas',1200,'Sin foto',5);
        """)

    conn.commit()
