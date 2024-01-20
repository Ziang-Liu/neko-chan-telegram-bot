# [telegraph-2-Komga-format](https://github.com/Ziang-Liu/telegraph-2-Komga-format)
Since the latest release of [tachiyomi](https://github.com/tachiyomiorg/tachiyomi) removed official support for plugins and recommended connecting to self-hosted comic servers, I intend to migrate many of the comics I've read on Telegraph to the open-source comic management project, [komga](https://github.com/gotson/komga). Based on its categorization of tankobon, I have currently made a simple script for the purpose of downloading, packaging, and archiving comics.

## Usage

### GUI Notes
Review the requirements.txt file and install the relevant dependencies.

### Docker Deployment
1. Paste dockerhub repository **darinirvana/telegraph-2-komga-format** or use command `docker pull darinirvana/telegraph-2-komga-format:latest`
2. Check **docker-compose.yml** and fill corresponding variables. (Note: Currently supports only http_proxy.) 

### Bot Config
Below is a set of sample commands that can be added to your personal bot:
``` txt
tgraph_2_komga - Receive telegraph links and send manga to your komga server.
komga_complete - Finish "tgraph_2_komga" command
```

## Features plan
- [x] Integrating this functionality into a Telegram bot.
- [x] Create a Docker container capable of running on a server.
- [ ] Support epub upload.（etree import error on linux.）
