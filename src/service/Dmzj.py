from src.api.dmzj.api import DmzjApi

if __name__ == "__main__":
    comic = DmzjApi()
    random = comic.random()
    hot = comic.hot()
    carousel = comic.carousel()
    subject = comic.subject()
    category = comic.category()
    filter = comic.filter(tag_id = 3243, sort = 1)
    related = comic.related(id = filter[0]['id'])
    search = comic.search(query = '86')
    detail = comic.manga_detail(id = 74429)
    author = comic.author(author_tag_id = "11451")
