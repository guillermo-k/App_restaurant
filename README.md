# Aplicación para administración de un restaurante

## Librerías y dependencias
- Recomendamos la creación de un entorno virtual.
- Instalar las dependencias del proyecto:
  ```bash
  pip3 install -r requirements.txt
  ```
- Instalar [XAMPP](https://www.apachefriends.org/download.html) (No es necesario en Ubuntu)
  ```bash
  cd /home/[username]/Downloads
  chmod a+x xampp-linux-*-installer.run
  sudo ./xampp-linux-*-installer.run
  ```
  Luego de correr los comandos anteriores, seguir con la instalación gráfica.
- Instalar MySQL (no hace falta si ya está instalado XAMPP)
  ```bash
  sudo apt update
  sudo apt install mysql-server
  sudo systemctl start mysql.service
  sudo mysql_secure_installation
  ```
  Para verificar si es posible acceder a la terminal de MySQL: `sudo mysql`

## Correr el proyecto localmente
- Iniciar MySQL Server
- Iniciar Apache Web Server (XAMPP por lo general trae ambos servicios integrados)
- Correr la app:
  ```bash
  export FLASK_APP=app; export FLASK_ENV=development; flask run
  ```

  En Ubuntu, caso de recibir el error, (1698, "Access denied for user 'root'@'localhost'"), [consultar aquí](https://stackoverflow.com/questions/39281594/error-1698-28000-access-denied-for-user-rootlocalhost)

## Pautas para contribuir al proyecto
1. Trabajar únicamente en issues que estén asignados a uno mismo.
2. Crear una rama para resolver cada issue:
   ```bash
   git checkout -b nro_issue_descripcion_corta
   ```
3. Crear un PR indicando pruebas realizadas para corroborar que los cambios propuestos funcionen correctamente.
4. Asignar una persona para que revise el código.
5. Una vez revisado el código, recién realizar merge a rama main.

