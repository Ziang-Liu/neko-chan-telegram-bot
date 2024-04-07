from loguru import logger

logger.disable("httpx")
logger.add("record.log", format= "{time} {level} {function} {message}", level= "INFO")
logger.level("INFO")
