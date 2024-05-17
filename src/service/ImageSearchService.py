from urllib import parse as urlparse

import aiohttp
from PicImageSearch import Iqdb, Network
from PicImageSearch.model import IqdbResponse

from src.utils.LoggerUtil import logger


class AggregationSearch:
    def __init__(self):
        self.url: str | None = None
        self.similarity: float | None = None
        self.image_size: str | None = None
        self.source: str | None = None

    def _iqdb_result(self, resp: IqdbResponse):
        self.url = resp.raw[0].url
        self.similarity = resp.raw[0].similarity
        self.image_size = resp.raw[0].size
        self.source = resp.raw[0].source

    async def iqdb_search(self, url, proxy = None, _retry = 3):
        if _retry == 0:
            raise ConnectionError('Max retries exceeded')

        try:
            async with Network(proxies = proxy) as client:
                search_result = await Iqdb(client = client).search(url = url)
                self._iqdb_result(search_result)
        except Exception as e:
            logger.warning(e)
            await self.iqdb_search(url, proxy, _retry - 1)


class TraceMoe:
    """
    I just write support for url input, image upload seems no usage situations
    """

    def __init__(self):
        self._base = "https://api.trace.moe"
        self._default_api = "https://api.trace.moe/search?url={}"
        self._api_cb = "https://api.trace.moe/search?cutBorders&url={}"
        self._api_al = "https://api.trace.moe/search?anilistInfo&url={}"
        self.resp: dict | None = None

    async def _error_handler(self):
        if self.resp.get("error"):
            raise Exception(self.resp["error"])

    async def _check_connection(self, session, proxy = None):
        async with session.get(self._base, proxy = proxy) as resp:
            if resp.status != 200:
                raise ConnectionError(resp.status)

    async def _search(self, url, api_url, proxy = None):
        async with aiohttp.ClientSession() as session:
            await self._check_connection(session, proxy)

            async with session.get(api_url.format(urlparse.quote_plus(url)), proxy = proxy) as resp:
                self.resp = await resp.json()
                await self._error_handler()

                return self.resp['result']

    async def default(self, url, proxy = None):
        return await self._search(url, self._default_api, proxy)

    async def cut_black_borders(self, url, proxy = None):
        return await self._search(url, self._api_cb, proxy)

    async def include_anilist(self, url, proxy = None):
        return await self._search(url, self._api_al, proxy)
