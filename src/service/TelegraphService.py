import concurrent.futures
import os.path
import re
import shutil
import urllib.request
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
        # manga params
        self.full_title = "None"
        self.manga_title = "None"
        self.artist_name = 'その他'
        # network params
        proxy = env.get_variable("HTTP_PROXY")
        self._headers = {'User-Agent': UserAgent().random}
        self._proxy = {'https': proxy, 'http': proxy}
        self._threads = env.get_variable("TELEGRAPH_MAX_THREAD")
        # setup proxy service
        handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(handler)
        urllib.request.install_opener(opener)
        # working dir
        working_dirs = []
        self.komga_folder = env.get_variable("KOMGA_PATH")
        working_dirs.append(self.komga_folder)
        self.epub_folder = env.get_variable("EPUB_PATH")
        working_dirs.append(self.epub_folder)
        self._temp_folder = env.get_variable("TEMP_PATH")
        working_dirs.append(self._temp_folder)
        self._deprecated_folder = env.get_variable("DEPRECATED_PATH")
        working_dirs.append(self._deprecated_folder)
        self._current_working_dir = os.getcwd()
        # create basic dirs
        for folder in working_dirs:
            os.makedirs(name = folder, exist_ok = True, mode = 0o777)
        # generated path
        self.manga_path = self._temp_folder
        self._download_path = os.path.join(self._temp_folder, str(uuid4()))
        # generate preference
        self._is_epub = False
        self._is_zip = False

    def _create_download_thread(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers = self._threads) as executor:
            for i, url in enumerate(self._image_url_list):
                image_path = os.path.join(self._download_path, f'{i}.jpg')
                executor.submit(self._image_downloader, url, image_path, 3)

    def _create_download_task(self):
        zip_path = os.path.join(self.manga_path, self.manga_title + '.zip')
        epub_path = os.path.join(self.manga_path, self.manga_title + '.epub')

        if self._is_zip and os.path.exists(zip_path):
            return "Exist ZIP"

        if self._is_epub and os.path.exists(epub_path):
            return "Exist EPUB"

        if not os.path.exists(self.manga_path):
            os.mkdir(self.manga_path)

        if not os.path.exists(self._download_path):
            os.mkdir(self._download_path)

        self._create_download_thread()

    def _info_init(self, url: str, _retry = 3):
        if _retry != 0:
            resp = requests.get(url = url, headers = self._headers, proxies = self._proxy)

            if resp.status_code == 200:
                # get full title
                pattern = r'\*|\||\?|– Telegraph| |/|:'
                title = BeautifulSoup(resp.text, 'html.parser').find("title").text
                sub = {'*': '٭', '|': '丨', '?': '？', '– Telegraph': '', ' ': '', '/': 'ǀ', ':': '∶'}
                self._get_image_url_list(resp.text)
                self.full_title = re.sub(pattern, lambda x: sub[x.group()], title)
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
                    self.artist_name = artist_match.group(2) if artist_match.group(2) else artist_match.group(1)
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

                return

            self._info_init(url, _retry - 1)

        raise TimeoutError

    def _image_downloader(self, url, image_path, _retry) -> None:
        if os.path.exists(image_path):
            return

        if _retry != 0:
            resp = requests.get(url, headers = self._headers, proxies = self._proxy)

            if resp.status_code == 200:
                with open(image_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size = 128):
                        f.write(chunk)
                return

            self._image_downloader(url, image_path, _retry - 1)

    def _check_integrity(self) -> str:
        image_list = len([file for file in os.listdir(self._download_path) if file.endswith(".jpg")])

        if self._ideal_image_count - image_list in range(1, 11):
            logger.warning(f"Find {self.manga_title} missing {self._ideal_image_count - image_list} images, "
                           f"try to download again")
            self._create_download_thread()
            self._check_integrity()

        if self._ideal_image_count - image_list > 10:
            logger.error(f"Downloaded images from '{self.full_title}' "
                         f"are very corrupt which beyond the scope of compensation, "
                         f"missing {self._ideal_image_count - image_list} images")
            return 'Deprecated'

        return 'Completed'

    def _get_image_url_list(self, text):
        self._image_url_list = re.findall(r'img src="(.*?)"', text)
        self._image_url_list = ['https://telegra.ph' + url for url in self._image_url_list]
        self._ideal_image_count = len(self._image_url_list)

    def _create_zip(self):
        output = os.path.join(self.manga_path, self.manga_title) + '.zip'

        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as output_zip:
            for root, _, files in os.walk(self._download_path):
                if root == self._download_path:
                    relative_root = ''
                else:
                    relative_root = root.replace(self._download_path, '') + os.sep

                for filename in files:
                    if ".jpg" in filename:
                        output_zip.write(os.path.join(str(root), str(filename)), relative_root + filename)

        output_zip.close()
        shutil.rmtree(self._download_path)

        logger.info(f"Create zip '{output}'")

    def _create_epub(self):
        sorted_images = sorted([f for f in os.listdir(self._download_path) if
                                os.path.isfile(os.path.join(self._download_path, f)) and str(f).endswith('.jpg')],
                               key = lambda x: int(re.search(r'\d+', x).group()))
        manga_cover = open(os.path.join(self._download_path, sorted_images[0]), "rb").read()

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
                                   content = open(os.path.join(self._download_path, image), "rb").read())

            manga.add_item(image)
            manga.add_item(html)
            manga.spine.append(html)
            manga.toc.append(epub.Link(html.file_name, html.title, ''))

        manga.add_item(epub.EpubNav())
        manga.add_item(epub.EpubNcx())

        os.chdir(self.manga_path)
        epub.write_epub(self.manga_title + '.epub', manga, {})
        os.chdir(self._current_working_dir)
        shutil.rmtree(self._download_path)

        logger.info(f"Create epub '{self.manga_title + '.epub'}'")

    def _start_process(self, url: str):
        if self._is_zip:
            self._target_function = self._create_zip
        elif self._is_epub:
            self._target_function = self._create_epub

        self._info_init(url)

        if self._create_download_task() == "Exist ZIP":
            logger.info(f"Skip existed file '{self.manga_title}.zip'")
            return
        elif self._create_download_task() == "Exist Epub":
            logger.info(f"Skip existed file '{self.manga_title}.epub'")
            return

        if self._check_integrity() == 'Completed':
            self._target_function()
        elif self._check_integrity() == 'Deprecated':
            shutil.move(self._temp_folder, self._deprecated_folder)

    def pack_to_epub(self, url: str):
        self._is_epub = True
        self._start_process(url)

    def sync_to_library(self, url: str):
        self._is_zip = True
        self._start_process(url)

    def get_basic_info(self, url: str):
        self._info_init(url)
