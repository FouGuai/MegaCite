import database as db

def fetch_article(url: str) -> db.Article:
    """
    抓取指定URL的文章内容
    """
    