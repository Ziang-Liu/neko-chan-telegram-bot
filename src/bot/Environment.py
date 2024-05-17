import os

from src.utils.LoggerUtil import logger


class EnvironmentReader:
    def __init__(self):
        # bot params
        self.BOT_TOKEN = str(os.getenv('BOT_TOKEN', ''))
        self.SELF_USER_ID = int(os.getenv('SELF_USER_ID', -1))
        # basic working dirs
        os.makedirs(name = '/media', exist_ok = True, mode = 0o777)
        self.KOMGA_PATH = os.getenv('KOMGA_PATH', '/media/komga/')
        self.DMZJ_PATH = os.getenv('DMZJ_PATH', '/media/dmzj/')
        self.EPUB_PATH = os.getenv('EPUB_PATH', '/media/epub/')
        self.TEMP_PATH = os.getenv('TEMP_PATH', '/media/.temp/')
        self.DEPRECATED_PATH = os.getenv('DEPRECATED_PATH', '/media/.deprecated/')
        # other
        self.HTTP_PROXY: None | str = os.getenv('HTTP_PROXY', None)

    def print_env(self):
        logger.info(f'BOT_TOKEN: {self.BOT_TOKEN}')
        logger.info(f'SELF_USER_ID: {self.SELF_USER_ID}')
        logger.info(f'HTTP_PROXY: {self.HTTP_PROXY}')

    def print_attribute(self, attribute_name):
        if hasattr(self, attribute_name):
            attribute_value = getattr(self, attribute_name)
            logger.info(f"{attribute_name}: {attribute_value}")
        else:
            attribute_value = getattr(self, attribute_name)
            logger.info(f"{attribute_name}: {attribute_value}")

    def get_variable(self, variable_name):
        value = getattr(self, variable_name, None)
        if isinstance(value, str):
            return value.strip() if value is not None else None
        return value
