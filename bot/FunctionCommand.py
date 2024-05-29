import asyncio
import random
import re
from typing import Optional

import aiohttp
from fake_useragent import UserAgent
from httpx import Proxy
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    filters
)
from urlextract import URLExtract

# custom
from src import (
    AggregationSearch,  # class
    logger,             # var
    Telegraph           # class
)


class PandoraBox:
    def __init__(self, proxy: None | Proxy = None):
        self._proxy = proxy
        self._headers = {'User-Agent': UserAgent().random}

    async def _get_image_url(self, query):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url = query, proxy = self._proxy, headers = self._headers) as resp:
                    if resp.status == 200:
                        return re.findall(r'img src="(.*?)"', await resp.text())
        except (aiohttp.ClientError, asyncio.TimeoutError):
            raise aiohttp.ClientError

    async def handle_inline_button(self, update: Update, context: object):
        choices = [
            [InlineKeyboardButton("猫娘交流模式", callback_data = "gpt")],
            [InlineKeyboardButton("Telegraph 队列", callback_data = "komga")],
            [InlineKeyboardButton("帮助", callback_data = "help")],
            [InlineKeyboardButton("关于", callback_data = "start")],
        ]
        reply_markup = InlineKeyboardMarkup(choices)
        await update.message.reply_text("需要什么帮助瞄", reply_markup = reply_markup)

    async def auto_parse_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        async def search(url) -> tuple[str, Optional[InlineKeyboardMarkup]]:
            search_instance = AggregationSearch(proxy = self._proxy)
            result = await search_instance.aggregation_search(url)

            if not result:
                logger.info(f"No accurate results for {url}")
                _message = "Not found 😿"
                return _message, None

            search_url = result['url']
            search_thumb = result['thumbnail']
            _message = f"[🖼️]({search_url}) Gacha (>ワ<) [😼]({search_thumb})"

            if result["class"] == "iqdb":
                search_similarity = result['similarity']
                search_source = result['source']
                button = [
                    [InlineKeyboardButton(f"{search_source}: {search_similarity}% Match", url = search_url)]
                ]
                _reply_markup = InlineKeyboardMarkup(button)
                return _message, _reply_markup

            if result["class"] == "ascii2d":
                search_author = result['author']
                search_author_url = result['author_url']
                button = [
                    [InlineKeyboardButton("Original", url = search_url)],
                    [InlineKeyboardButton(f"{search_author}", url = search_author_url)]
                ]
                _reply_markup = InlineKeyboardMarkup(button)
                return _message, _reply_markup

        # hey, start here c:
        if not filters.REPLY.filter(update.message):
            if re.search(r'hug|cuddle|pet', update.message.text):
                old_fashioned_words = [
                    "唔嗯（蹭蹭）", "没我同意前可别松手哦～",
                    "呜呼～（抱紧）", "（*扑腾扑腾*）不可以突然这样，会害羞的啦～",
                    "嗯哼（脸红）", "（*呼噜呼噜*）好温暖..."
                ]
                await update.message.reply_text(random.choice(old_fashioned_words))
            elif re.search(r'kiss|snog', update.message.text):
                very_shy = [
                    "(⁄ ⁄•⁄ω⁄•⁄ ⁄)", "(*/ω＼*)",
                    "(⁄ ⁄>⁄ ▽ ⁄<⁄ ⁄)", "(⁄ ⁄•⁄-⁄•⁄ ⁄)",
                    "（*轻轻颤抖*）", "唔嗯，嗯，啊"
                ]
                await update.message.reply_text(random.choice(very_shy))

            return ConversationHandler.END

        user = update.message.from_user.username
        user_replied_to = update.message.reply_to_message.from_user.username
        logger.info(f"{user} replied to {user_replied_to}: "
                    f"{update.message.text} with update_id {update.update_id}")

        link_preview = update.message.reply_to_message.link_preview_options
        attachment = update.message.reply_to_message.effective_attachment

        if link_preview:
            if "danbooru" or "x" or "pixiv" or "twitter" in link_preview.url:
                msg = "Why you use result to search 🤔?"
                await update.message.reply_text(text = msg)
            else:
                link_url = await self._get_image_url(link_preview.url)
                msg, mark = await search(link_url)
                await update.message.reply_markdown(text = msg)

            return ConversationHandler.END

        if filters.PHOTO.filter(update.message.reply_to_message):
            photo_file = update.message.reply_to_message.photo[2]
            file_link = (await context.bot.get_file(photo_file.file_id)).file_path
            logger.info(f"{user} want to search image {photo_file.file_id}")

            msg, mark = await search(file_link)
            await update.message.reply_markdown(text = msg, reply_markup = mark)

            return ConversationHandler.END

        if filters.Sticker.ALL.filter(update.message.reply_to_message):
            sticker_url = (await context.bot.get_file(attachment.file_id)).file_path
            logger.info(f"{user} want sticker {attachment.file_unique_id}")

            sticker_instance = AggregationSearch(proxy = self._proxy)
            media = await sticker_instance.get_media(sticker_url)

            if attachment.is_video:
                filename = attachment.file_unique_id + '.webm'
                await update.message.reply_document(document = media, filename = filename)
            else:
                await update.message.reply_photo(photo = media)

            return ConversationHandler.END

        if filters.Document.IMAGE.filter(update.message.reply_to_message):
            file_link = (await context.bot.get_file(attachment.thumbnail.file_id)).file_path
            logger.info(f"{user} want to search image(document) {attachment.thumbnail.file_id}")

            msg, mark = await search(file_link)
            await update.message.reply_markdown(text = msg, reply_markup = mark)

            return ConversationHandler.END
        else:
            await update.message.reply_text("这是什么 OwO（欲哭无泪）")

        return ConversationHandler.END


(KOMGA) = range(1)


class TelegraphHandler:
    def __init__(self, proxy: Optional[Proxy] = None, user_id: int = -1):
        self._proxy = proxy
        self._user_id = user_id
        self._epub_task_queue = asyncio.Queue()
        self._komga_task_queue = asyncio.Queue()
        self._idle_count = 0

        if user_id != -1:
            komga_loop = asyncio.get_event_loop()
            komga_loop.create_task(self._run_komga_task_periodically())

    async def _run_komga_task_periodically(self):
        async def process_queue(queue, num_tasks):
            self._idle_count = 0
            tasks = [Telegraph(await queue.get()) for _ in range(num_tasks)]
            await asyncio.gather(*[task.get_zip() for task in tasks])

        while True:
            if self._idle_count == 20:
                funny_states = [
                    "watch a YouTube video", "enjoy a cup of coffee", "go outside for relax",
                    "play with Neko Chan", "read the logger, interesting", "add some bugs"
                ]
                logger.info(f"[Komga Sync Service]: Idle state, {random.choice(funny_states)}")
                await asyncio.sleep(300)
            else:
                if not self._komga_task_queue.empty():
                    queue_size = self._komga_task_queue.qsize()
                    logger.info(f"[Komga Sync Service]: Pending tasks: {queue_size}")

                    if queue_size == 1:
                        self._idle_count = 0
                        instance = Telegraph(await self._komga_task_queue.get())
                        await asyncio.create_task(instance.get_zip())
                    elif 2 <= queue_size <= 9:
                        await process_queue(self._komga_task_queue, 3)
                    elif queue_size >= 10:
                        await process_queue(self._komga_task_queue, 4)

                self._idle_count += 1
                await asyncio.sleep(3)

    async def _get_link(self, is_epub = False, content = None):
        telegra_ph_links = URLExtract().find_urls(content)
        target_link = next((url for url in telegra_ph_links if "telegra.ph" in url), None)

        if target_link and not is_epub:
            return await self._komga_task_queue.put(target_link)

        if target_link and is_epub:
            return await self._epub_task_queue.put(target_link)

    async def komga_start(self, update: Update, context: object):
        if update.message.from_user.id != self._user_id:
            msg = f"だめですよ~ XwX, {update.message.from_user.username}"
            await update.message.reply_text(text = msg)

            return ConversationHandler.END

        msg = f"@{update.message.from_user.username}, 把 telegraph 链接端上来罢 ฅ(＾・ω・＾ฅ)"
        await update.message.reply_text(text = msg)

        return KOMGA

    async def get_link(self, update: Update, context: object):
        self._idle_count = 0
        await self._get_link(content = update.message.text_markdown)
