import os

PROXY_URL = os.getenv('PROXY_URL', str) # example: 'http://localhost:7890'
TGBOT_TOKEN = os.getenv('TG_BOT_TOKEN', str) # get from botfather
DOWNLOAD_THREADS = os.getenv('DOWNLOAD_THREADS', int) # best at 8~32
DOWNLOAD_PATH = os.getenv('DOWNLOAD_PATH', '/download') # map '/download' in container to 'path/to/your/physical/directory'
GET_HEADER_TEST_URL = 'https://www.apple.com' # get user-agent