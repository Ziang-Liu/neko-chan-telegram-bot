import asyncio
import os
import re
import shutil
import zipfile
from datetime import datetime, timedelta

import aiofiles
import aiohttp
from bs4 import BeautifulSoup
from ebooklib import epub
from fake_useragent import UserAgent

from src.Environment import EnvironmentReader
from src.utils.Logger import logger


class Telegraph:
    def __init__(self, url: str) -> None:
        # manga params
        self.url = url
        self.title_raw: str | None = None
        self.title: str | None = None
        self.artist: str | None = None

        env = EnvironmentReader()

        # network params
        self._proxy = env.get_variable("PROXY")
        self._thread = env.get_variable("TELEGRAPH_THREADS")
        self._headers = {'User-Agent': UserAgent().random}

        # working dir
        working_dirs = []
        self.base_path = env.get_variable("BASE_DIR")
        self.komga_base_path = env.get_variable("KOMGA_PATH")
        self.epub_base_path = env.get_variable("EPUB_PATH")
        self._temp_path = env.get_variable("TEMP_PATH")
        self._working_path = os.getcwd()
        working_dirs.append(self.komga_base_path)
        working_dirs.append(self.epub_base_path)
        working_dirs.append(self._temp_path)

        # dir operation
        for folder in working_dirs:
            os.makedirs(name = folder, exist_ok = True, mode = 0o777)

        # remove cache folders last longer than 1 day
        for root, dirs, _ in os.walk(self._temp_path):
            for temp_dir in dirs:
                path = os.path.join(root, temp_dir)
                folder_mod_time = os.path.getmtime(path)
                folder_mod_datetime = datetime.fromtimestamp(folder_mod_time)
                current_time = datetime.now()

                if current_time - folder_mod_datetime > timedelta(days = 1):
                    shutil.rmtree(path)

        # generated path
        self.manga_path = self._temp_path
        self._download_path = self._temp_path

    async def _task_handler(self, first_time = True, is_zip = False, is_epub = False):
        async def image_handler(session: aiohttp.ClientSession, url, image_path, retries = 5, delay = 3):
            async def write_image(response: aiohttp.ClientResponse, path) -> None:
                if os.path.exists(path) and os.path.getsize(path) != 0:
                    return

                async with aiofiles.open(path, 'wb') as f:
                    await f.write(await response.read())

            for attempt in range(retries):
                try:
                    async with session.get(url, headers = self._headers, proxy = self._proxy) as resp:
                        if resp.status == 200:
                            await write_image(resp, image_path)
                            return
                        else:
                            logger.warning(f"HTTP Status {resp.status} for {image_path}")
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    if attempt < retries - 1:
                        await asyncio.sleep(delay)

        async def create_queue():
            async def worker(queue: asyncio.Queue, session: aiohttp.ClientSession):
                while True:
                    img_num, url = await queue.get()

                    if url is None:
                        break

                    image_path = os.path.join(self._download_path, f'{img_num}.jpg')  # this is useful
                    await image_handler(session, url, image_path)  # use function
                    queue.task_done()

            q = asyncio.Queue()
            for rank, link in enumerate(self._image_url_list):
                q.put_nowait((rank, link))

            timeout = aiohttp.ClientTimeout(total = 10)
            async with aiohttp.ClientSession(timeout = timeout) as client:
                tasks = []

                for _ in range(self._thread):
                    task = asyncio.create_task(worker(q, client))
                    tasks.append(task)

                await q.join()

                for _ in range(self._thread):
                    q.put_nowait((None, None))

                await asyncio.gather(*tasks)

        zip_path = os.path.join(self.manga_path, self.title + '.zip')
        epub_path = os.path.join(self.manga_path, self.title + '.epub')

        if is_zip and os.path.exists(zip_path):
            logger.info(f"Skip existed file '{self.title}.zip'")
            return "Exist"

        if is_epub and os.path.exists(epub_path):
            logger.info(f"Skip existed file '{self.title}.epub'")
            return "Exist"

        if os.path.exists(self._download_path):
            if first_time:
                return "Downloaded"
            else:
                await create_queue()
                return
        else:
            os.mkdir(self._download_path)

        await create_queue()
        return

    async def _get_info_handler(self, retries = 3, delay = 5, is_zip = False, is_epub = False) -> str:
        async def regex(response: aiohttp.ClientResponse) -> list:
            # Regex: Full Title
            match = r'\*|\||\?|– Telegraph| |/|:'
            sub = {'*': '٭', '|': '丨', '?': '？', '– Telegraph': '', ' ': '', '/': 'ǀ', ':': '∶'}
            title_raw = BeautifulSoup(await response.text(), 'html.parser').find("title").text
            image_list = re.findall(r'img src="(.*?)"', await response.text())

            image_url_list = ['https://telegra.ph' + i for i in image_list]
            self.title_raw = re.sub(match, lambda x: sub[x.group()], title_raw)

            logger.info(f"Start job for '{self.title_raw}'")

            # Regex: Manga Title
            title_match = re.search(r'](.*?\(.*?\))', self.title_raw)

            if not title_match:
                title_match = re.search(r'](.*?)[(\[]', self.title_raw)

            if not title_match:
                title_match = re.search(r"](.*)", self.title_raw)

            self.title = title_match.group(1) if title_match else self.title_raw

            # Regex: Aritst
            artist_match = re.search(r'\[(.*?)(?:\((.*?)\))?]', self.title_raw)

            if artist_match:
                self.artist = artist_match.group(2) if artist_match.group(2) else artist_match.group(1)
            else:
                self.artist = 'その他'

            # Filter target path
            if self.artist in ['Fanbox', 'FANBOX', 'FanBox', 'Pixiv', 'PIXIV']:
                self.manga_path = os.path.join(self.komga_base_path, self.title)
            else:
                self.manga_path = os.path.join(self.komga_base_path, self.artist)

            if is_epub:
                self.manga_path = os.path.join(self.epub_base_path, self.artist)

            if is_zip:
                self.manga_path = os.path.join(self.komga_base_path, self.artist)

            self._download_path = os.path.join(self._temp_path, self.title)

            return image_url_list

        for attempt in range(retries):
            try:
                timeout = aiohttp.ClientTimeout(total = 10)
                async with aiohttp.ClientSession(timeout = timeout) as session:
                    async with session.get(
                            url = self.url,
                            headers = self._headers,
                            proxy = self._proxy
                    ) as resp:
                        if resp.status == 200:
                            self._image_url_list = await regex(resp)
                            return "OK"
                        else:
                            logger.error(f"HTTP Status {resp.status}, maybe article is missing?")
            except (aiohttp.ClientError, asyncio.TimeoutError):
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Info init failed")
                    return "ERROR"

    async def _process_handler(self, is_zip = False, is_epub = False) -> str:
        async def create_zip():
            output = os.path.join(self.manga_path, self.title) + '.zip'

            if not os.path.exists(self.manga_path):
                os.mkdir(self.manga_path)

            with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as output_zip:
                for root, _, files in os.walk(self._download_path):
                    if root == self._download_path:
                        relative_root = ''
                    else:
                        relative_root = root.replace(self._download_path, '') + os.sep

                    for filename in files:
                        output_zip.write(os.path.join(str(root), str(filename)), relative_root + filename)

            logger.info(f"Create zip '{output}'")

        async def create_epub():
            sorted_images = sorted([f for f in os.listdir(self._download_path) if
                                    os.path.isfile(os.path.join(self._download_path, f)) and str(f).endswith('.jpg')],
                                   key = lambda x: int(re.search(r'\d+', x).group()))
            async with aiofiles.open(os.path.join(self._download_path, sorted_images[0]), "rb") as f:
                manga_cover = await f.read()

            manga = epub.EpubBook()
            manga.set_title(self.title)
            manga.set_identifier('dariNirvana')
            manga.add_author(self.artist)
            manga.set_cover("cover.jpg", manga_cover)

            if "翻訳" or "汉化" or "中國" or "翻译" or "中文" or "中国" in self.title_raw:
                manga.set_language('zh')
            else:
                manga.set_language('ja')

            for i, image in enumerate(sorted_images):
                html = epub.EpubHtml(title = f"Page {i + 1}", file_name = f"image_{i + 1}.xhtml",
                                     content = f"<html><body><img src='{image}'></body></html>".encode('utf8'))
                async with aiofiles.open(os.path.join(self._download_path, image), "rb") as f:
                    image_content = await f.read()

                image = epub.EpubImage(uid = image, file_name = image, media_type = "image/jpeg",
                                       content = image_content)
                manga.add_item(image)
                manga.add_item(html)
                manga.spine.append(html)
                manga.toc.append(epub.Link(html.file_name, html.title, ''))

            manga.add_item(epub.EpubNav())
            manga.add_item(epub.EpubNcx())

            if not os.path.exists(self.manga_path):
                os.mkdir(self.manga_path)

            os.chdir(self.manga_path)
            epub.write_epub(self.title + '.epub', manga, {})
            os.chdir(self._working_path)
            logger.info(f"Create epub '{self.title + '.epub'}'")

        async def check_integrity(times = 1) -> str:
            if not os.path.exists(self._download_path):
                return "Empty"

            images = [file for file in os.listdir(self._download_path) if file.endswith(".jpg")]
            empty = [file for file in images if os.path.getsize(os.path.join(self._download_path, file)) == 0]

            if len(empty) != 0:
                logger.warning(f"There are {len(empty)} broken images from {self.title}, retrying {times}")
                await asyncio.sleep(10)
                await self._task_handler(first_time = False)
                await check_integrity(times = times + 1)

            return 'Completed'

        info_return = await self._get_info_handler(is_zip = is_zip, is_epub = is_epub)

        if info_return == "OK":
            task_return = await self._task_handler(is_zip = is_zip, is_epub = is_epub)

            if task_return == "Exist":
                return "OK"
            elif task_return == "Downloaded":
                if is_zip:
                    await create_zip()
                elif is_epub:
                    await create_epub()

                return "OK"
            else:
                check_return = await check_integrity()

                if check_return == "Empty":
                    return "OK"

                if check_return == 'Completed':
                    if is_zip:
                        await create_zip()
                    elif is_epub:
                        await create_epub()

                    return "OK"
        else:
            return "ERROR"

    # main functions being used
    async def get_epub(self):
        return await self._process_handler(is_epub = True)

    async def get_zip(self):
        return await self._process_handler(is_zip = True)

    async def get_info(self):
        return await self._get_info_handler()
