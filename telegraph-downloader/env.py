import os

PROXY_URL = os.getenv('PROXY_URL')
TGBOT_TOKEN = os.getenv('TG_BOT_TOKEN')
DOWNLOAD_THREADS = os.getenv('DOWNLOAD_THREADS', int)
DOWNLOAD_PATH = os.getenv('DOWNLOAD_PATH', '/download')
GET_HEADER_TEST_URL = 'https://www.apple.com'