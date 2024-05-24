import asyncio
import json

import aiohttp
from fake_useragent import UserAgent

from src.api.dmzj.crypto import Crypto
from src.utils.Logger import logger


class ComicApi:
    def __init__(self):
        self._v3 = "https://nnv3api.dmzj.com"
        self._v4 = "https://nnv4api.dmzj.com"
        self._decrypter = Crypto()
        self._headers = {'User-Agent': UserAgent().random}

    async def _parse_v4(self, url: str = '', params = None) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params = params, headers = self._headers) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    logger.error(f'Request failed with status code: {response.status}')
                    return b''

    async def _parse_v3(self, url: str = '', params = None) -> json:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params = params, headers = self._headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f'Request failed with status code: {response.status}')
                    return {}

    def carousel(self) -> list[dict]:
        """ 漫画轮播
        :return:
        [{"category_id":,"title":,"sort":,"data":
        [{"cover":,"title":,"sub_title":,"type":,"url":,"obj_id":,"status":,"appWxId":},]}]
        """
        url = f"{self._v3}/recommend_new.json"

        return asyncio.run(self._parse_v3(url = url))

    def random(self) -> list[dict]:
        """ 随便看看 """
        url = f"{self._v3}/recommend/batchUpdate?category_id=50"
        data_raw = asyncio.run(self._parse_v3(url = url))

        return data_raw['data']['data']

    def hot(self) -> list[dict]:
        """ 热门连载 """
        url = f"{self._v3}/recommend/batchUpdate?category_id=54"
        data_raw = asyncio.run(self._parse_v3(url = url))

        return data_raw['data']['data']

    def subject(self, page: int = 0) -> list[dict]:
        """ 漫画专题
        :param page: 默认第一页，数字越小内容越靠近最近
        :return:
        [{"id":,"title":,"short_title":,"create_time":,"small_cover":,"page_type":,"sort":,"page_url":},]
        """
        url = f"{self._v3}/subject/0/{page}.json"

        return asyncio.run(self._parse_v3(url))

    def subject_detail(self, id: int) -> dict:
        """ 漫画专题详情
        :param id: such like comic_subject()[0]['id']
        :return:
        {"mobile_header_pic":,"title":,"page_url":,"description":,"comics":,"comment_amount":}
        """
        url = f"{self._v3}/subject/{id}.json"

        return asyncio.run(self._parse_v3(url))

    def category(self) -> dict:
        """ 漫画分类标签
        :return:
        {"tag_name": tag_id}
        """
        url = f"{self._v3}/classify/filter.json"
        data_raw = asyncio.run(self._parse_v3(url))
        tag_dict = {}

        for category in data_raw:
            for item in category["items"]:
                tag_name = item["tag_name"]
                tag_id = item["tag_id"]
                if tag_name not in tag_dict:
                    tag_dict[tag_name] = tag_id

        return tag_dict

    def filter(self, tag_id: int = 0, sort: int = 0, page: int = 0) -> list[dict]:
        """ 筛选类别
        :param tag_id: get from category()
        :param sort: sort order. 0 represents popularity, 1 represents recently updated
        :param page: the search page. 0 represents first page
        """
        url = f"{self._v3}/classifyWithLevel/{tag_id}/{sort}/{page}.json"

        return asyncio.run(self._parse_v3(url))

    def related(self, id: int) -> dict[list]:
        """ 关联漫画
        :return:
        {author_comics[], theme_comics[], novels[]}
        :param id: manga id
        """
        url = f"{self._v3}/v3/comic/related/{id}.json"
        return asyncio.run(self._parse_v3(url))

    def search(self, query: str = 'None', page: int = 0) -> list[dict]:
        """ 漫画搜索
        :param query: 用户需要搜索的字符串
        :param page: the search page. 0 represents first page
        """
        if query != 'None':
            url = f"{self._v3}/search/show/0/{query}/{page}.json"

            return asyncio.run(self._parse_v3(url))
        else:
            return [{}]

    def manga_detail(self, id):
        """
        :param id: manga id
        """
        url = f"{self._v4}/comic/detail/{id}?uid=2665531"
        resp = asyncio.run(self._parse_v4(url))
        return self._decrypter.decrypt(resp)

    def chapter_detail(self, id, chapter_id):
        url = f"{self._v4}/comic/chapter/{id}/{chapter_id}"
        resp = asyncio.run(self._parse_v4(url))

        return self._decrypter.decrypt(resp)

    def author(self, author_tag_id) -> dict:
        url = f"{self._v3}/UCenter/author/{author_tag_id}.json"

        return asyncio.run(self._parse_v3(url))
