import urllib.parse as urlparse

import requests
from PicImageSearch import Iqdb, Network
from PicImageSearch.model import IqdbResponse

from src.utils.LoggerUtil import logger


class AggregationSearch:
    def __init__(self):
        self.url = "None"
        self.similarity = -1.0
        self.image_size = "None"
        self.source = "None"

    def _iqdb_result(self, resp: IqdbResponse):
        self.url = resp.raw[0].url
        self.similarity = resp.raw[0].similarity
        self.image_size = resp.raw[0].size
        self.source = resp.raw[0].source

    async def iqdb_search(self, url, proxy = None, _retry = 3):
        if _retry != 0:
            if requests.get(url, proxies = proxy).status_code == 200:
                async with Network(proxies = proxy) as client:
                    search_result = await Iqdb(client = client).search(url = url)
                    self._iqdb_result(search_result)
            else:
                await self.iqdb_search(url, proxy, _retry - 1)

        logger.error(f"iqdb search failed for url {url}")


class TraceMoe:
    def __init__(self):
        self._base = "https://api.trace.moe/search"
        self._base_api = "https://api.trace.moe/search?url={}"
        self._base_api_with_cb = "https://api.trace.moe/search?cutBorders&url={}"
        self._base_api_with_al = "https://api.trace.moe/search?anilistInfo&url={}"
        self.resp = {}

    def _error_handler(self):
        if self.resp["error"] == "":
            logger.error(self.resp["error"])
            self.resp["error"] = "ERROR"

    def _check_connection(self, proxy = None):
        if requests.get(self._base, proxies = proxy).status_code != 200:
            logger.error(f"Failed connect to {self._base}")
            return False
        return True

    def search_by_url(self, url, proxy = None):
        if self._check_connection(proxy):
            self.resp = requests.get(self._base_api.format(urlparse.quote_plus(url)), proxies = proxy).json()
            self._error_handler()

    def search_by_url_cb(self, url, proxy = None):
        if self._check_connection(proxy):
            self.resp = requests.get(self._base_api_with_cb.format(urlparse.quote_plus(url)), proxies = proxy).json()
            self._error_handler()

    def search_by_url_al(self, url, proxy = None):
        if self._check_connection(proxy):
            self.resp = requests.get(self._base_api_with_al.format(urlparse.quote_plus(url)), proxies = proxy).json()
            self._error_handler()
