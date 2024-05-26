import asyncio
from httpx import Proxy
from typing import (
    Dict,
    Optional, Any, )
from urllib import parse as urlparse

import aiohttp
from PicImageSearch import Ascii2D
from PicImageSearch import Network
from PicImageSearch.model import Ascii2DResponse
from fake_useragent import UserAgent
from httpx import URL, AsyncClient

from src.utils.Logger import logger


def parse_cookies(cookies_str: Optional[str] = None) -> Dict[str, str]:
    cookies_dict: Dict[str, str] = {}

    if cookies_str:
        for line in cookies_str.split(";"):
            key, value = line.strip().split("=", 1)
            cookies_dict[key] = value

    return cookies_dict


class AggregationSearch:
    def __init__(self, proxy: None | Proxy = None):
        self.preview_link = str()
        self.results = dict()
        self._proxy = proxy
        self.image_raw: bytes | int = bytes()
        self.ascii2d_result = dict()
        self.ascii2d_result_bovw = dict()
        self.saucenao_db = {
            "all": 999,
            "pixiv": 5,
            "danbooru": 9,
            "anime": [21, 22],
            "doujin": [18, 38],
            "fakku": 16,
        }

    async def get_media_bytes(self, url: str, cookies: Optional[str] = None) -> int:
        _url = URL(url)
        referer = f"{_url.scheme}://{_url.host}/"
        default_headers = {"User-Agent": UserAgent().random}
        headers = {"Referer": referer, **default_headers}

        async with AsyncClient(
                headers = headers, cookies = parse_cookies(cookies),
                proxies = self._proxy, follow_redirects = True
        ) as client:
            resp = await client.get(_url)

            if resp.status_code >= 400:
                return resp.status_code

        self.image_raw = resp.content

        return 200

    async def _format_ascii2d_result(self, resp: Ascii2DResponse, bovw: bool = False):
        target_dict = self.ascii2d_result_bovw if bovw else self.ascii2d_result

        for i, r in enumerate(resp.raw):
            if not (r.title or r.url_list):
                continue

            r.author = "None" if r.author == '' else r.author
            target_dict[i - 1] = dict()
            target_dict[i - 1]["url"] = r.url
            target_dict[i - 1]["author"] = r.author
            target_dict[i - 1]["author_url"] = r.author_url
            target_dict[i - 1]["thumbnail"] = r.thumbnail

            if i == 3:
                break

    async def ascii2d_search(self, url, _retry = False) -> dict[Any] | None:
        async with Network(proxies = self._proxy) as client:
            a2d = Ascii2D(client = client)
            status = await self.get_media_bytes(url = url)

            if status != 200:
                if not _retry:
                    await self.ascii2d_search(url = url, _retry = True)
                else:
                    logger.error(f"Request {status}")

                return None

            results = await a2d.search(file = self.image_raw)

            if not results.raw:
                return None

            resp_text, resp_url, _ = await a2d.get(results.url.replace("/color/", "/bovw/"))
            bovw_res = Ascii2DResponse(resp_text, resp_url)
            tasks = [self._format_ascii2d_result(bovw_res, True),
                     self._format_ascii2d_result(results)]
            await asyncio.gather(*tasks)

            for i in range(len(self.ascii2d_result)):
                if self.ascii2d_result[i]["url"] != "":
                    if self.ascii2d_result[i]["url"] == self.ascii2d_result_bovw[i]["url"]:
                        return self.ascii2d_result[i]


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
