import re
import trafilatura
from bs4 import BeautifulSoup
from curl_cffi import requests
from playwright.sync_api import sync_playwright
from client.cookie_store import load_cookies

def fetch_html(url: str) -> str:
    # 针对语雀 (Yuque) 的特殊处理：SPA 动态渲染 + 权限控制 + 专用清洗
    if "yuque.com" in url:
        return _fetch_dynamic(url, "yuque")
        
    # 其他默认静态抓取
    return _fetch_static(url)

def _fetch_dynamic(url: str, platform: str) -> str:
    print(f"[*] Using Playwright for {platform}...")
    try:
        cookies = load_cookies(platform) or []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            if cookies:
                context.add_cookies(cookies)
            
            page = context.new_page()
            page.goto(url)
            
            # 等待语雀阅读器核心容器
            try:
                page.wait_for_selector(".ne-viewer-body", timeout=15000)
                # 获取核心内容区域的 HTML，而非整个页面
                content = page.locator(".ne-viewer-body").inner_html()
            except Exception:
                # 兜底
                page.wait_for_load_state("networkidle")
                content = page.content()
                
            browser.close()
            
            if platform == "yuque":
                return _process_yuque_content(content)
                
            return _clean_content(content)
    except Exception as e:
        print(f"[-] Dynamic Fetch Error: {e}")
        return ""

def _process_yuque_content(html_source: str) -> str:
    """
    专门针对语雀的 <ne-*> 标签体系进行清洗和标准化转换。
    目标是生成下游 AI 转换器能理解的 '类 HTML' 或 'Markdown 混合体'。
    """
    print("[*] Pre-processing Yuque DOM structure...")
    soup = BeautifulSoup(html_source, "html.parser")

    # 1. 移除干扰元素 (SVG, 锚点、折叠按钮、填充符、操作按钮等)
    # ne-heading-anchor: 标题前的锚点图标
    # ne-heading-fold: 标题折叠按钮
    # ne-viewer-b-filler: 占位符
    # ne-uli-i / ne-oli-i: 列表原本的符号(圆点/数字)，我们稍后会自己生成 Markdown 符号，所以去掉原生的
    selectors_to_remove = [
        "svg", "style", "script", "noscript",
        ".ne-heading-ext", ".ne-heading-anchor", ".ne-heading-fold", 
        ".ne-viewer-b-filler", ".ne-ui-exit-max-view-btn", "button",
        "ne-uli-i", "ne-oli-i" 
    ]
    for selector in selectors_to_remove:
        for tag in soup.select(selector):
            tag.decompose()

    # 2. 标签映射表 (Yuque Tag -> Standard Tag)
    # 直接将 ne-h* 替换为标准 h*，Trafilatura 或 Converter 更容易识别
    tag_map = {
        "ne-h1": "h1", "ne-h2": "h2", "ne-h3": "h3",
        "ne-h4": "h4", "ne-h5": "h5", "ne-h6": "h6",
        "ne-p": "p",
        "ne-quote": "blockquote"
    }

    for ne_tag, std_tag in tag_map.items():
        for tag in soup.find_all(ne_tag):
            tag.name = std_tag
            tag.attrs = {} # 移除所有属性，保持纯净

    # 3. 特殊处理：列表 (ne-uli / ne-oli)
    # 语雀的列表结构较深，且上面已经移除了 ne-*-i (符号)，现在只剩下内容 ne-*-c
    # 我们将其转换为扁平的段落，带有 Markdown 列表标记，方便后续 AI 识别
    for uli in soup.find_all("ne-uli"):
        text = uli.get_text(strip=True)
        new_tag = soup.new_tag("p")
        new_tag.string = f"- {text}" 
        uli.replace_with(new_tag)

    for oli in soup.find_all("ne-oli"):
        text = oli.get_text(strip=True)
        # 清理可能残留的序号文本（如果有）
        text = re.sub(r'^\d+\.', '', text).strip()
        new_tag = soup.new_tag("p")
        new_tag.string = f"1. {text}"
        oli.replace_with(new_tag)

    # 4. 特殊处理：代码块 (ne-card[data-card-name="codeblock"])
    # 语雀代码块是一个复杂的 Card，实际代码在 .cm-content 内
    for card in soup.find_all("ne-card", attrs={"data-card-name": "codeblock"}):
        code_content = ""
        # 尝试从 CodeMirror 内容中提取
        cm_content = card.select_one(".cm-content")
        if cm_content:
            # CodeMirror 的每一行通常是一个 div.cm-line
            lines = [line.get_text() for line in cm_content.select(".cm-line")]
            code_content = "\n".join(lines)
        else:
            # 兜底：直接获取文本
            code_content = card.get_text("\n")

        # 创建标准的 pre > code 结构
        pre_tag = soup.new_tag("pre")
        code_tag = soup.new_tag("code")
        code_tag.string = code_content
        pre_tag.append(code_tag)
        card.replace_with(pre_tag)

    # 5. 特殊处理：分割线 (ne-card[data-card-name="hr"])
    for hr_card in soup.find_all("ne-card", attrs={"data-card-name": "hr"}):
        hr_tag = soup.new_tag("hr")
        hr_card.replace_with(hr_tag)

    # 6. 最后的清理：unwrap 掉无用的包装标签
    # ne-heading-content: 标题内容的包装
    # ne-text: 文本的包装
    for wrapper in soup.select("ne-heading-content, ne-text"):
        wrapper.unwrap()

    print(f"[*] Yuque DOM normalized. Length: {len(str(soup))}")
    return str(soup)

def _fetch_static(url: str) -> str:
    try:
        resp = requests.get(
            url, 
            impersonate="chrome120", 
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            timeout=10
        )
        if resp.status_code != 200:
            print(f"[-] HTTP Error: {resp.status_code}")
            return ""
        return _clean_content(resp.text)
    except Exception as e:
        print(f"[-] Static Fetch Error: {e}")
        return ""

def _clean_content(html_source: str) -> str:
    try:
        # 使用 Trafilatura 进行通用清洗
        cleaned_content = trafilatura.extract(
            html_source,
            include_formatting=True, 
            include_links=True,      
            include_images=False,    
            include_tables=True,     
            include_comments=False,
            output_format='html'     
        )
        
        if not cleaned_content:
            # 如果 Trafilatura 失败（可能因为 DOM 结构太碎），尝试直接返回 body 的一部分
            # 这是一个简单的兜底
            print("[-] Warning: Trafilatura extracted nothing. Returning raw body slice.")
            if "body" in html_source:
                return html_source # 返回原始内容给 AI 尝试处理
            return ""
            
        print(f"[*] Success. Length: {len(cleaned_content)} chars")
        return cleaned_content

    except Exception as e:
        print(f"[-] Cleaning Error: {e}")
        return ""

if __name__ == '__main__':
    # ctx = fetch_html('https://www.cnblogs.com/swizard/p/19332596')
    # print(ctx)
    ctx = fetch_html('https://www.yuque.com/yharim-vfti3/ti9p8n/mxfagzycmiar9vfx')
    print(ctx)