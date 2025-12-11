import time
import trafilatura
from curl_cffi import requests # 关键库：能够模拟浏览器底层指纹

def fetch_html(url: str) -> str:
    """
    无浏览器环境下的极速抓取方案。
    1. 获取：使用 curl_cffi 模拟 Chrome 120 的 TLS 指纹，欺骗服务器相信这是真实浏览器。
    2. 清洗：使用 trafilatura 库提取纯净正文。
    """
    try:
        # 使用 curl_cffi 发送请求
        # impersonate="chrome120": 关键参数，这会让握手包跟真实 Chrome 完全一致
        # 从而绕过 CSDN 的指纹检测，直接拿到正文，不会触发 nodata
        resp = requests.get(
            url, 
            impersonate="chrome120", 
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            timeout=10
        )
        
        # 检查状态码
        if resp.status_code != 200:
            print(f"[-] HTTP Error: {resp.status_code}")
            return ""

        html_source = resp.text

    except Exception as e:
        print(f"[-] Fetch Error: {e}")
        return ""

    # --- 使用 Trafilatura 进行清洗 ---
    try:
        # extract 是目前最可靠的去除非正文算法
        cleaned_content = trafilatura.extract(
            html_source,
            include_comments=False,
            include_tables=True,    # 保留表格
            include_images=False,   # 仅文本（如需图片改为True）
            no_fallback=False,
            output_format='html'
        )
        
        if not cleaned_content:
            # 极少数情况可能因为伪装不够完美导致获取到空内容，或者页面本身无内容
            print("[-] Warning: No content extracted.")
            return ""
            
        print(f"[*] Success. Length: {len(cleaned_content)} chars")
        return cleaned_content

    except Exception as e:
        print(f"[-] Cleaning Error: {e}")
        return ""

if __name__ == '__main__':
    start = time.time()
    url = 'https://blog.csdn.net/weixin_38991876/article/details/148174827'
    
    print(f"[*] Fetching: {url}")
    ctx = fetch_html(url)
    
    print(f"[*] Total Time: {time.time() - start:.2f}s")
    print("-" * 50)
    print(ctx[:500] if ctx else "Empty")