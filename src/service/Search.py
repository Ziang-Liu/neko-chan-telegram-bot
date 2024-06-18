import asyncio
from typing import Dict, Optional, List

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
        self._ascii2d: List = []
        self._ascii2d_bovw: List = []
        self.ascii2d_result: Dict = {}
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

            return resp.raise_for_status().content

    async def _search_with_type(self, url: str, function, client_class):
        async with Network(proxies = self._proxy) as client:
            media = await self.get_media(url)
            search_instance = client_class(client = client)
            results = await function(search_instance, file = media)
            if not results.raw:
                raise Exception("No search results")

            if client_class == Ascii2D:
                resp_text, resp_url, _ = await search_instance.get(results.url.replace("/color/", "/bovw/"))
                bovw_results = Ascii2DResponse(resp_text, resp_url)
                tasks = [self._format_ascii2d_result(bovw_results, True),
                         self._format_ascii2d_result(results)]
                await asyncio.gather(*tasks)
            elif client_class == Iqdb:
                await self._format_iqdb_result(results)

    async def _format_iqdb_result(self, resp: IqdbResponse):
        selected_res: IqdbItem = resp.raw[0]
        danbooru_res: List[IqdbItem] = [i for i in resp.raw if i.source == "Danbooru"]
        yandere_res: List[IqdbItem] = [i for i in resp.raw if i.source == "yande.re"]

        if danbooru_res:
            selected_res = danbooru_res[0]
        elif yandere_res:
            selected_res = yandere_res[0]

        if selected_res.similarity < 85.0:
            return

        self.iqdb_result["class"] = "iqdb"
        self.iqdb_result["url"] = selected_res.url
        self.iqdb_result["similarity"] = selected_res.similarity
        self.iqdb_result["thumbnail"] = selected_res.thumbnail
        self.iqdb_result["content"] = selected_res.content
        self.iqdb_result["source"] = selected_res.source

    async def _format_ascii2d_result(self, resp: Ascii2DResponse, bovw: bool = False):

        target: List = self._ascii2d_bovw if bovw else self._ascii2d

        for i, r in enumerate(resp.raw):
            if not r.url_list or i == 0:
                continue

            r.author = "None" if not r.author else r.author
            target.append({
                "class": "ascii2d", "url": r.url, "author": r.author, "author_url": r.author_url,
                "thumbnail": r.thumbnail
            })

            if i == 3:
                break

    async def iqdb_search(self, url: str):
        await self._search_with_type(url, Iqdb.search, Iqdb)

    async def ascii2d_search(self, url):
        await self._search_with_type(url, Ascii2D.search, Ascii2D)

        for i in range(min(len(self._ascii2d_bovw), len(self._ascii2d))):
            if self._ascii2d[i]["url"] == self._ascii2d_bovw[i]["url"]:
                self.ascii2d_result = self._ascii2d[i]

    async def aggregation_search(self, url: str) -> Optional[Dict]:
        tasks = [self.iqdb_search(url), self.ascii2d_search(url)]
        await asyncio.gather(*tasks)

        return self.iqdb_result if self.iqdb_result else self.ascii2d_result
