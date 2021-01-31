# Module imports
import logging as log
import sys

# Local imports
from bot import Bot
from database import Database
from providers import Providers
from scheduler import Sched

# Log config
log.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s ',
    level=log.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

def main():
    """ Main function """
    
    # Get token from args
    if len(sys.argv) == 2:
        token = sys.argv[1]
    elif len(sys.argv) == 1:
        print("Error: por favor generar token y usarlo como argumento para correr el bot.")
        return
    else:
        print("Error: se debe utilizar sólo 1 argumento que será el token del bot generado en Telegram.")
        return

    # Initialize classes
    prov = Providers()
    db = Database()
    sch = Sched(db, prov)
    bot = Bot(sch, db, prov, token)
    sch.bot = bot
    
    # Start bot
    bot.updater.start_polling()
    bot.updater.idle()

if __name__ == "__main__":
    main()