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
