import database as db

def render_markdown(article : db.Article) -> str:
    """
    将Markdown渲染为HTML
    ref 为引用信息
    """