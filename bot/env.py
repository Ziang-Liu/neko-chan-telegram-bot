import os

# optional
PROXY_URL = os.getenv('PROXY_URL', 'http://127.0.0.1:7890')
DOWNLOAD_THREADS = os.getenv('DOWNLOAD_THREADS', 8)
# necessary
BOT_TOKEN = os.getenv('TG_BOT_TOKEN', '6707614408:AAG6nQbYkln_lowLSC95p57eTvQbatYo32M')
DOWNLOAD_PATH = os.getenv('DOWNLOAD_PATH', "/home/tairitsucat/Templates/")
USER_ID = os.getenv('USER_ID', 5229239723)

