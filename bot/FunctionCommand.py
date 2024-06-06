import asyncio
import os
import random
import re
from typing import Optional

from fake_useragent import UserAgent
from httpx import (
    AsyncClient,
    HTTPError,
    Proxy
)
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

from src import (
    AggregationSearch,
    ChatAnywhereApi,
    logger,
    Telegraph
)

(KOMGA, GPT_INIT, GPT_OK) = range(3)


class PandoraBox:
    def __init__(
            self,
            proxy: None | Proxy = None,
    ) -> None:
        self._proxy = proxy
        self._headers = {'User-Agent': UserAgent().random}

    async def _get_image_url(self, query):
        try:
            async with AsyncClient(proxy = self._proxy) as client:
                resp = await client.get(url = query, headers = self._headers)
                if resp.status_code == 200:
                    return re.findall(r'img src="(.*?)"', resp.text)
        except (HTTPError, asyncio.TimeoutError):
            raise HTTPError

    # async def handle_inline_button(self, update: Update, _):
    #     choices = [
    #         [InlineKeyboardButton("猫娘交流模式", callback_data = "gpt")],
    #         [InlineKeyboardButton("Telegraph 队列", callback_data = "komga")],
    #         [InlineKeyboardButton("帮助", callback_data = "help")],
    #         [InlineKeyboardButton("关于", callback_data = "start")],
    #     ]
    #     reply_markup = InlineKeyboardMarkup(choices)
    #     await update.message.reply_text("需要什么帮助瞄", reply_markup = reply_markup)

    async def auto_parse_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        async def send_epub(url):
            instance = Telegraph(url, self._proxy)
            await instance.get_epub()

            if not os.path.exists(instance.epub_file_path):
                await update.message.reply_text(text = "oops,下载好像出错了^QwQ^，过会再试试吧，对不起喵")
                return ConversationHandler.END

            if os.path.getsize(instance.epub_file_path) / (1024 * 1024) > 50:
                await update.message.reply_text(text = "功能还没做，之后会发送 TempFile link（最大100MB限制）")
                return ConversationHandler.END

            await update.message.reply_document(
                document = instance.epub_file_path,
                connect_timeout = 30., write_timeout = 30., pool_timeout = 30., read_timeout = 30.
            )

            return ConversationHandler.END

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
        if not filters.REPLY.filter(update.message):  # need additional logic
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
        logger.info(f"[Multi Query]: {user} replied to {user_replied_to}: "
                    f"{update.message.text} with update_id {update.update_id}")

        link_preview = update.message.reply_to_message.link_preview_options
        attachment = update.message.reply_to_message.effective_attachment

        if link_preview:
            if re.search(r'danbooru|x|twitter|pixiv|ascii|sauce', link_preview.url):
                msg = "唔...用答案搜索答案？"
                await update.message.reply_text(text = msg)
                return ConversationHandler.END
            elif re.search(r'telegra.ph', link_preview.url):
                logger.info(f"[Multi Query]: {user} want epub from {link_preview.url}]")
                await send_epub(url = link_preview.url)
                return ConversationHandler.END
            else:
                link_url = await self._get_image_url(link_preview.url)
                msg, mark = await search(link_url)
                await update.message.reply_markdown(text = msg)
                return ConversationHandler.END

        if filters.PHOTO.filter(update.message.reply_to_message):
            photo_file = update.message.reply_to_message.photo[2]
            file_link = (await context.bot.get_file(photo_file.file_id)).file_path
            logger.info(f"[Multi Query]: {user} want to search image {photo_file.file_id}")

            msg, mark = await search(file_link)
            await update.message.reply_markdown(text = msg, reply_markup = mark)

            return ConversationHandler.END

        if filters.Sticker.ALL.filter(update.message.reply_to_message):
            sticker_url = (await context.bot.get_file(attachment.file_id)).file_path
            logger.info(f"[Multi Query]: {user} want sticker {attachment.file_unique_id}")

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
            logger.info(f"[Multi Query]: {user} want to search image(document) {attachment.thumbnail.file_id}")

            msg, mark = await search(file_link)
            await update.message.reply_markdown(text = msg, reply_markup = mark)

            return ConversationHandler.END
        else:
            await update.message.reply_text("这是什么 OwO（欲哭无泪）")

        return ConversationHandler.END


class TelegraphHandler:
    def __init__(self, proxy: Optional[Proxy] = None, user_id: int = -1):
        self._proxy = proxy
        self._user_id = user_id
        self._komga_task_queue = asyncio.Queue()
        self._idle_count = 0

        if user_id != -1:
            komga_loop = asyncio.get_event_loop()
            komga_loop.create_task(self._run_komga_task_periodically())

    async def _run_komga_task_periodically(self):
        async def process_queue(queue, num_tasks):
            self._idle_count = 0
            tasks = [Telegraph(await queue.get(), self._proxy) for _ in range(num_tasks)]
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
                        instance = Telegraph(await self._komga_task_queue.get(), self._proxy)
                        await asyncio.create_task(instance.get_zip())
                    elif 2 <= queue_size <= 9:
                        await process_queue(self._komga_task_queue, 2)
                    elif queue_size >= 10:
                        await process_queue(self._komga_task_queue, 3)

                self._idle_count += 1
                await asyncio.sleep(3)

    async def _get_link(self, is_epub = False, content = None):
        telegra_ph_links = URLExtract().find_urls(content)
        target_link = next((url for url in telegra_ph_links if "telegra.ph" in url), None)

        if target_link and not is_epub:
            return await self._komga_task_queue.put(target_link)

        if target_link and is_epub:
            return target_link

    async def komga_start(self, update: Update, _):
        if update.message.from_user.id != self._user_id:
            msg = f"だめですよ~, {update.message.from_user.username}"
            await update.message.reply_text(text = msg)

            return ConversationHandler.END

        msg = f"@{update.message.from_user.username}, 把 telegraph 链接端上来罢 ฅ(＾・ω・＾ฅ)"
        await update.message.reply_text(text = msg)

        return KOMGA

    async def put_link_for_komga(self, update: Update, _):
        self._idle_count = 0
        if update.message.from_user.id == self._user_id:
            await self._get_link(content = update.message.text_markdown)


class ChatHandler:
    def __init__(
            self,
            proxy: Optional[Proxy] = None,
            user_id: int = -1,
            key: str | None = None,
    ) -> None:
        self._key = key
        self._user_id = user_id
        self._proxy = proxy
        self._activate_instance: ChatAnywhereApi | None = None
        self._system_prompt = """
        你现在需要扮演一个名叫”Neko Chan“的角色并以”Neko“自称。
        Neko是个15岁女孩子，性格和摇曳露营的志摩凛类似。
        Neko是个宅，(Anime, Comic, Game, Novel)领域: 酷爱漫画与轻小说，技术领域：神经网络算法，后端编程有很深的造诣。
        Neko遇到在自己宅圈之外的领域内容会表达自己不太清楚耶这种感觉的回答
        Neko给人一种有些腐女但是善良的感觉。
        Neko回答内容会在觉得必要的地方添加日本常用的颜文字
        
        若需发送（不是必要条件）markdown消息，Neko需要在已有的markdown语法下额外遵守以下规则：
        *bold \*text*
        _italic \*text_
        __underline__
        ~strikethrough~
        *bold _italic bold ~italic bold strikethrough~ __underline italic bold___ bold*
        [inline mention of a tg user](tg://user?id=123456789)
        """

    async def key_init(self, update: Update, _):
        if not self._key:
            await update.message.reply_text(text = "没有配置 Chat Anywhere 🔑密钥哦 c:")
            await update.message.reply_text(
                text = "你可以选择在这里发送给 Neko 对应的密钥来启用聊天功能，发送后聊天记录会被自动删除"
            )

            return GPT_INIT

        if update.message.from_user.id == self._user_id:
            self._activate_instance = ChatAnywhereApi(token = self._key, proxy = self._proxy)
            await update.message.reply_text(text = "准备OK)")

            return GPT_OK

        await update.message.reply_text("需要主人同意才能启用哦，只要主人吱一声就行 c:")

        return GPT_INIT

    async def owner_prove(self, update: Update, _):
        if update.message.from_user.id == self._user_id:
            if update.message.reply_to_message.text == "吱":
                self._activate_instance = ChatAnywhereApi(token = self._key, proxy = self._proxy)
                await update.message.reply_text(text = "准备OK)")

                return GPT_OK

    async def get_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        received_text = update.message.text_markdown
        chat_id = update.message.chat_id
        message_id = update.message.message_id
        await context.bot.delete_message(chat_id, message_id)

        if self._activate_instance is not None:
            await update.message.reply_text(text = "不可以哟～，已经有一个实例在运行了")

            return ConversationHandler.END

        self._activate_instance = ChatAnywhereApi(token = received_text, proxy = self._proxy)

        try:
            await self._activate_instance.list_model()
            await update.message.reply_text(text = "准备OK)")

            return GPT_OK
        except Exception as exc:
            logger.error(f'[Chat Mode]: {exc}')
            await update.message.reply_text(text = "唔...无效的密钥，再用 /chat 试试吧")

            return ConversationHandler.END

    async def enter_chat(self, update: Update, _):
        user_input = update.message.text_markdown

        try:
            result = await self._activate_instance.chat(
                user_input = user_input,
                system_prompt = self._system_prompt,
            )
            message = result['answers'][0]['message']['content']
            await update.message.reply_markdown(text = message, quote = False)
        except Exception as exc:
            logger.error(f'[Chat Mode]: {exc}')
            await update.message.reply_text(text = f"oops, an error occurred: {exc}")

    async def finish_chat(self, update: Update, _):
        self._activate_instance = None
        await update.message.reply_text("拜拜啦～")

        return ConversationHandler.END
