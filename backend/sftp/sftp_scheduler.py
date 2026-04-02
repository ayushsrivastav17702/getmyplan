"""
SFTP Scheduler — runs background jobs to poll the SFTP server.
In demo mode, simulates processing cycles.
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class SFTPSchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler(daemon=True)
        self.running = False
        self.last_run = None
        self.last_result = None
        self._db = None
        self._sftp = None

    def configure(self, db, sftp_service):
        self._db = db
        self._sftp = sftp_service

    async def _run_cycle(self):
        """Execute one processing cycle (real or demo)."""
        if not self._sftp or not self._db:
            return
        now = datetime.now(timezone.utc)
        if self._sftp.demo_mode:
            records = self._sftp.generate_demo_cycle()
            for r in records:
                await self._db.sftp_logs.insert_one(r)
            self.last_result = {
                'total': len(records),
                'success': sum(1 for r in records if r['status'] == 'success'),
                'failed': sum(1 for r in records if r['status'] != 'success'),
            }
        else:
            # Real SFTP processing would go here
            pass
        self.last_run = now.isoformat()

    def start(self, interval_minutes: int = 30):
        if self.running:
            return
        self.scheduler.add_job(
            func=self._sync_run,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id='sftp_poll',
            name='SFTP Poll Cycle',
            replace_existing=True,
        )
        self.scheduler.start()
        self.running = True
        logger.info("SFTP Scheduler started (interval=%d min)", interval_minutes)

    def stop(self):
        if not self.running:
            return
        self.scheduler.shutdown(wait=False)
        self.running = False
        logger.info("SFTP Scheduler stopped")

    def _sync_run(self):
        """Wrapper to run the async cycle from sync scheduler."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self._run_cycle())
            else:
                loop.run_until_complete(self._run_cycle())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self._run_cycle())

    @property
    def status(self) -> dict:
        return {
            'running': self.running,
            'last_run': self.last_run,
            'last_result': self.last_result,
        }


# Singleton
sftp_scheduler = SFTPSchedulerService()
