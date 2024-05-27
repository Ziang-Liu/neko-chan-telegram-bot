import asyncio
import re
from typing import Optional

import aiohttp
from fake_useragent import UserAgent
from httpx import Proxy
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, filters

from src.service.Search import AggregationSearch
from src.utils.Logger import logger


class PandoraBox:
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

            if not result:
                logger.info(f"No accurate results for {url}")
                message = "Not found 😿"
                return message, None

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

        # hey, start here c:
        user = update.message.from_user.username
        user_replied_to = update.message.reply_to_message.from_user.username
        logger.info(f"{user} replied to {user_replied_to}: "
                    f"{update.message.text} with update_id {update.update_id}")

        link_preview = update.message.reply_to_message.link_preview_options
        attachment = update.message.reply_to_message.effective_attachment

        if not filters.REPLY.filter(update.message):
            return ConversationHandler.END

        if link_preview:
            if "danbooru" or "x" or "pixiv" or "twitter" in link_preview.url:
                await update.message.reply_text("Why you use result to search 🤔?", do_quote=False)
            else:
                link_url = await self.get_image_url(link_preview.url)
                msg, mark = await search(link_url)
                await update.message.reply_markdown(text = msg, do_quote = False)

            return ConversationHandler.END

        if filters.PHOTO.filter(update.message.reply_to_message):
            photo_file = update.message.reply_to_message.photo[2]
            file_link = (await context.bot.get_file(photo_file.file_id)).file_path
            logger.info(f"{user} want to search image {photo_file.file_id}")

            msg, mark = await search(file_link)
            await update.message.reply_markdown(text = msg, reply_markup = mark, do_quote = False)

            return ConversationHandler.END

        if filters.Sticker.ALL.filter(update.message.reply_to_message):
            sticker_url = (await context.bot.get_file(attachment.file_id)).file_path
            logger.info(f"{user} want sticker {attachment.file_unique_id}")

            sticker_instance = AggregationSearch(proxy = self._proxy)
            await sticker_instance.get_media(sticker_url)

            media = sticker_instance.image_byte

            if attachment.is_video:
                filename = attachment.file_unique_id + '.webm'
                await update.message.reply_document(document = media, filename = filename, do_quote = False)
            else:
                await update.message.reply_photo(photo = media, do_quote = False)

            return ConversationHandler.END

        if filters.Document.IMAGE.filter(update.message.reply_to_message):
            file_link = (await context.bot.get_file(attachment.thumbnail.file_id)).file_path
            logger.info(f"{user} want to search image(document) {attachment.thumbnail.file_id}")

            msg, mark = await search(file_link)
            await update.message.reply_markdown(text = msg, reply_markup = mark, do_quote = False)

            return ConversationHandler.END
        else:
            await update.message.reply_text("这是什么OwO（欲哭无泪）", do_quote = False)

        return ConversationHandler.END
