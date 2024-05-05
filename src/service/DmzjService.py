from src.api.dmzj.ComicApi import ComicApi

if __name__ == "__main__":
    comic = ComicApi()
    info = comic.comic_chapter_detail(60632, 131618)
    pass
