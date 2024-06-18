from typing import List
from urllib.parse import quote_plus

from fake_useragent import UserAgent
from httpx import AsyncClient, Proxy


class TraceMoeApi:
    def __init__(self, proxy: Proxy | None = None):
        self._base = "https://api.trace.moe"
        self._search_with_file = "https://api.trace.moe/search"
        self._search_by_url = "https://api.trace.moe/search?url={}"
        self._search_by_url_with_cut_boarder = "https://api.trace.moe/search?cutBorders&url={}"
        self._search_by_url_with_anilist = "https://api.trace.moe/search?anilistInfo&url={}"
        self._proxy = proxy

    async def _search(self, api: str, url: str | None = None, data: bytes | None = None):
        headers = {
            "User-Agent": UserAgent().random,
            "Content-Type": "application/octet-stream"
        } if url else {"User-Agent": UserAgent().random}

        async with AsyncClient(proxy = self._proxy, headers = headers) as client:
            resp = await client.get(api.format(quote_plus(url))) if url else await client.post(api, data = data)
            result = resp.raise_for_status().json()
            if result.get("error"):
                raise Exception(result["error"])

            return result.get("result")

    async def search_by_url(self, url: str) -> List:
        return await self._search(self._search_by_url, url = url)

    async def search_by_url_with_cut_boarder(self, url) -> List:
        return await self._search(self._search_by_url_with_cut_boarder, url = url)

    async def search_by_url_with_anilist_info(self, url) -> List:
        return await self._search(self._search_by_url_with_anilist, url = url)

    async def search_by_file(self, file: bytes) -> List:
        return await self._search(self._search_with_file, data = file)
