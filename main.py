"""Starts the listener and the scheduler"""


import asyncio

from listener import LISTENER
from scheduler import SCHEDULER


async def main():
    """Main function"""
    SCHEDULER.start()
    await LISTENER.start()


if __name__ == "__main__":
    asyncio.run(main())
