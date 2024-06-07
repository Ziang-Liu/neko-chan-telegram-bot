import os

from src.utils.Logger import logger


class EnvironmentReader:
    def __init__(self):
        self.BOT_TOKEN = os.getenv('BOT_TOKEN', None)
        self.CHAT_ANYWHERE_KEY = os.getenv('CHAT_ANYWHERE_KEY', None)
        self.MY_USER_ID = int(os.getenv('MY_USER_ID', -1))
        self.BASE_URL = os.getenv('BASE_URL', 'https://api.telegram.org/bot')
        self.BASE_FILE_URL = os.getenv('BASE_FILE_URL', 'https://api.telegram.org/file/bot')
        self.PROXY = os.getenv('PROXY', None)
        self.TELEGRAPH_THREADS = int(os.getenv('TELEGRAPH_THREADS', 4))

    def print_env(self):
        logger.info(f"[Env]: Master user id: {self.MY_USER_ID}")
        logger.info(f"[Env]: Proxy: {self.PROXY}")
        logger.info(f"[Env]: Telegraph threads: {self.TELEGRAPH_THREADS}")
        logger.info(f"[Env]: Base URL: {self.BASE_URL}")
        logger.info(f"[Env]: Base File URL: {self.BASE_FILE_URL}")

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
