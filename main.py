"""Starts the listener and the scheduler"""
from time import sleep
import logging
from listener import Listener
# from scheduler import SCHEDULER

logging.basicConfig(level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p', format='%(asctime)s %(message)s')
logger = logging.getLogger("listener")


def main():
    """Main function"""
    global logger
    logger.info("Waiting for kafka")
    sleep(15) # Waiting until kafka is ready
    Listener(logger).start()


if __name__ == "__main__":
    main()
