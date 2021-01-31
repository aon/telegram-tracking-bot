import sqlite3
from sqlite3 import Error
import threading
import logging as log

class Database:
    def __init__(self):

        # Define lock for threads
        self.lock = threading.Lock()

        # Create connection and cursor
        self.conn = sqlite3.connect('database.db', check_same_thread=False)
        self.cursor = self.conn.cursor()

        # Make tables
        self._make_tables()

    def _make_tables(self):

        # Create tracking numbers table
        with self.lock:
            self.cursor.execute(
                """ CREATE TABLE IF NOT EXISTS track_nums (
                    user        INTEGER,
                    tracknum    TEXT,
                    company     TEXT,
                    name        TEXT
                ); """)
            
            # Create tracking info table
            self.cursor.execute(
                """ CREATE TABLE IF NOT EXISTS track_info (
                    tracknum    TEXT,
                    company     TEXT,
                    date        TEXT,
                    description TEXT,
                    location    TEXT
                ); """)
        

            # Commit (don't know if necessary, just in case)
            self.conn.commit()

    # ------------ Add --------------- #
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

    def add_tracknum_info(self, tracknum, date, company, description, location) -> bool:
        """
        Adds new gathered info to database

        Returns True if new data, False if existing data.
        """

        exists = self._check_tracknum_info_exists(tracknum, date, company, description, location)
        
        if not exists:
            with self.lock, self.conn:
                self.cursor.execute(
                    "INSERT INTO track_info VALUES (:track_num, :company, :date, :description, :location)",
                    {
                        'track_num':        tracknum,
                        'company':          company,
                        'date':             date,
                        'description':      description,
                        'location':         location
                    },
                    )
            return True
        else:
            return False

    # ------------ Del --------------- #
    def del_tracknum_user(self, chat_id, tracknum, company):
        """
        Deletes tracking number from user database
        """
        with self.lock, self.conn:
            self.cursor.execute(
                "DELETE from track_nums WHERE user=:user AND tracknum=:tracknum",
                {
                    'user':         chat_id,
                    'tracknum':    tracknum
                })
        
    def del_tracknum_info(self, tracknum, company):
        """
        Deletes tracking number from info database
        """
        with self.lock, self.conn:
            self.cursor.execute(
                "DELETE from track_info WHERE tracknum=:tracknum AND company=:company",
                {
                    'tracknum':    tracknum,
                    'company':     company
                })
    
    # ------------ Check --------------- #
    def check_tracknum_exists(self, chat_id, tracknum, company):
        """
        Check if tracknum exists for a given user.
        
        If it doesn't, it returns False.
        If it does, it returns the name given by the user.
        """

        with self.lock:
            self.cursor.execute(
                "SELECT name FROM track_nums WHERE user=:user AND tracknum=:tracknum AND company=:company",
                {
                    'user':        chat_id,
                    'tracknum':    tracknum,
                    'company':     company
                })

            # Shouldn't be more than one, so only fetchone
            data = self.cursor.fetchone()

        if not data:
            return(False)
        else:
            return(data[0])

    def check_name_exists(self, chat_id, name):
        """
        Check if name exists for a given user.
        
        If it doesn't, it returns False.
        If it does, it returns the associated tracknum.
        """

        with self.lock:
            self.cursor.execute(
                "SELECT tracknum FROM track_nums WHERE user=:user AND name=:name",
                {
                    'user':        chat_id,
                    'name':        name
                })

            # Shouldn't be more than one, so only fetchone
            data = self.cursor.fetchone()

        if not data:
            return(False)
        else:
            return(data[0])
    
    def check_anyone_else_has_tracknum(self, tracknum, company):
        """
        Checks if more than one person has this tracknumg.

        If it does it returns True,
        else it returns False.
        """
        with self.lock:
            self.cursor.execute(
                "SELECT user FROM track_nums WHERE tracknum=:tracknum",
                {
                    'tracknum':    tracknum
                })

            data = self.cursor.fetchall()

        if len(data) <= 1:
            return(False)
        else:
            return(True)

    def _check_tracknum_info_exists(self, tracknum, date, company, description, location) -> bool:
        """
        Check if tracknum info exists or not.

        If it doesn't it returns False,
        else it returns True.
        """
        with self.lock:
            self.cursor.execute(
                "SELECT tracknum FROM track_info WHERE tracknum=:tracknum AND company=:company AND date=:date AND description=:description AND location=:location",
                {
                    'tracknum':    tracknum,
                    'company':     company,
                    'date':        date,
                    'description': description,
                    'location':    location
                })

            # Shouldn't be more than one, so only fetchone
            data_exists = self.cursor.fetchone()

        if not data_exists:
            return(False)
        else:
            return(True)
    
    # ------------ Get --------------- #
    def get_user_tracknums(self, chat_id) -> list:
        """
        Returns names associated with id
        """    
        with self.lock:
            self.cursor.execute(
                "SELECT tracknum, name FROM track_nums WHERE user=:user",
                {'user': chat_id}
                )
            track_name_list = self.cursor.fetchall()
        return(track_name_list)

    def get_tracknums_and_company(self):
        """
        Returns a list with every tracknum and its company.
        Used when rebooting bot and adding all jobs.
        """
        with self.lock:
            self.cursor.execute("SELECT tracknum, company FROM track_nums")
            track_company_list = self.cursor.fetchall()    
        return(track_company_list)
        
    def get_ids_for_tracknum(self, tracknum, company) -> list:
        """
        Returns a list of all chat_ids that are following
        a given tracknum and company.
        """
        with self.lock:
            self.cursor.execute(
                "SELECT user FROM track_nums WHERE tracknum=:tracknum AND company=:company",
                {
                    'tracknum':    tracknum,
                    'company':     company
                })
            data_tuple = self.cursor.fetchall()
        
        data = [user[0] for user in data_tuple]     # Get out of tuple
        return data

    def get_tracknum_name(self, tracknum, chat_id, company) -> str:
        """
        Return name for a given tracknum and company
        """
        with self.lock:
            self.cursor.execute(
                "SELECT name FROM track_nums WHERE tracknum=:tracknum AND company=:company AND user=:user",
                {
                    'tracknum':    tracknum,
                    'company':     company,
                    'user':        chat_id
                })
            return self.cursor.fetchone()[0]

    def get_tracknum_and_company_by_name(self, chat_id, name):
        """
        Returns tracknum and company by giving the id and name
        """   
        with self.lock:
            self.cursor.execute(
                "SELECT tracknum, company FROM track_nums WHERE user=:user AND name=:name",
                {
                    'user':     chat_id,
                    'name':     name
                })
            return self.cursor.fetchone()

    def get_existing_info(self, tracknum, company):
        with self.lock:
            self.cursor.execute(
                "SELECT date, description, location FROM track_info WHERE tracknum=:tracknum AND company=:company",
                {
                    'tracknum':     tracknum,
                    'company':      company
                })
            unordered_info = self.cursor.fetchall()
        if unordered_info:
            data = []
            for info in unordered_info:
                data.append(
                    {
                        "date":         info[0],
                        "description":  info[1],
                        "location":     info[2]
                    }
                )
            return data
        else:
            return