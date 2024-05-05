import requests
from fake_useragent import UserAgent

from src.api.dmzj.Decrypt import RSAUtil
from src.api.dmzj.Urls import Urls
from src.utils.LoggerUtil import logger


class ComicApi:
    def __init__(self):
        self._api_url = Urls()
        self._decrypter = RSAUtil()
        self._headers = {'User-Agent': UserAgent().random}

    def _get(self, url: str = '', params = None):
        response = requests.get(url, headers = self._headers, params = params)

        if response.status_code == 200:
            logger.info(f'Process url request: {url}')
            return response.text
        else:
            logger.error(f'GET {url} failed, status code: {response.status_code}')

    def comic_carousel(self):
        """
        漫画轮播
        - 第一层 {category_id: int, title: str, sort: int, data: tuple}
        - 第二层 {cover: str, title: str, sub_title: str, type: int, url: str, obj_id: int, status: str, appWxId: str}
        """
        url = f"{self._api_url.v3_url}/recommend_new.json"
        return self._get(url)

    def comic_recommend(self):
        """
        漫画推荐
        - 第一层 {code: int, msg: str, data: tuple}
        - 第二层 {category_id: int, title: str, sort: int, data: tuple}
        - 第三层 {id: int, title: str, authors: str, status: str, cover: str, num: int}
        """
        url = f"{self._api_url.v3_url}/recommend/batchUpdate?category_id=50"
        return self._get(url)

    def comic_domestic(self):
        """
        首页国漫
        """
        url = f"{self._api_url.v3_url}/recommend/batchUpdate?category_id=52"
        return self._get(url)

    def comic_hot(self):
        """
        动漫热门
        - 第一层 {code: int, msg: str, data: tuple}
        - 第二层 {category_id: int, title: str, sort: int, data: list}
        - 第三层 {cover: str, title: str, sub_title: str, type: int, url: str, obj_id: int, status: str}
        """
        url = f"{self._api_url.v3_url}/recommend/batchUpdate?category_id=54"
        return self._get(url)

    def comic_subscription(self):
        """
        漫画订阅（需要登陆）
        """
        url = f"{self._api_url.v3_url}/0/category_with_level.json"
        return self._get(url)

    def comic_subject(self, page: int = 0):
        """
        漫画专题
        默认第一页
        page: 页面翻页，数字越小内容越靠近最近
        """
        url = f"{self._api_url.v3_url}/subject/0/{page}.json"
        return self._get(url)

    def comic_subject_detail(self, id: int):
        """
        漫画专题详情
        id: 页面翻页，数字越大内容越靠近最近
        PS: 现在是28/4/2024,id最大更新到了505
        """
        url = f"{self._api_url.v3_url}/subject/{id}.json"
        return self._get(url)

    def comic_category(self):
        """
        漫画分类标签
        第一层：{title: “题材”, items: list}
        第二层：{tag_number: int}
        第三层：{tag_id: int, tag_name; str}
        """
        url = f"{self._api_url.v3_url}/classify/filter.json"
        return self._get(url)

    def comic_filter(self, filter: int = 0, sort: int = 0, page: int = 0):
        """
        筛选类别
        默认搜索为：全部-正序-第一页
        filter: get from self.comic_category(self) -> tag_number
        sort: 0是正序，1是逆序
        page: 第几页
        """
        url = f"{self._api_url.v3_url}/classifyWithLevel/{filter}/{sort}/{page}.json"
        return self._get(url)

    def comic_related(self, id: int):
        """
        关联漫画
        id: 对应直接关联的漫画id
        第一层: {author_comics: str, theme_comics: str}
        第二层: {author_name: str, author_id: int, data: tuple}
        第三层: {comic_number: list} 0['id']即为传参的id
        第四层: {id: int, name: str, cover: str, status: str}
        """
        url = f"{self._api_url.v3_url}/v3/comic/related/{id}.json"
        return self._get(url)

    def comic_search(self, query: str = 'None', page: int = 0):
        """
        漫画搜索
        默认第一页
        query: 用户需要搜索的字符串
        page: 翻页
        """
        if query != 'None':
            url = f"{self._api_url.v3_url}/search/show/0/{query}/{page}.json"
            return self._get(url)
        else:
            return 'Search not found'

    def comic_type_search(self, type: int = 0):
        """
        漫画搜索类型
        默认为0
        只有0和1是能用的，具体这是什么type并不清楚
        """
        url = f"{self._api_url.v3_url}/search/hot/{type}.json"
        return self._get(url)

    def comic_latest(self, type, page):
        """
        Wait for testing !!!
        """
        url = f"{self._api_url.v4_url}/comic/update/list/{type}/{page}"
        return RSAUtil().decrypt(self._get(url))

    def comic_detail(self, comic_id):
        url = f"{self._api_url.v4_url}/comic/detail/{comic_id}"
        return self._decrypter.decrypt(self._get(url))

    def comic_chapter_detail(self, comic_id, chapter_id):
        url = f"{self._api_url.v4_url}/comic/chapter/{comic_id}/{chapter_id}"
        return self._decrypter.decrypt(self._get(url))

    def author_detail(self, author_id):
        url = f"{self._api_url.v3_url}/UCenter/author/{author_id}.json"
        return self._get(url)

    def comic_rank(self, tag_id, by_time, rank_type, page):
        url = f"{self._api_url.v3_url}/comic/rank/list"
        params = {"tag_id": tag_id, "by_time": by_time, "rank_type": rank_type, "page": page}
        return self._get(url, params)
