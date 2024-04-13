from PicImageSearch import Iqdb, Network
from PicImageSearch.model import IqdbResponse


class ImageSearch:
    def __init__(self):
        self.proxy = None
        self.url = ''
        self.source_url: str = ''
        self.similarity: float = 0.0
        self.size: str = ''
        self.source: str = ''

    def _show_result(self, resp: IqdbResponse):
        self.source_url = resp.raw[0].url
        self.similarity = resp.raw[0].similarity
        self.size = resp.raw[0].size
        self.source = resp.raw[0].source

    async def sync(self):
        async with Network(proxies = self.proxy) as client:
            iqdb = Iqdb(client = client)
            resp = await iqdb.search(url = self.url)
            self._show_result(resp)
