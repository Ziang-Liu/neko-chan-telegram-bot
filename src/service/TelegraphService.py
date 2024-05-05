import concurrent.futures
import os.path
import re
import shutil
import zipfile
from uuid import uuid4

import requests
from bs4 import BeautifulSoup
from ebooklib import epub
from fake_useragent import UserAgent

from src.bot.Environment import EnvironmentReader
from src.utils.LoggerUtil import logger


class Telegraph:
    def __init__(self):
        env = EnvironmentReader()
        env.print_env()
        # basic params
        proxy_url = env.get_variable("HTTP_PROXY")
        self.url = "https://telegra.ph/"
        self.full_title = "None"
        self.manga_title = "None"
        self.artist_name = "None"
        self._headers = {'User-Agent': UserAgent().random}
        self._threads = env.get_variable("TELEGRAPH_MAX_THREAD")
        self._proxy = {"http": proxy_url, "https": proxy_url}
        # working dirs
        self.komga_folder = env.get_variable("KOMGA_PATH")
        self.epub_folder = env.get_variable("EPUB_PATH")
        self._temp_folder = env.get_variable("TEMP_PATH")
        self._deprecated_folder = env.get_variable("DEPRECATED_PATH")
        self._target_manga_path = self._temp_folder
        self._temp_download_path = os.path.join(self._temp_folder, str(uuid4()))
        self._current_working_dir = os.getcwd()
        # specific params
        self._is_epub = False
        self._is_zip = False
        # create basic dirs
        for folder in [self.komga_folder, self.epub_folder, self._temp_folder, self._deprecated_folder]:
            os.makedirs(name = folder, exist_ok = True, mode = 0o777)

    def _create_download_thread(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers = self._threads) as executor:
            futures = {
                executor.submit(self._image_downloader, url, os.path.join(self._temp_download_path, f'{i}.jpg'), 3):
                    url for i, url in enumerate(self._image_url_list)
            }

            for future in concurrent.futures.as_completed(futures):
                future.result()
                return True

    def _create_download_task(self):
        if self._is_zip:
            if os.path.exists(os.path.join(self._target_manga_path, self.manga_title + '.zip')):
                return

        if self._is_epub:
            if os.path.exists(os.path.join(self._target_manga_path, self.manga_title + '.epub')):
                return

        if not os.path.exists(self._target_manga_path):
            os.mkdir(self._target_manga_path)

        if not os.path.exists(self._temp_download_path):
            os.mkdir(self._temp_download_path)

        if self._create_download_thread():
            return 'FINISH'
        else:
            return 'ERROR'

    def _telegraph_basic_info_init(self, retry):
        if retry != 0:
            requested_url = requests.get(self.url, headers = self._headers, proxies = self._proxy)

            if requested_url.status_code == 200:
                self._get_image_url_list(requested_url.text)
                self.full_title = re.sub(
                    r'\*|\||\?|– Telegraph| |/|:',
                    lambda x: {'*': '٭', '|': '丨', '?': '？', '– Telegraph': '',
                               ' ': '', '/': '∕', ':': '∶'}[x.group()],
                    BeautifulSoup(requested_url.text, 'html.parser').find("title").text)

                try:
                    self.manga_title = re.search(r'](.*?)[(\[]', self.full_title).group(1)
                except AttributeError:
                    try:
                        self.manga_title = re.search(r"](.*)", self.full_title).group(1)
                    except AttributeError:
                        self.manga_title = self.full_title

                try:
                    self.artist_name = re.search(
                        r'\((.*?)\)', re.search(r'\[(.*?)]', self.full_title).group(1)).group(1)
                except AttributeError:
                    try:
                        re.search(r'\[(.*?)]', self.full_title).group(1)
                    except AttributeError:
                        self.artist_name = 'その他'

                if self.artist_name in ['Fanbox', 'FANBOX', 'FanBox', 'Pixiv', 'PIXIV']:
                    self._target_manga_path = os.path.join(self.komga_folder, self.manga_title)
                else:
                    self._target_manga_path = os.path.join(self.komga_folder, self.artist_name)

                if self._is_epub:
                    self._target_manga_path = os.path.join(self.epub_folder, self.artist_name)

                if self._is_zip:
                    self._target_manga_path = os.path.join(self.komga_folder, self.artist_name)

                return True

            self._telegraph_basic_info_init(retry - 1)

        return False

    def _image_downloader(self, url, image_path, retry):
        if os.path.exists(image_path):
            return

        if retry != 0:
            requested_url = requests.get(url, headers = self._headers, proxies = self._proxy)

            if requested_url.status_code == 200:
                with open(image_path, 'wb') as f:
                    for chunk in requested_url.iter_content(chunk_size = 128):
                        f.write(chunk)

                return

            self._image_downloader(url, image_path, retry - 1)

    def _check_integrity(self):
        image_list = len([file for file in os.listdir(self._temp_download_path) if file.endswith(".jpg")])

        if self._ideal_image_count - image_list in range(1, 11):
            logger.warning(f"Find {self.manga_title} missing {self._ideal_image_count - image_list} images, "
                           f"try to download again")

            self._create_download_thread()
            self._check_integrity()

        if self._ideal_image_count - image_list > 10:
            logger.error(f"Downloaded images from '{self.full_title}' "
                         f"are very corrupt which beyond the scope of compensation, "
                         f"missing {self._ideal_image_count - image_list} images")

            return False
        else:
            return True

    def _get_image_url_list(self, text):
        self._image_url_list = []
        start = 0

        while True:
            start = text.find('img src="', start)

            if start == -1:
                break

            start += 9
            end = text.find('"', start)

            if end == -1:
                break

            self._image_url_list.append('https://telegra.ph' + text[start:end])
            start = end

        self._ideal_image_count = len(self._image_url_list)

    def _create_zip(self):
        output = os.path.join(self._target_manga_path, self.manga_title) + '.zip'

        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as output_zip:
            for root, _, files in os.walk(self._temp_download_path):
                if root == self._temp_download_path:
                    relative_root = ''
                else:
                    relative_root = root.replace(self._temp_download_path, '') + os.sep

                for filename in files:
                    if ".jpg" in filename:
                        output_zip.write(os.path.join(str(root), str(filename)), relative_root + filename)

        output_zip.close()
        shutil.rmtree(self._temp_download_path)

        logger.info(f"Create zip '{output}'")

    def _create_epub(self):
        sorted_images = sorted([f for f in os.listdir(self._temp_download_path) if
                                os.path.isfile(os.path.join(self._temp_download_path, f)) and str(f).endswith('.jpg')],
                               key = lambda x: int(re.search(r'\d+', x).group()))
        manga_cover = open(os.path.join(self._temp_download_path, sorted_images[0]), "rb").read()

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
            image = epub.EpubImage(uid = image, file_name = image, media_type = "image/jpeg",
                                   content = open(os.path.join(self._temp_download_path, image), "rb").read())

            manga.add_item(image)
            manga.add_item(html)
            manga.spine.append(html)
            manga.toc.append(epub.Link(html.file_name, html.title, ''))

        manga.add_item(epub.EpubNav())
        manga.add_item(epub.EpubNcx())

        os.chdir(self._target_manga_path)
        epub.write_epub(self.manga_title + '.epub', manga, {})
        os.chdir(self._current_working_dir)
        shutil.rmtree(self._temp_download_path)

        logger.info(f"Create epub '{self.manga_title + '.epub'}'")

    def _start_process(self):
        if self._is_zip:
            self._target_function = self._create_zip
        elif self._is_epub:
            self._target_function = self._create_epub

        if self._telegraph_basic_info_init(3):
            if self._create_download_task() == 'FINISH':
                if self._check_integrity():
                    self._target_function()
                else:
                    shutil.move(self._temp_folder, self._deprecated_folder)
            elif self._create_download_task() == 'ERROR':
                logger.error(f"Create download task failed")
            else:
                logger.info(f'Skip existed file {self.manga_title}')
        else:
            logger.error("Fetch telegraph basic info failed")

    def pack_to_epub(self):
        self._is_epub = True
        self._start_process()

    def sync_to_library(self):
        self._is_zip = True
        self._start_process()

    def get_basic_info(self):
        self._telegraph_basic_info_init(3)
