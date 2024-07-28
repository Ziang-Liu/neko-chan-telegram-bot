import os

from src.utils.Logger import logger


class EnvironmentReader:
    def __init__(self):
        self.BOT_TOKEN = os.getenv('BOT_TOKEN', None)
        self.CHAT_ANYWHERE_KEY = os.getenv('CHAT_ANYWHERE_KEY', None)
        self.MY_USER_ID = int(os.getenv('MY_USER_ID', -1))
        self.PROXY = os.getenv('PROXY', None)
        self.CF_WORKER_PROXY = os.getenv('CF_WORKER_URL', None)
        self.TELEGRAPH_THREADS = int(os.getenv('TELEGRAPH_THREADS', 2))

    def print_env(self):
        logger.info(f"[Env]: Master user id: {self.MY_USER_ID}") if self.MY_USER_ID is not -1 else None
        logger.info(f"[Env]: Telegraph threads: {self.TELEGRAPH_THREADS}")
        logger.info(f"[Env]: Proxy: {self.PROXY}") if not self.PROXY else None
        logger.info(f"[Env]: CloudFlare Worker Proxy: {self.CF_WORKER_PROXY}") if not self.CF_WORKER_PROXY else None

    def print_attribute(self, attribute_name):
        if hasattr(self, attribute_name):
            attribute_value = getattr(self, attribute_name)
            logger.info(f"[Env]: {attribute_name}: {attribute_value}")
        else:
            attribute_value = getattr(self, attribute_name)
            logger.info(f"[Env]: {attribute_name}: {attribute_value}")

    def get_variable(self, variable_name):
        value = getattr(self, variable_name, None)
        if isinstance(value, str):
            return value.strip() if value is not None else None

        return value
