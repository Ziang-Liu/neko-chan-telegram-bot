import os

TGBOT_TOKEN = os.getenv('TG_BOT_TOKEN', str) # get from botfather
DOWNLOAD_THREADS = os.getenv('DOWNLOAD_THREADS', int) # best at 8~32
DOWNLOAD_PATH = os.getenv('DOWNLOAD_PATH', '/download') # map '/download' in container to 'path/to/your/physical/directory'
GET_HEADER_TEST_URL = 'https://httpbin.org/' # get user-agent
