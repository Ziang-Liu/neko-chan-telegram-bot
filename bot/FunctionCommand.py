import asyncio
import re

import aiohttp
from fake_useragent import UserAgent
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram._message import Sticker, Document, PhotoSize
from telegram.ext import ContextTypes, ConversationHandler

from src.service.Search import AggregationSearch


class Search:
    def __init__(self, proxy: None | str = None):
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
        async def ascii2d_search(url) -> tuple[str, InlineKeyboardMarkup] | tuple[None, None]:
            search_instance = AggregationSearch(proxy = self._proxy)
            result = await search_instance.ascii2d_search(url)
            if result:
                search_thumb = result['thumbnail']
                search_url = result['url']
                search_author = result['author']
                search_author_url = result['author_url']
                message = f"[🖼️]({search_thumb}) Gacha (>ワ<)，完美匹配😼"
                button = [
                    [InlineKeyboardButton("Original", url = search_url)],
                    [InlineKeyboardButton(f"{search_author}", url = search_author_url)]
                ]
                reply_markup = InlineKeyboardMarkup(button)
                return message, reply_markup
            else:
                return None, None

        if update.message.reply_to_message:
            reply_link_preview = update.message.reply_to_message.link_preview_options
            attachment = update.message.reply_to_message.effective_attachment

            if reply_link_preview:
                if "danbooru" or "x" or "pixiv" or "twitter" in reply_link_preview.url:
                    await update.message.reply_text("Why you use result to search 🤔?")
                else:
                    link_url = await self.get_image_url(reply_link_preview.url)
                    msg, mark = await ascii2d_search(link_url)
                    if msg:
                        await update.message.reply_markdown(text = msg)

            if isinstance(attachment, tuple):
                if isinstance(attachment[0], PhotoSize):
                    msg, mark = await ascii2d_search(
                        (await context.bot.get_file(attachment[2].file_id)).file_path)
                    if msg:
                        await update.message.reply_markdown(text = msg, reply_markup = mark)

            if isinstance(attachment, Sticker):
                sticker_url = (await context.bot.get_file(attachment.file_id)).file_path
                sticker_instance = AggregationSearch(proxy = self._proxy)
                await sticker_instance.get_media_bytes(sticker_url)
                media = sticker_instance.image_raw

                if attachment.is_video:
                    filename = attachment.file_unique_id + '.webm'
                    await update.message.reply_document(document = media, filename = filename)
                else:
                    await update.message.reply_photo(photo = media)

            if isinstance(attachment, Document):
                if "image" in attachment.mime_type:
                    msg, mark = await ascii2d_search(
                        (await context.bot.get_file(attachment.thumbnail.file_id)).file_path)
                    if msg:
                        await update.message.reply_markdown(text = msg, reply_markup = mark)

        return ConversationHandler.END
