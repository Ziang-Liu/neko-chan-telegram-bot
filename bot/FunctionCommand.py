import asyncio
import re
from typing import Optional

import aiohttp
from fake_useragent import UserAgent
from httpx import Proxy
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram._message import Sticker, Document, PhotoSize
from telegram.ext import ContextTypes, ConversationHandler

from src.service.Search import AggregationSearch
from src.utils.Logger import logger


class Search:
    def __init__(self, proxy: None | Proxy = None):
        self._proxy = proxy
        self._headers = {'User-Agent': UserAgent().random}

    async def get_image_url(self, query):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url = query, proxy = self._proxy, headers = self._headers) as resp:
                    if resp.status == 200:
                        return re.findall(r'img src="(.*?)"', await resp.text())
        except (aiohttp.ClientError, asyncio.TimeoutError):
            raise aiohttp.ClientError

    async def query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        async def search(url) -> tuple[str, Optional[InlineKeyboardMarkup]]:
            search_instance = AggregationSearch(proxy = self._proxy)
            result = await search_instance.aggregation_search(url)

            if result:
                search_url = result['url']
                search_thumb = result['thumbnail']
                message = f"[🖼️]({search_url}) Gacha (>ワ<) [😼]({search_thumb})"

                if result["class"] == "iqdb":
                    search_similarity = result['similarity']
                    search_source = result['source']
                    button = [
                        [InlineKeyboardButton(f"{search_source}: {search_similarity}% Match", url = search_url)]
                    ]
                    reply_markup = InlineKeyboardMarkup(button)
                    return message, reply_markup

                if result["class"] == "ascii2d":
                    search_author = result['author']
                    search_author_url = result['author_url']
                    button = [
                        [InlineKeyboardButton("Original", url = search_url)],
                        [InlineKeyboardButton(f"{search_author}", url = search_author_url)]
                    ]
                    reply_markup = InlineKeyboardMarkup(button)
                    return message, reply_markup
            else:
                logger.info(f"No accurate results for {url}")
                message = "Not found 😿"
                return message, None

        # hey, start here c:
        if update.message.reply_to_message:
            user = update.message.from_user.username
            user_replied_to = update.message.reply_to_message.from_user.username
            logger.info(f"{user} replied to {user_replied_to}: "
                        f"{update.message.text} with update_id {update.update_id}")
            reply_link_preview = update.message.reply_to_message.link_preview_options
            attachment = update.message.reply_to_message.effective_attachment

            if reply_link_preview:
                if "danbooru" or "x" or "pixiv" or "twitter" in reply_link_preview.url:
                    await update.message.reply_text("Why you use result to search 🤔?")
                else:
                    link_url = await self.get_image_url(reply_link_preview.url)
                    msg, mark = await search(link_url)
                    await update.message.reply_markdown(text = msg)

            if isinstance(attachment, tuple):
                if isinstance(attachment[0], PhotoSize):
                    file_link = (await context.bot.get_file(attachment[2].file_id)).file_path
                    logger.info(f"{user} want to search image {attachment[2].file_id}")
                    msg, mark = await search(file_link)
                    await update.message.reply_markdown(text = msg, reply_markup = mark)

            if isinstance(attachment, Sticker):
                sticker_url = (await context.bot.get_file(attachment.file_id)).file_path
                logger.info(f"{user} want sticker {attachment.file_unique_id}")
                sticker_instance = AggregationSearch(proxy = self._proxy)
                await sticker_instance.get_media(sticker_url)
                media = sticker_instance.image_byte

                if attachment.is_video:
                    filename = attachment.file_unique_id + '.webm'
                    await update.message.reply_document(document = media, filename = filename)
                else:
                    await update.message.reply_photo(photo = media)

            if isinstance(attachment, Document):
                if "image" in attachment.mime_type:
                    file_link = (await context.bot.get_file(attachment.thumbnail.file_id)).file_path
                    logger.info(f"{user} want to search image(document) {attachment.thumbnail.file_id}")
                    msg, mark = await search(file_link)
                    await update.message.reply_markdown(text = msg, reply_markup = mark)
        else:
            await update.message.reply_text("Suki 🤗")

        return ConversationHandler.END
