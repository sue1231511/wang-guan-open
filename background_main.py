"""Background task extension skeleton.

Private autonomous activity, personal reminders and relationship-specific
behavior have deliberately not been copied into the public repository.
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def example_background_loop():
    while True:
        await asyncio.sleep(3600)
        log.info("example background loop tick")


async def main():
    await asyncio.gather(example_background_loop())


if __name__ == "__main__":
    asyncio.run(main())
