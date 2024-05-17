import asyncio
import os
import re
import shutil
import zipfile

import aiofiles
import aiohttp
from bs4 import BeautifulSoup
from ebooklib import epub
from fake_useragent import UserAgent

from src.bot.Environment import EnvironmentReader
from src.utils.LoggerUtil import logger


class Telegraph:
    def __init__(self):
        env = EnvironmentReader()

        # manga params
        self.full_title: str | None = None
        self.manga_title: str | None = None
        self.artist_name: str | None = None

        # network params
        self._proxy = env.get_variable("HTTP_PROXY")
        self._thread = env.get_variable("TELEGRAPH_THREADS")
        self._headers = {'User-Agent': UserAgent().random}

        # working dir
        self.base_folder = env.get_variable("BASE_DIR")
        working_dirs = []
        self.komga_folder = env.get_variable("KOMGA_PATH")
        working_dirs.append(self.komga_folder)
        self.epub_folder = env.get_variable("EPUB_PATH")
        working_dirs.append(self.epub_folder)
        self._temp_folder = env.get_variable("TEMP_PATH")
        working_dirs.append(self._temp_folder)
        self._current_working_dir = os.getcwd()

        # create basic dirs
        for folder in working_dirs:
            os.makedirs(name = folder, exist_ok = True, mode = 0o777)

        # generated path
        self.manga_path = self._temp_folder
        self._download_path = self._temp_folder

        # generate preference
        self._is_epub = False
        self._is_zip = False

    async def _image_retry_handler(self, session, url, image_path, retries=5, delay=3):
        for attempt in range(retries):
            try:
                await self._write_image(session, url, image_path)
                return
            except (aiohttp.ClientError, asyncio.TimeoutError):
                if attempt < retries - 1:
                    await asyncio.sleep(delay)

    async def _start_task_queue(self):
        async def worker():
            while True:
                img_num, url = await queue.get()

                if url is None:
                    break

                image_path = os.path.join(self._download_path, f'{img_num}.jpg')
                await self._image_retry_handler(session, url, image_path)  # use function
                queue.task_done()

        queue = asyncio.Queue()

        for rank, link in enumerate(self._image_url_list):
            queue.put_nowait((rank, link))

        timeout = aiohttp.ClientTimeout(total=10)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks = []

            for _ in range(self._thread):
                task = asyncio.create_task(worker())
                tasks.append(task)

            await queue.join()

            for _ in range(self._thread):
                queue.put_nowait((None, None))

            await asyncio.gather(*tasks)

    async def _create_task(self):
        zip_path = os.path.join(self.manga_path, self.manga_title + '.zip')
        epub_path = os.path.join(self.manga_path, self.manga_title + '.epub')

        if self._is_zip and os.path.exists(zip_path):
            logger.info(f"Skip existed file '{self.manga_title}.zip'")
            return

        if self._is_epub and os.path.exists(epub_path):
            logger.info(f"Skip existed file '{self.manga_title}.epub'")
            return

        if not os.path.exists(self._download_path):
            os.mkdir(self._download_path)

        await self._start_task_queue()
        return

    async def _info_init(self, url: str, retries=5, delay=3):
        timeout = aiohttp.ClientTimeout(total=10)

        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url=url, headers=self._headers, proxy=self._proxy) as resp:
                        if resp.status == 200:
                            # get full title
                            match = r'\*|\||\?|– Telegraph| |/|:'
                            sub = {'*': '٭', '|': '丨', '?': '？', '– Telegraph': '', ' ': '', '/': 'ǀ', ':': '∶'}
                            title_raw = BeautifulSoup(await resp.text(), 'html.parser').find("title").text
                            image_list = re.findall(r'img src="(.*?)"', await resp.text())

                            self._image_url_list = ['https://telegra.ph' + url for url in image_list]
                            self.full_title = re.sub(match, lambda x: sub[x.group()], title_raw)

                            logger.info(f"Start job for '{self.full_title}'")

                            # find manga title
                            title_match = re.search(r'](.*?\(.*?\))', self.full_title)

                            if not title_match:
                                title_match = re.search(r'](.*?)[(\[]', self.full_title)

                            if not title_match:
                                title_match = re.search(r"](.*)", self.full_title)

                            self.manga_title = title_match.group(1) if title_match else self.full_title

                            # find artist
                            artist_match = re.search(r'\[(.*?)(?:\((.*?)\))?]', self.full_title)

                            if artist_match:
                                try_match = artist_match.group(2)
                                self.artist_name = try_match if try_match else artist_match.group(1)
                            else:
                                self.artist_name = 'その他'

                            # confirm manga path
                            if self.artist_name in ['Fanbox', 'FANBOX', 'FanBox', 'Pixiv', 'PIXIV']:
                                self.manga_path = os.path.join(self.komga_folder, self.manga_title)
                            else:
                                self.manga_path = os.path.join(self.komga_folder, self.artist_name)

                            if self._is_epub:
                                self.manga_path = os.path.join(self.epub_folder, self.artist_name)

                            if self._is_zip:
                                self.manga_path = os.path.join(self.komga_folder, self.artist_name)

                            self._download_path = os.path.join(self._temp_folder, self.manga_title)
                            return "OK"
            except (aiohttp.ClientError, asyncio.TimeoutError):
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Info init failed")
                    return "ERROR"

    async def _write_image(self, session, url, image_path) -> None:
        if os.path.exists(image_path) and os.path.getsize(image_path) != 0:
            return

        async with session.get(url, headers = self._headers, proxy = self._proxy) as resp:
            if resp.status == 200:
                async with aiofiles.open(image_path, 'wb') as f:
                    await f.write(await resp.read())

    async def _check_integrity(self, times = 1) -> str:
        if not os.path.exists(self._download_path):
            return "Empty"

        images = [file for file in os.listdir(self._download_path) if file.endswith(".jpg")]
        empty = [file for file in images if os.path.getsize(os.path.join(self._download_path, file)) == 0]

        if len(empty) != 0:
            logger.warning(f"There are {len(empty)} broken images from {self.manga_title}, retrying {times}")
            await asyncio.sleep(10)
            await self._start_task_queue()
            await self._check_integrity(times = times + 1)

        return 'Completed'

    async def _create_zip(self):
        output = os.path.join(self.manga_path, self.manga_title) + '.zip'

        if not os.path.exists(self.manga_path):
            os.mkdir(self.manga_path)

        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as output_zip:
            for root, _, files in os.walk(self._download_path):
                if root == self._download_path:
                    relative_root = ''
                else:
                    relative_root = root.replace(self._download_path, '') + os.sep

                for filename in files:
                    if ".jpg" in filename:
                        output_zip.write(os.path.join(str(root), str(filename)), relative_root + filename)

        shutil.rmtree(self._download_path)
        logger.info(f"Create zip '{output}'")

    async def _create_epub(self):
        sorted_images = sorted([f for f in os.listdir(self._download_path) if
                                os.path.isfile(os.path.join(self._download_path, f)) and str(f).endswith('.jpg')],
                               key = lambda x: int(re.search(r'\d+', x).group()))
        async with aiofiles.open(os.path.join(self._download_path, sorted_images[0]), "rb") as f:
            manga_cover = await f.read()

        manga = epub.EpubBook()
        manga.set_title(self.manga_title)
        manga.set_identifier('dariNirvana')
        manga.add_author(self.artist_name)
        manga.set_cover("cover.jpg", manga_cover)

        if "翻訳" or "汉化" or "中國" or "翻译" or "中文" or "中国" in self.full_title:
            manga.set_language('zh')
        else:
            manga.set_language('ja')

        for i, image in enumerate(sorted_images):
            html = epub.EpubHtml(title = f"Page {i + 1}", file_name = f"image_{i + 1}.xhtml",
                                 content = f"<html><body><img src='{image}'></body></html>".encode('utf8'))
            async with aiofiles.open(os.path.join(self._download_path, image), "rb") as f:
                image_content = await f.read()
            image = epub.EpubImage(uid = image, file_name = image, media_type = "image/jpeg", content = image_content)

            manga.add_item(image)
            manga.add_item(html)
            manga.spine.append(html)
            manga.toc.append(epub.Link(html.file_name, html.title, ''))

        manga.add_item(epub.EpubNav())
        manga.add_item(epub.EpubNcx())

        if not os.path.exists(self.manga_path):
            os.mkdir(self.manga_path)

        os.chdir(self.manga_path)
        epub.write_epub(self.manga_title + '.epub', manga, {})
        os.chdir(self._current_working_dir)
        shutil.rmtree(self._download_path)

        logger.info(f"Create epub '{self.manga_title + '.epub'}'")

    async def _start_process(self, url: str):
        if self._is_zip:
            self._target_function = self._create_zip

        if self._is_epub:
            self._target_function = self._create_epub

        info_return = await self._info_init(url)

        if info_return == "OK":
            await self._create_task()

            check_return = await self._check_integrity()

            if check_return == "Empty":
                return "OK"

            if check_return == 'Completed':
                await self._target_function()
        else:
            return "ERROR"

    async def pack_to_epub(self, url: str):
        self._is_epub = True
        return await self._start_process(url)

    async def sync_to_library(self, url: str):
        self._is_zip = True
        return await self._start_process(url)

    async def get_basic_info(self, url: str):
        return await self._info_init(url)
