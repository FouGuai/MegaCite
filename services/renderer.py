import markdown

class HTMLRenderer:
    """渲染 HTML 内容"""

    TEMPLATE_INDEX = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{username}'s Blog</title>
</head>
<body>
    <h1>Articles by {username}</h1>
    <hr>
    <ul>
        {list_items}
    </ul>
</body>
</html>
"""

    TEMPLATE_POST = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body>
    <h1>{title}</h1>
    <p>Date: {date} | Author: {author} | CID: {cid}</p>
    <hr>
    <div>
        {content}
    </div>
    <hr>
    <a href="index.html">Back to Index</a>
</body>
</html>
"""

    def render_user_index(self, username: str, post_list: list[dict]) -> str:
        items = []
        for p in post_list:
            # 链接直接指向同级目录下的 .html 文件
            items.append(f'<li><a href="{p["filename"]}">{p["title"]}</a></li>')
        
        return self.TEMPLATE_INDEX.format(
            username=username,
            list_items="\n".join(items) if items else "<li>No posts.</li>"
        )

    def render_post(self, post_data: dict, author_name: str, cid: str) -> str:
        raw_content = str(post_data.get("context", "") or "")
        # 使用 markdown 库渲染 HTML
        content = markdown.markdown(raw_content)
        
        return self.TEMPLATE_POST.format(
            title=post_data.get("title", "Untitled"),
            date=post_data.get("date", ""),
            author=author_name,
            cid=cid,
            content=content
        )