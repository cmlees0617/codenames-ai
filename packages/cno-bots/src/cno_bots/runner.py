"""Run a player bot until disconnect or interrupt."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import signal
from collections.abc import Awaitable, Callable

from game_core.players import OperativePlayer, SpymasterPlayer

logger = logging.getLogger(__name__)

type CNOPlayer = SpymasterPlayer | OperativePlayer


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
            with contextlib.suppress(NotImplementedError, RuntimeError):
                loop.add_signal_handler(sig, trigger)


async def run_player(
    player: CNOPlayer,
    *,
    shutdown: ShutdownController | None = None,
) -> int:
    """Run ``player.play()`` with optional graceful shutdown. Returns exit code."""
    controller = shutdown or ShutdownController()
    run_task = asyncio.create_task(player.play())
    closer = player.close
    controller.install(
        asyncio.get_running_loop(),
        closer,
        run_task=run_task,
    )

    try:
        await run_task
        return 0
    except asyncio.CancelledError:
        logger.info("Interrupted.")
        return 130
    finally:
        await controller.close(closer)
