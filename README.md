# Neko-Chan

Neko is a self-hosted Telegram bot designed with many useful functions c:, especially for acg lovers.

## 🔧 Docker Deployment

### Get image

You can Pull image from **darinirvana/neko-chan:latest** or manually build
from [Dockerfile](https://github.com/Ziang-Liu/Neko-Chan/blob/master/Dockerfile)

### Environment list:

| Variable          | Hint                                        | Default                             |  
|-------------------|---------------------------------------------|-------------------------------------|  
| BOT_TOKEN         | required                                    | `None`                              |  
| MY_USED_ID        | required if you need telegraph sync service | `None`                              |  
| BASE_URL          | official bot API URL                        | `https://api.telegram.org/bot`      |  
| BASE_FILE_URL     | official file API URL                       | `https://api.telegram.org/file/bot` |  
| PROXY             | required if can't connect to API directly   | `None`                              |  
| TELEGRAPH_THREADS | how many images downloaded in singe rank    | `4`                                 |  
| CHAT_ANYWHERE_KEY | for GPT use, optional                       | `None`                              |  

### Additional

Mount `/path/to/your/localhost` to `/media`

## 📝 Bot Config

Below is a set of sample commands that can be added to your personal bot:

``` txthug - 抱抱 Neko！  
cuddle - 依偎在 Neko 旁边，轻轻搂住她  
pet - 摸摸 Neko 的头  
kiss - chu~ 一下 Neko 的脸颊  
snog - 抱住 Neko 猛亲  
komga - 启用漫画下载模式  
chat - GPT 交流模式  
bye - 关闭 chathelp - Neko Chan 的使用方法  
```      

## 💡 Features List

### Telegram bot based on [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)

- [x] Sticker download
- [x] Image search
- [x] Sync telegraph manga
- [x] ChatGPT mode
- [ ] Dmzj notification
- [ ] Upload manga from EX, EH, NH links

### Back-end Functions

- [x] Docker Hub image hosting (support arm64 and amd64).
- [x] Organize manga from provided telegraph links (support [Komga](https://github.com/gotson/komga) and Tachiyomi).
- [x] Photo set Epub conversion based on [ebooklib](https://github.com/aerkalov/ebooklib).
- [x] Ascii2d, iqdb search based on [PicImageSearch](https://github.com/kitUIN/PicImageSearch).
- [x] Anime timeline search based on [trace.moe](https://github.com/soruly/trace.moe).
- [x] ChatAnywhere v1 API integration.
- [ ] Full Dmzj v3, v4 API integration.
- [x] HTTP and socks5 proxy integration.
- [ ] EX, EH, NH fetching.