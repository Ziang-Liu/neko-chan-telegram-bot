# Neko-Chan
A self-hosted Telegram bot designed to turn Telegraph links into local manga source that supports platforms such as Komga and Tachiyomi, along with other integrated features for enhanced functionality.
## Docker Deployment  
>You can run [debug.py](https://github.com/Ziang-Liu/Neko-Chan/blob/main/t2c-bot/debug.py) in advance to have a try.
1. Use Docker-hub repository **darinirvana/telegraph-2-komga-format** or use command `docker pull darinirvana/telegraph-2-komga-format:latest`  
2. Check [docker-compose.yml](https://github.com/Ziang-Liu/Neko-Chan/blob/main/docker-compose.yml) , fill necessary environmental variables.
3. Run the container
## Bot Config  
Below is a set of sample commands that can be added to your personal bot:  
``` txt  
monitor_start - Service for link fetching and image search, etc.
monitor_finish - Stop the service and Neko-Chan won't read the messages.
t2epub - Read Telegraph link and give you converted epub file
```  
  
## Features List
- [x] Integrating functionality into a Telegram Bot based on [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot).  
- [x] Docker container support.
- [x] Auto sync Telegraph links into your own Komga server.
- [x] Epub conversion and upload function on Telegram based on [ebooklib](https://github.com/aerkalov/ebooklib).
- [x] Auto image search based on [PicImageSearch](https://github.com/kitUIN/PicImageSearch)
- [ ] Daily conversation feature.
- [ ] EX, EH, NH fetching support.