# [telegraph-2-Komga-format](https://github.com/Ziang-Liu/telegraph-2-Komga-format)
Since the latest release of [tachiyomi](https://github.com/tachiyomiorg/tachiyomi) removed official support for plugins and recommended connecting to self-hosted comic servers, I intend to migrate many of the comics I've read on Telegraph to the open-source comic management project, [komga](https://github.com/gotson/komga). Based on its categorization of tankobon, I have currently made a simple script for the purpose of downloading, packaging, and archiving comics.

## Usage

### GUI Notes
Check requirements.txt and install related dependence.

### Docker Deployment
1. Paste dockerhub repository **darinirvana/telegraph-2-komga-format** or use command `docker pull darinirvana/telegraph-2-komga-format:latest`
2. Check **docker-compose.yml** and fill corresponding variables. (Only support http_proxy currently and 'http(s)://' is needed.) 

### Bot Config
There is a list of sample commands you can add to your own bot:
``` txt
tgraph_2_komga - Receive telegraph links and send manga to your komga server.
tgraph_2_epub - Receive a telegraph link and convert it to epub file.
komga_complete - Finish "tgraph_2_komga" command
epub_complete - Finish "epub_2_komga" command
```

## Features plan
- [x] Integrating this functionality into a Telegram bot.
- [x] Create a Docker container capable of running on a server.
- [ ] Support epub upload.（etree import error）

## Known Problems
1. If network timeout occurs, the service will have a force quit.
2. The latest downloaded folder will be in used and can not be moved.
