"""Public extension point for periodic/background tasks.

The private repository contains personal autonomous routines. They are deliberately
excluded here. Register your own coroutine factories in REGISTERED_TASKS.
"""
import asyncio
import logging

log = logging.getLogger(__name__)


async def example_periodic_task():
    while True:
        await asyncio.sleep(3600)
        try:
            log.info("example periodic task tick")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.error("example task failed: %s", exc, exc_info=True)


# Keep empty by default. Example: REGISTERED_TASKS = [example_periodic_task]
REGISTERED_TASKS = []
