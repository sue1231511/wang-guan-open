"""Process B: generic periodic/background task runner.

Private autonomous behavior from the author's personal deployment is intentionally
not included. Add your own tasks in background_tasks.py.
"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s", force=True)
log = logging.getLogger(__name__)


async def _main():
    from background_tasks import REGISTERED_TASKS

    coros = [factory() for factory in REGISTERED_TASKS]
    if not coros:
        log.info("No background tasks registered. Process B will stay alive.")
        while True:
            await asyncio.sleep(3600)

    log.info("Starting %d background task(s)", len(coros))
    await asyncio.gather(*coros, return_exceptions=False)


if __name__ == "__main__":
    asyncio.run(_main())
