import os

# optional
PROXY_URL = os.getenv('PROXY_URL', None)  # eg. 'http://localhost:port' and 'http://' is required
DOWNLOAD_THREADS = os.getenv('DOWNLOAD_THREADS', 4)  # recommend at 8-16
# necessary
BOT_TOKEN = os.getenv('BOT_TOKEN', '')  # get from bot father
USER_ID = os.getenv('USER_ID', -1)
# other
DOWNLOAD_PATH = os.getenv('DOWNLOAD_PATH', '/download')  # you should mount the path
