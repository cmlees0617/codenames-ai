"""Shared shutdown handling for async bot sessions."""

from __future__ import annotations

import asyncio
import logging
import signal
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)


class ShutdownController:
    """Cooperative shutdown triggered by SIGINT/SIGTERM."""

    def __init__(self) -> None:
        self.event = asyncio.Event()
        self._closing = False

    async def close(self, closer: Callable[[], Awaitable[None]]) -> None:
        if self._closing:
            return
        self._closing = True
        self.event.set()
        await closer()

    def install(
        self,
        loop: asyncio.AbstractEventLoop,
        closer: Callable[[], Awaitable[None]],
        *,
        run_task: asyncio.Task[object] | None = None,
    ) -> None:
        def trigger() -> None:
            async def handle() -> None:
                logger.info("Interrupt received, leaving room...")
                self.event.set()
                if run_task is not None and not run_task.done():
                    run_task.cancel()
                await self.close(closer)

            asyncio.create_task(handle())

        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, trigger)
            except (NotImplementedError, RuntimeError):
                pass
