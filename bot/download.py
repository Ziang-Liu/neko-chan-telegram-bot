import concurrent.futures
import os.path
import re
import shutil
import zipfile
from functools import partial

import requests
from bs4 import BeautifulSoup
from ebooklib import epub
from fake_useragent import UserAgent

from env import *
from logger import logger


def _get_pic_url(text) -> list:
    urls = []
    start = 0

    while True:
        start = text.find('img src="', start)
        if start == -1:
            break

        start += 9
        end = text.find('"', start)

        if end == -1:
            break

        urls.append(text[start:end])
        start = end

    return urls


def _get_pic(url, file_path, proxy):
    if os.path.exists(file_path):
        return

    retry = 0

    while retry < 2:
        try:
            requested_url = requests.get(url, proxies = proxy, timeout = 1)
            if requested_url.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in requested_url.iter_content(chunk_size = 128):
                        f.write(chunk)

                break
        except requests.exceptions.RequestException as e:
            logger.error(e)
            retry += 1

    return


def _zip_folder(path, output = None):
    """
    Behavior:
    "~/testmanga/img(num).jpg..." ->
    "~/testmanga/testmanga.zip"
    """
    file_list: list = os.listdir(path)
    output: str = output or os.path.basename(path) + '.zip'

    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as output_zip:
        for root, _, files in os.walk(path):
            relative_root = '' if root == path else root.replace(path, '') + os.sep
            for filename in files:
                if ".jpg" in filename:
                    output_zip.write(os.path.join(str(root), str(filename)), relative_root + filename)

    output_zip.close()
    [os.remove(os.path.join(path, image)) for image in file_list if ".jpg" in image]
    logger.info(f"Create zip '{output}'")


def _create_epub(manga_title: str, img_path: str, epub_path: str, exist_zip = False):
    """
    JUST PUT IMAGES AND RELATED PATH
    IT CAN PACK IMAGES IN ORDER INTO EPUB FILE
    MAGIC
    """
    manga = epub.EpubBook()
    manga.set_title(manga_title)
    manga.set_identifier('tairitsucat')
    manga.add_author('t2kf')
    manga.set_language('zh')

    image_files = sorted([f for f in os.listdir(img_path) if
                          os.path.isfile(os.path.join(img_path, f)) and str(f).endswith('.jpg')],
                         key = lambda x: int(re.search(r'\d+', x).group()))

    if image_files:
        manga.set_cover("cover.jpg", open(os.path.join(img_path, image_files[0]), "rb").read())

    for i, image_file in enumerate(image_files):
        manga.add_item(epub.EpubImage(uid = image_file, file_name = image_file, media_type = "image/jpeg",
                                      content = open(os.path.join(img_path, image_file), "rb").read()))
        html = epub.EpubHtml(title = f"Image {i + 1}", file_name = f"image_{i + 1}.xhtml",
                             content = f"<html><body><img src='{image_file}'></body></html>".encode('utf8'))
        manga.add_item(html)
        manga.spine.append(html)
        manga.toc.append(epub.Link(html.file_name, html.title, ''))

    manga.add_item(epub.EpubNav()).add_item(epub.EpubNcx())
    epub.write_epub(manga_title + '.epub', manga, {})

    if not exist_zip:
        shutil.rmtree(os.path.join(epub_path, manga_title))
    else:
        [os.remove(os.path.join(img_path, image)) for image in os.listdir(img_path) if ".jpg" in image]

    logger.info(f"Create epub '{manga_title + '.epub'}'")


class TelegraphDownloader:
    def __init__(self):
        self.proxy: dict[str, str | None] = {"http": PROXY_URL, "https": PROXY_URL}
        self.threads: int = int(DOWNLOAD_THREADS)
        self.download_path: str = DOWNLOAD_PATH
        self.url: str = ''
        self.title: str = ''
        self._target_path: str = ''
        self._is_epub: bool = False
        self._is_zip: bool = False
        self._exist_zip: bool = False

    def _init_pic(self):
        if not os.path.exists(self._target_path):
            logger.info(f"Create dir at '{self._target_path}'")
            os.mkdir(self._target_path)
        else:
            logger.info(f"Skip existed dir '{self._target_path}'")
            exist_zip = os.path.join(self._target_path, self.title + '.zip')
            exist_epub = os.path.join(self.download_path, self.title + '.epub')

            if os.path.exists(exist_zip):
                self._exist_zip = True

                if not self._is_epub:
                    logger.info(f"Skip existed zip '{self.title + '.zip'}")

                    return False

            if os.path.exists(exist_epub):
                if not self._is_zip:
                    logger.info(f"Skip existed epub '{self.title + '.epub'}")

                    return False

        os.chdir(self._target_path)

        with concurrent.futures.ThreadPoolExecutor(max_workers = self.threads) as executor:
            future_to_url = {
                executor.submit(partial(_get_pic, proxy = self.proxy),
                                'https://telegra.ph' + url, f'img{i}.jpg'): url
                for i, url in enumerate(self._image_urls)}

            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    future.result()

                    return True
                except Exception as e:
                    logger.error(f"{e}")

    def _init_data(self):
        if "telegra.ph" not in self.url:
            logger.error(f'DOWNLOAD MODULE: Detect wrong link {self.url}')

            return False

        if not os.path.isdir(self.download_path):
            logger.error(f"Invalid path for '{self.download_path}'")

            return False

        retry = 0

        while retry < 3:
            try:
                headers = {'User-Agent': UserAgent().random}
                requested_url = requests.get(self.url, headers = headers, proxies = self.proxy, timeout = 3)

                if requested_url.status_code == 200:
                    self._image_urls = _get_pic_url(requested_url.text)
                    self._image_count = len(self._image_urls)
                    self.title = re.sub(
                        r'<title>|</title>|\*|\||\?|– Telegraph| |/|:',
                        lambda x: {'<title>': '', '</title>': '', '*': '', '|': '', '?': '',
                                   '– Telegraph': '', ' ': '', '/': '∕', ':': '∶'}[x.group()],
                        str(BeautifulSoup(requested_url.text, 'html.parser').find("title"))
                    )
                    self._target_path = os.path.join(self.download_path, self.title)

                    return True

            except requests.exceptions.RequestException as e:
                logger.error(e)
                retry += 1

        return False

    def _check_integrity(self):
        if len([file for file in os.listdir(self._target_path) if file.endswith(".jpg")]) != self._image_count:
            logger.error(f"Images in '{self._target_path}' are broken")

            return False

        return True

    def pack_zip(self):
        if self._init_data():
            self._is_zip = True
            if self._init_pic():
                if self._check_integrity():
                    _zip_folder(self._target_path)
                    os.chdir(self.download_path)

    def pack_epub(self):
        if self._init_data():
            self._is_epub = True
            if self._init_pic():
                if self._check_integrity():
                    os.chdir(self.download_path)
                    _create_epub(self.title, self._target_path, self.download_path, self._exist_zip)

    def get_title(self):
        self._init_data()
