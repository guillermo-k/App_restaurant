# Aplicación para administración de un restaurante

## Librerías y dependencias
- Recomendamos la creación de un entorno virtual.
- Instalar Python 3.10 o superior
- Instalar las dependencias del proyecto
  ```bash
  pip3 install -r requirements.txt
  ```
- Instalar MySQL
  ```bash
  sudo apt update
  sudo apt install mysql-server
  sudo systemctl start mysql.service
  ```
  Para verificar si es posible acceder a la terminal de MySQL: `sudo mysql`

- O bien (en vez de instalar MySQL) instalar [XAMPP](https://www.apachefriends.org/download.html), que incluye MySQL  
  **En Windows:**  
  Bajar e instalar el archivo ejecutable.
  
  **En Linux:**
  ```bash
  cd /home/[username]/Downloads
  chmod a+x xampp-linux-*-installer.run
  sudo ./xampp-linux-*-installer.run
  ```
  Luego de correr los comandos anteriores, seguir con la instalación gráfica.  
  
  _NOTA: lo que es estrictamente necesario para correr el proyecto es tener instalado MySQL. Sin embargo, en Windows, instalar XAMPP simplifica mucho el proceso de correr el proyecto por primera vez_


## Correr el proyecto localmente
- Iniciar MySQL Server o Iniciar XAMPP
- Correr la app
  ```bash
  export FLASK_DEBUG=True; export FLASK_APP=app; export FLASK_ENV=development; flask run
  ```

  En Ubuntu, caso de recibir el error, (1698, "Access denied for user 'root'@'localhost'"), [consultar aquí](https://stackoverflow.com/questions/39281594/error-1698-28000-access-denied-for-user-rootlocalhost)

## Pautas para contribuir al proyecto
### Trabajá únicamente en issues que tengas asignados

1. Si querés trabajar en una nueva feature, mirá los issues, y si no encontrás uno relacionado, agregalo, y asignátelo.
2. Una vez que tengas asignado el issue, creá una rama para resolverlo, **siempre partiendo de la rama `main`**:
   ```bash
   git checkout -b nro_issue_descripcion_corta
   ```
3. Creá un PR indicando las pruebas que realizaste para corroborar que los cambios propuestos funcionen correctamente.
4. Cuando hayas decidido que el PR está completo, asigná a Guillermo o a Gianfranco (o a ambos) para que lo revisen.
5. Agregá también la etiqueta `ready-for-review`
6. Una vez aceptado el código, Gianfranco o Guillermo realizarán el merge a la rama main.

## Rebase y solución de conflictos
Te proponemos que antes de dar el toque final a tu rama, realices un rebase.

Fuentes para leer al respecto de rebase:
https://www.atlassian.com/git/tutorials/merging-vs-rebasing
https://dev.to/amalv/a-cleaner-github-workflow-one-commit-per-pull-pequest-3ic1


### En general, estos son los pasos que se siguen para hacer un rebase interactivo (etiqueta `-i`)
1. Ir a rama main
   ```git checkout main```

2. Traer últimos cambios
   ```git pull```

3. Ir a la rama en la que deseás hacer rebase
   ```git checkout rama```

4. Realizar rebase
   ```git rebase -i main```

5. Aparecerá la opción de realizar pick o squash (y algunas otras). Dejá el primer commit como "pick" y cambiá los demás por "s" (o "squash") y guardá los cambios. Después de guardar, se abrirá un segundo diálogo, donde podrás elegir el mensaje del nuevo commit.

6. Realizá un push forzado a tu rama
   ```git push --force```

Después de esta acción, debería quedar sólo un commit en esta rama.

**Si hay conflictos**, se verá un mensaje al respecto luego del paso 4. [Este es un buen video para aprender a resolver conflictos de git.](https://www.youtube.com/watch?v=xNVM5UxlFSA&ab_channel=Ihatetomatoes)
