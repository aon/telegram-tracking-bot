from apscheduler.schedulers.background import BackgroundScheduler
import logging as log
from datetime import datetime


class Sched:
    def __init__(self, db, prov):
        # Start the scheduler
        self.sched = BackgroundScheduler()
        self.sched.start()
        self.db = db
        self.prov = prov
        
        # Set track time
        self.JOB_INTERVAL = 30 * 60   # seconds

        # Disable below warning-level logs
        log.getLogger('apscheduler.executors.default').setLevel(log.WARNING)
        log.getLogger('apscheduler.scheduler').setLevel(log.WARNING)

        # After restart
        self._add_existing_tracknums()

        # Placeholder so that no error happens
        self.bot = None
        
    def add_tracknum_job(self, id, tracknum, company):

        # Check if already exists, if it doesn't, add it
        # and run it now to get the info
        if not self.sched.get_job(job_id=tracknum+company):
            log.info('sched: add_tracknum_job() = Adding job id: ' +tracknum+company)
            self.sched.add_job(
                lambda: self._update_tracking(tracknum, company),
                'interval',
                seconds=self.JOB_INTERVAL,
                coalesce=True,
                id=tracknum+company,
                next_run_time=datetime.now()
            )

        # Send existing tracking info if it's not adding a job
        elif id:
            info = self.prov.get(tracknum, company)
            log.info('sched: add_tracknum_job() = Sending existing info')
            self.bot.send_update([id], tracknum, company, info, False)
            
    def del_tracknum_job(self, tracknum, company):
        log.info('sched: del_tracknum_job() = Removing job id: ' + tracknum + company)
        self.sched.remove_job(job_id=tracknum+company)        
    
    def _add_existing_tracknums(self):
        """
        Adds existing tracking numbers after reboot
        """
        tracknum_list = self.db.get_tracknums_and_company()
        
        if tracknum_list:
            for num in tracknum_list:
                self.add_tracknum_job(None, num[0], num[1])

    def _update_tracking(self, tracknum, company):
        """
        Job that executes regularly and checks for changes
        """
        log.info('sched: _update_tracking() = Updating tracking ' + tracknum + " " + company)

        info = self.prov.get(tracknum, company)
        new_info = []
        
        # Check if it has location and return if no data
        if not info:
            log.info('sched: _update_tracking() = No provider data')
            return
            
        for row in info:
            date = row["date"]
            description = row["description"]
            location = row["location"]

            # Check if it's new info and add it to database
            is_new_info = self.db.add_tracknum_info(tracknum, date, company, description, location)
            if is_new_info:
                new_info.append(row)
            
        
        # If any info is new, send update to bot        
        if new_info:
            log.info('sched: _update_tracking() = New info detected')
            ids = self.db.get_ids_for_tracknum(tracknum, company)
            log.info('sched: _update_tracking() = Sending info update to bot')
            self.bot.send_update(ids, tracknum, company, new_info, True)
        else:
            log.info('sched: _update_tracking() = No new info')
