""" logger
"""
import logging
import config

handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(config.LOG_FORMAT, config.LOG_TIME_FORMAT)
)
handler.setLevel(config.LOG_LEVEL)
logger = logging.getLogger(config.LOG_NAME)
logger.setLevel(config.LOG_LEVEL)
logger.addHandler(handler)
logger.propagate = False


def getLogger(name=None):
    return logger.getChild(name) if name else logger
