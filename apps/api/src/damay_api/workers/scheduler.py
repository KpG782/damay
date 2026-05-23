"""APScheduler wrapper that drives the stellar worker + payout cron."""

from __future__ import annotations

import asyncio

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from damay_api.clients.stellar import StellarClient
from damay_api.clients.supabase import SupabaseClient
from damay_api.config import Settings
from damay_api.workers import payout_cron, stellar_worker

logger = structlog.get_logger("damay.scheduler")


class WorkerScheduler:
    def __init__(
        self,
        settings: Settings,
        supabase: SupabaseClient,
        stellar: StellarClient,
    ) -> None:
        self.settings = settings
        self.supabase = supabase
        self.stellar = stellar
        self._scheduler = AsyncIOScheduler(timezone="UTC")
        self._lock = asyncio.Lock()

    def start(self) -> None:
        self._scheduler.add_job(
            self._safe_drain,
            "interval",
            seconds=self.settings.stellar_worker_interval_seconds,
            id="stellar_worker",
            max_instances=1,
            coalesce=True,
        )
        self._scheduler.add_job(
            self._safe_payout_tick,
            "interval",
            seconds=self.settings.payout_cron_interval_seconds,
            id="payout_cron",
            max_instances=1,
            coalesce=True,
        )
        self._scheduler.start()
        logger.info("scheduler_started")

    async def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("scheduler_stopped")

    async def _safe_drain(self) -> None:
        async with self._lock:
            try:
                await stellar_worker.drain_once(self.supabase, self.stellar)
            except Exception as e:
                logger.warning("stellar_drain_error", error=str(e))

    async def _safe_payout_tick(self) -> None:
        try:
            await payout_cron.tick(self.supabase)
        except Exception as e:
            logger.warning("payout_tick_error", error=str(e))
