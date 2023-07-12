"""Contains Scheduler for timer jobs management"""

from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

import pytz
from date import DATE_TIME_INFO


from settings import SETTINGS_MANAGER
from tuner import Tuner


class Scheduler:
    """Scheduler for timer jobs management"""

    def _add_tuner_job(self):
        self.tuner_job = self.scheduler.add_job(
            self.tuner_wrapper,
            CronTrigger(
                hour=SETTINGS_MANAGER.tuner.scheduler.hour,
                minute=SETTINGS_MANAGER.tuner.scheduler.minute,
                day_of_week=SETTINGS_MANAGER.tuner.scheduler.day_of_week,
                timezone=self._tz,
            ),
        )

    def __init__(self) -> None:
        self._tz = DATE_TIME_INFO.tz

        self.scheduler = AsyncIOScheduler(
            timezone=self._tz,
        )
        self.tuner: Optional[Tuner] = None
        self._add_tuner_job()

    def restart_tuner_job(self):
        """Restarts scrap job"""
        self.scheduler.remove_job(self.tuner_job.id)
        self._add_tuner_job()

    async def tuner_wrapper(self):
        """Tuner wrapper"""
        if self.tuner:
            await self.tuner.start()

    def start(self):
        """Starts the scheduler"""

        self.tuner = Tuner()
        self.scheduler.start()


SCHEDULER = Scheduler()
