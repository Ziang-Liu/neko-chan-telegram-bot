import os

# optional
PROXY_URL = os.getenv('PROXY_URL', str)  # eg. 'http://localhost:port' and 'http://' is required!
DOWNLOAD_THREADS = os.getenv('DOWNLOAD_THREADS', int)  # best at 8~16
# necessary
BOT_TOKEN = os.getenv('BOT_TOKEN', str)  # get from bot father
DOWNLOAD_PATH = os.getenv('DOWNLOAD_PATH', '/download')
USER_ID = os.getenv('USER_ID', int)  # check your own id
