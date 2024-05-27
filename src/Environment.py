import os

from src.utils.Logger import logger


class EnvironmentReader:
    def __init__(self):
        # bot params
        self.BOT_TOKEN: str | None = os.getenv('BOT_TOKEN', None)  # required
        self.MY_USER_ID: int | None = os.getenv('MY_USER_ID', None)  # in common sense, it is required

        # basic working dirs, no need to change
        self.BASE_DIR = os.getenv('BASE_DIR', '/media')
        os.makedirs(name = self.BASE_DIR, exist_ok = True, mode = 0o777)
        self.KOMGA_PATH = os.getenv('KOMGA_PATH', f'{self.BASE_DIR}/komga/')
        self.DMZJ_PATH = os.getenv('DMZJ_PATH', f'{self.BASE_DIR}/dmzj/')
        self.EPUB_PATH = os.getenv('EPUB_PATH', f'{self.BASE_DIR}/epub/')
        self.TEMP_PATH = os.getenv('TEMP_PATH', f'{self.BASE_DIR}/.temp/')

        # specific params
        self.PROXY: None | str = os.getenv('PROXY', None)  # if your country has GFW, it is required
        self.TELEGRAPH_THREADS = int(os.getenv('TELEGRAPH_THREADS', 4))  # optional

    def print_env(self):
        logger.info("---------------Environment variables---------------")
        logger.info(f"Bot token: {self.BOT_TOKEN}")
        logger.info(f"Master's user id: {self.MY_USER_ID}")
        logger.info(f"Proxy: {self.PROXY}")
        logger.info(f"Telegraph threads: {self.TELEGRAPH_THREADS}")
        logger.info("---------------------------------------------------")

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
