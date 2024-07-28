# Neko-Chan

Neko is a self-hosted Telegram bot designed with many useful functions c:, especially for acg lovers.

## 💡 Features List

### Telegram Bot Features

- [x] Download stickers
- [x] Upload manga as EPUB from Telegraph
- [x] Image search using Ascii2d and Iqdb
- [x] Sync manga from Telegraph to server
- [x] ChatGPT assistant support
- [x] Anime timeline search by using stickers(GIF)
- [ ] Dmzj manga update notifications
- [ ] Convert manga from Dmzj links to Telegraph
- [ ] Convert manga from EX, EH, NH links to Telegraph

### Back-end

- [x] Host Docker images on Docker Hub (support for arm64 and amd64)
- [x] Organize manga from provided Telegraph links (support for [Komga](https://github.com/gotson/komga) and Tachiyomi)
- [x] Convert to EPUB using [ebooklib](https://github.com/aerkalov/ebooklib)
- [x] Image search using [PicImageSearch](https://github.com/kitUIN/PicImageSearch) for Ascii2d and Iqdb search
- [x] Integrate [trace.moe](https://soruly.github.io/trace.moe-api/#/) API
- [x] Integrate [ChatAnywhere](https://chatanywhere.apifox.cn/) v1 API
- [x] HTTP(S) and socks5 proxies support
- [x] CloudFlare Worker proxy support based on [Cloudflare-Workers-Proxy](https://github.com/ymyuuu/Cloudflare-Workers-Proxy)
- [ ] Fully integrate Dmzj v3 and v4 APIs
- [ ] Fetch manga from EX, EH, NH sources

## 🔧 Docker Deployment

### Get Image

You can pull the image from **darinirvana/neko-chan:latest** or manually build it from
the [Dockerfile](https://github.com/Ziang-Liu/Neko-Chan/blob/master/Dockerfile).

### Environment Variables:

| Variable          | Description                                       | Default                             |  
|-------------------|---------------------------------------------------|-------------------------------------|  
| BOT_TOKEN         | Required                                          | `None`                              |  
| MY_USED_ID        | Required if you need Telegraph sync service       | `-1`                                |  
| CF_WORKER_PROXY   | CloudFlare Worker proxy                           | `Nonw`                              |
| PROXY             | Required if you can't connect to the API directly | `None`                              |  
| TELEGRAPH_THREADS | Number of images downloaded in a single batch     | `4`                                 |  
| CHAT_ANYWHERE_KEY | For GPT use, optional                             | `None`                              |  

### Additional Information

Mount `/path/to/your/localhost` to `/neko`.

## 📝 Bot Config

Below is a set of sample commands that can be added to your personal bot:

``` txt
hug - 抱抱 Neko！  
cuddle - 轻轻搂住 Neko
pet - 摸摸 Neko 的头
kiss - chu 一下 Neko 的脸颊  
snog - 抱住 Neko 猛亲  
komga - 启用漫画下载模式  
chat - GPT 交流模式  
bye - 关闭 chat
help - Neko Chan 的使用方法  
```
