from PicImageSearch import Iqdb, Network
from PicImageSearch.model import IqdbResponse, GoogleResponse

from src.utils.LoggerUtil import logger


class ImageSearch:
    def __init__(self):
        self.proxy = None
        self.input_url = ''

    def _iqdb_result(self, resp: IqdbResponse):
        try:
            self.iqdb_url = resp.raw[0].url
            self.iqdb_similarity = resp.raw[0].similarity
            self.iqdb_size = resp.raw[0].size
            self.iqdb_source = resp.raw[0].source
        except Exception as e:
            logger.error(e)
            self.iqdb_similarity = 0.0

    def _google_result(self, resp: GoogleResponse):
        try:
            selected = next((i for i in resp.raw if i.thumbnail), resp.raw[2])
            self.google_title = selected.title
            self.google_url = selected.url
        except Exception as e:
            logger.error(e)
            self.google_title = ''
            self.google_url = ''

    async def sync(self):
        async with Network(proxies = self.proxy) as client:
            self._iqdb_result(await Iqdb(client = client).search(url = self.input_url))
