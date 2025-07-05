import asyncio
import logging
from typing import List, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from ..config import settings

logger = logging.getLogger(__name__)


class Scheduler:
    """Background job scheduler for refreshing user data"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.jobs = {}
    
    def start(self):
        """Start the scheduler"""
        try:
            self.scheduler.start()
            logger.info("Scheduler started")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
    
    def stop(self):
        """Stop the scheduler"""
        try:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    def add_refresh_job(self, job_id: str, func: Callable, interval_seconds: int = None):
        """Add a periodic refresh job"""
        try:
            interval = interval_seconds or settings.refresh_interval
            
            job = self.scheduler.add_job(
                func,
                trigger=IntervalTrigger(seconds=interval),
                id=job_id,
                replace_existing=True
            )
            
            self.jobs[job_id] = job
            logger.info(f"Added refresh job {job_id} with {interval}s interval")
            
        except Exception as e:
            logger.error(f"Failed to add refresh job {job_id}: {e}")
    
    def remove_job(self, job_id: str):
        """Remove a job"""
        try:
            if job_id in self.jobs:
                self.scheduler.remove_job(job_id)
                del self.jobs[job_id]
                logger.info(f"Removed job {job_id}")
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {e}")
    
    def get_jobs(self) -> List[dict]:
        """Get list of all jobs"""
        try:
            return [
                {
                    "id": job.id,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                }
                for job in self.scheduler.get_jobs()
            ]
        except Exception as e:
            logger.error(f"Error getting jobs: {e}")
            return []
    
    def trigger_job(self, job_id: str):
        """Manually trigger a job"""
        try:
            self.scheduler.modify_job(job_id, next_run_time='now')
            logger.info(f"Triggered job {job_id}")
        except Exception as e:
            logger.error(f"Failed to trigger job {job_id}: {e}") 