# Telegram Tracking Bot 🤖
Telegram tracking bot for sent packages.

It allows to add shipments and track them:

<p align="center">
  <img src="images/add.gif" alt="animated" />
</p>

And it also allows to modify shipments once added:

<p align="center">
  <img src="images/admin.gif" alt="animated" />
</p>


## Why?
I had ordered some stuff and I was very impatient. Then, I built this bot, which every 5 minutes sent me the updates (if any) without me having to press F5 constantlly.

## Running
In order to use this bot first clone the repo. Once done that, open the telegram-tracking-bot folder and run:
```
pip install -r requirements.txt
```
Finally run main.py using the telegram bot token as argument:
```
python main.py <TOKEN>
```

The telegram bot token must be created beforehand, following the instructions detailed [here](https://core.telegram.org/bots#6-botfather).

## Structure
This app is divided into 4 files:

 - [main.py](main.py)
 - [bot.py](bot.py) 
 - [database.py](database.py)
 - [providers.py](providers.py)
 - [scheduler.py](scheduler.py)

The first two files are self-explanatory. The last two are helper objects that have common functions to talk with the database and to connect to the API or scrape the providers websites.

### Database
I used `sqlite3` since it comes with Python and this is a very small project.

The functions of this class are divided by its purpose:
 - add
 - get
 - delete

This database doesn't natively allow *concurrency*, which means it can't be called from another thread, which is the case of the bot. So this option must be added:

```python
self.conn = sqlite3.connect('database.db', check_same_thread=False)
```

To be completely sure there's no corruption, a lock mechanism is implemented, which looks something like this:
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

### Providers
The Providers class has the functions to scrape the OCA website (for now) and return the information parsed.

### Scheduler
The Scheduler class creates scheduling jobs for each tracking that check every given time for new information.

### Bot
The Bot class was created using the [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) library.

## Built with 🛠️
- Python

## Authors ✒️
- Agustin Aon - [@aon](https://github.com/aon)
