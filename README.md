# telegram-tracking-bot
Un bot de telegram para hacer seguimiento de paquetes enviados.

Permite agregar envíos y trackearlos:

<p align="center">
  <img src="images/add.gif" alt="animated" />
</p>

Y administrar envíos una vez agregados:

<p align="center">
  <img src="images/admin.gif" alt="animated" />
</p>


## ¿Por qué?
Porque había pedido algunas cosas por Andreani y estaba muy impaciente a que llegaran. Así creé este bot, que cada 5 minutos me mandaba la nueva información.

## Ejecución
Para poder utilizarla básicamente clonan la repo, lo cual les recomiendo usar la aplicación de Github para eso. Una vez hecho esto entran dentro de la carpeta telegram-tracking-bot y corren lo siguiente:
```
pip install -r requirements.txt
```
Esto les instalará todas las librerías necesarias para correr la app. Finalmente corren main.py usando como argumento el token del bot:
```
python main.py <TOKEN>
```

Para poder tener un token van a tener que crear un bot de antemano, siguiendo las instrucciones detalladas [acá](https://core.telegram.org/bots#6-botfather).

## Estructura
El programa cuenta con cuatro archivos:

 - [main.py](main.py)
 - [bot.py](bot.py) 
 - [database.py](database.py)
 - [providers.py](providers.py)
 - [scheduler.py](scheduler.py)

Lo que hacen los dos primeros es bastante obvio. Los últimos dos son helpers que tienen funciones comunes para comunicarse con la base de datos y para conectarse al API/scrapear las páginas web de los proveedores, respectivamente.

### Database
La base de datos que usé es `sqlite3` ya que viene con Python y este es un proyecto muy pequeño. Hay mil tutoriales explicando su funcionamiento y sino es muy intuitiva.

Aquí encontramos la clase Database, con todas las funciones necesarias de ayuda para el bot. Las dividí en tres, que hacen lo que su nombre sugiere:
 - add
 - get
 - delete

Un pequeño detalle que vale la pena mencionar es que no permite *concurrencia*. ¿Qué es la concurrencia? Es la capacidad que tienen los programas de ejecutarse al mismo tiempo, en distintos *threads*. Este es el caso del bot, se ejecuta en un thread distinto al de la base de datos. Lo menciono ya que al crear la conexión en la base de datos, se agrega la opción:

```python
self.conn = sqlite3.connect('database.db', check_same_thread=False)
```

Se agregó entonces `check_same_thread=False` que nos permite conectarnos desde otro thread. Sin embargo eso no es suficiente. Dado que dos threads podrían tratar de escribir en simultáneo la base de datos, se le agrega al comienzo de cada proceso de escritura (y lectura, por las dudas) un comando para que ese thread se bloquee. Esto hace que la pc no pueda ejecutar otro thread mientras se mantenga ese bloqueo. En python esto se traduce a algo así:
```python
def add_tracknum(self, chat_id, tracknum, company, name):
    """
    Adds tracknum to database
    """
    with self.lock, self.conn:
        self.cursor.execute(
            "INSERT INTO track_nums VALUES (:user, :tracknum, :company, :name)",
            {
                'user':         chat_id,
                'tracknum':     tracknum,
                'company':      company.lower(),
                'name':         name
            }
        )  
```
Se usa el comando `with self.lock` que bloquea el thread al comienzo de la ejecución del código y lo desbloquea al finalizar.

### Providers
En este archivo se define la clase Providers. Dentro de ella están las funciones para poder scrapear la web de Oca, solo por ahora, y devolver la información ordenada en forma de un diccionario. Utilicé la librería `requests` pero se podría haber usado cualquier otra.

### Scheduler
Lo que permite la clase Sched es poder definir un BackgroundScheduler y utilizarlo para crear *jobs* que corran cada cierto tiempo. Esto hace que una vez que se agrega un número de tracking, cada un tiempo predefinido se chequee a ver si hay nueva información.

### Bot
En este archivo se define la clase Bot. Utilicé la librería [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot). Tiene muy buena documentación y básicamente todo el código lo saqué de ahí (y leyendo algunos issues interesantes).

En sí el bot en sí puede parecer un lío y es porque lo es. No pude encontrar una mejor manera de escribir los menúes, lo que en la librería se conocen como `ConversationHandler`, que me parecen la mejor manera de manejar la interfaz con el usuario.

## Colaboraciones
Esta es un proyecto bastante sencillo en el que se exploran varias cosas: uso de clases, varios archivos, librerías, logging, concurrencia, un poquito de web-scraping y bases de datos. Lo recomiendo para alguien que haya realizado un curso de Python hace poco y esté buscando experiencia en algún programa real.

Por mi parte escribí el código y los comentarios en inglés, ya que es más fácil colaborar con otros, así que sugiero que las colaboraciones se mantengan en el mismo idioma.

Cualquier duda que se les genere, me mandan un mensaje.