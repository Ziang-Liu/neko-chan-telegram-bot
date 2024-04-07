import concurrent.futures
import re
import shutil
import zipfile
from functools import partial

import requests
from bs4 import BeautifulSoup
from ebooklib import epub
from fake_useragent import UserAgent

from src.logger import logger
from src.bot.env import *


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
            requested_url = requests.get(url, proxies = proxy, timeout = 10)
            if requested_url.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in requested_url.iter_content(chunk_size = 128):
                        f.write(chunk)
                break
        except requests.exceptions.RequestException:
            logger.error(f"Timeout with url '{url}'")
            retry += 1

    if retry == 2:
        return


def _check_integrity(folder_path, file_count):
    files = os.listdir(folder_path)

    if len(files) != file_count:
        return False

    return True


def _zip_folder(path, output = None):
    """
    Behavior:
    "~/telegraphlib/download/testmanga/imgxxx.jpg..." ->
    "~/telegraphlib/download/testmanga/testmanga.zip"
    """
    file_list: list = os.listdir(path)
    output: str = output or os.path.basename(path) + '.zip'

    if os.path.exists(output):
        [os.remove(os.path.join(path, image)) for image in file_list if ".jpg" in image]
        return

    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as output_zip:
        for root, _, files in os.walk(path):
            relative_root = '' if root == path else root.replace(path, '') + os.sep
            for filename in files:
                if ".jpg" in filename:
                    output_zip.write(os.path.join(str(root), str(filename)), relative_root + filename)

    output_zip.close()
    [os.remove(os.path.join(path, image)) for image in file_list if ".jpg" in image]
    logger.info(f"Create zip '{output}'")


def _create_epub(manga_title: str, img_path: str, epub_path: str):
    """
    YOU DO NOT NEED TO KNOW HOW IT WORKS
    JUST PUT IMAGES AND RELATED PATH
    AND IT CAN GENERATE EPUB FILES IN A FLASH
    IT IS MAGIC
    """
    manga = epub.EpubBook()
    manga.set_title(manga_title)
    manga.set_identifier('tairitsucat')
    manga.add_author('t2kf')
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
    os.chdir(epub_path)
    epub.write_epub(manga_title + '.epub', manga, {})
    shutil.rmtree(os.path.join(epub_path, manga_title))
    logger.info(f"Create epub '{manga_title + '.epub'}'")


def _init_data(url: str, download_path: str, proxy: str, threads: int) -> tuple[str, str, int] | None:
    headers = {'User-Agent': UserAgent().random}

    if "telegra.ph" not in url:
        logger.warning(f'DOWNLOAD MODULE: Detect wrong link {url}')
        return

    retry = 0
    while retry < 3:
        try:
            requested_url = requests.get(url, headers = headers, proxies = proxy, timeout = 10)
            if requested_url.status_code == 200:
                image_urls: list = _get_pic_url(requested_url.text)
                image_count: int = len(image_urls)
                soup = BeautifulSoup(requested_url.text, 'html.parser')
                converted_title: str = re.sub(
                    r'<title>|</title>|\*|\||\?|– Telegraph| |/|:',
                    lambda x: {'<title>': '', '</title>': '', '*': '', '|': '', '?': '',
                               '– Telegraph': '', ' ': '', '/': '∕', ':': '∶'}[x.group()],
                    str(soup.find("title"))
                )
                target_path = os.path.join(download_path, converted_title)
                break
        except requests.exceptions.RequestException:
            logger.error(f"Timeout with url '{url}', retrying...")
            retry += 1

    if retry == 2:
        logger.error("Reach max retries, quit")
        return

    if not os.path.isdir(download_path):
        logger.error(f"Invalid path for '{download_path}'")
        return

    if not os.path.exists(target_path):
        os.mkdir(target_path)
        logger.info(f"Create dir at '{target_path}'")
    else:
        logger.info(f"Skip existed dir '{target_path}'")

    os.chdir(target_path)

    with concurrent.futures.ThreadPoolExecutor(max_workers = threads) as executor:
        future_to_url = {executor.submit(
            partial(_get_pic, proxy = proxy), 'https://telegra.ph' + url, f'img{i}.jpg'): url
                         for i, url in enumerate(image_urls)}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]

    os.chdir(download_path)

    return converted_title, target_path, image_count


class TelegraphDownloader:
    def __init__(self):
        try:
            self.proxy = {"http": PROXY_URL, "https": PROXY_URL}
            self.threads = int(DOWNLOAD_THREADS)
        except (ValueError, TypeError):
            self.proxy = None
            self.threads = 4
        self.download_path = DOWNLOAD_PATH
        self.url = ''

    def pack_zip(self):
        _, path, count = _init_data(self.url, self.download_path, self.proxy, self.threads)
        if _check_integrity(path, count):
            os.chdir(path)
            _zip_folder(path)
            os.chdir(self.download_path)
            return 0
        else:
            logger.error(f"Images in '{path}' is broken")
            return 114514

    def pack_epub(self):
        title, path, count = _init_data(self.url, self.download_path, self.proxy, self.threads)
        if _check_integrity(path, count):
            _create_epub(title, path, self.download_path)
            return 0
        else:
            logger.error(f"Images in '{path}' is broken")
            return 114514
