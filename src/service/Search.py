import asyncio
from typing import Any, Dict, Optional, List, ByteString, Tuple
from urllib import parse as urlparse

import aiohttp
from PicImageSearch import Ascii2D, Iqdb
from PicImageSearch import Network
from PicImageSearch.model import Ascii2DResponse, IqdbResponse, IqdbItem
from fake_useragent import UserAgent
from httpx import Proxy
from httpx import URL, AsyncClient


def parse_cookies(cookies_str: Optional[str] = None) -> Dict[str, str]:
    cookies_dict: Dict[str, str] = {}

    if cookies_str:
        for line in cookies_str.split(";"):
            key, value = line.strip().split("=", 1)
            cookies_dict[key] = value

    return cookies_dict


class AggregationSearch:
    def __init__(self, proxy: None | Proxy = None):
        self._proxy = proxy
        self._media_byte: ByteString = b''

        self.ascii2d_result: Dict = {}
        self.ascii2d_result_bovw: Dict = {}
        self.iqdb_result: Dict = {}

    async def get_media(self, url: str, cookies: Optional[str] = None):
        _url: URL = URL(url)
        _referer: str = f"{_url.scheme}://{_url.host}/"
        _default_headers: Dict = {"User-Agent": UserAgent().random}
        headers: Dict = {"Referer": _referer, **_default_headers}

        async with AsyncClient(
                headers = headers, cookies = parse_cookies(cookies),
                proxies = self._proxy, follow_redirects = True
        ) as client:
            resp = await client.get(_url)

            if resp.status_code != 200:
                return None

            self._media_byte = resp.content

            return b'Fetched'

    async def _search_with_type(
            self,
            url: str,
            function,
            client_class,
            _retry = False) -> Tuple[Any] | Dict | None:

        async with Network(proxies = self._proxy) as client:
            search_instance = client_class(client = client)

            if not self._media_byte:
                if not await self.get_media(url = url):
                    if not _retry:
                        await self._search_with_type(url, function, client_class, _retry = True)

                    raise aiohttp.ClientError

            results = await function(search_instance, file = self._media_byte)

            if not results.raw:
                return None

            if client_class == Ascii2D:
                resp_text, resp_url, _ = await search_instance.get(results.url.replace("/color/", "/bovw/"))
                bovw_results = Ascii2DResponse(resp_text, resp_url)
                tasks = [self._format_ascii2d_result(bovw_results, True),
                         self._format_ascii2d_result(results)]
                return await asyncio.gather(*tasks)  # always return tuple

            if client_class == Iqdb:
                return await self._format_iqdb_result(results)  # none or dict

    async def _format_iqdb_result(self, resp: IqdbResponse):
        selected_res: IqdbItem = resp.raw[0]
        danbooru_res: List[IqdbItem] = [i for i in resp.raw if i.source == "Danbooru"]
        yandere_res: List[IqdbItem] = [i for i in resp.raw if i.source == "yande.re"]

        if danbooru_res:
            selected_res = danbooru_res[0]
        elif yandere_res:
            selected_res = yandere_res[0]

        if selected_res.similarity < 85.0:
            return None

        self.iqdb_result["class"] = "iqdb"
        self.iqdb_result["url"] = selected_res.url
        self.iqdb_result["similarity"] = selected_res.similarity
        self.iqdb_result["thumbnail"] = selected_res.thumbnail
        self.iqdb_result["content"] = selected_res.content
        self.iqdb_result["source"] = selected_res.source

        return self.iqdb_result

    async def _format_ascii2d_result(self, resp: Ascii2DResponse, bovw: bool = False):

        target: Dict = self.ascii2d_result_bovw if bovw else self.ascii2d_result

        for i, r in enumerate(resp.raw):
            if not (r.title or r.url_list):
                continue

            r.author = "None" if r.author == '' else r.author
            target[i - 1] = {}
            target[i - 1]["class"] = "ascii2d"
            target[i - 1]["url"] = r.url
            target[i - 1]["author"] = r.author
            target[i - 1]["author_url"] = r.author_url
            target[i - 1]["thumbnail"] = r.thumbnail

            if i == 3:
                break

    async def iqdb_search(self, url: str, _retry = False) -> Dict | None:
        if not await self._search_with_type(url, Iqdb.search, Iqdb, _retry):
            return None

        return self.iqdb_result

    async def ascii2d_search(self, url, _retry = False) -> Dict | None:
        if not await self._search_with_type(url, Ascii2D.search, Ascii2D, _retry):
            return None

        for i in range(len(self.ascii2d_result)):
            if not self.ascii2d_result[i]["url"]:
                return None

            if self.ascii2d_result[i]["url"] == self.ascii2d_result_bovw[i]["url"]:
                return self.ascii2d_result[i]

    async def aggregation_search(self, url: str) -> Dict | None:
        result = await self.iqdb_search(url)

        if not result:
            return await self.ascii2d_search(url)
        else:
            return result


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
