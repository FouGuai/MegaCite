import trafilatura
from curl_cffi import requests

def fetch_html(url: str) -> str:
    try:
        # 模拟 Chrome 120 指纹
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

        html_source = resp.text

    except Exception as e:
        print(f"[-] Fetch Error: {e}")
        return ""

    # --- 使用 Trafilatura 进行清洗 ---
    try:
        cleaned_content = trafilatura.extract(
            html_source,
            include_formatting=True, # <--- 必须开启！保留 b, strong, i, em 等
            include_links=True,      # <--- 强烈建议开启！保留 a href，否则 Markdown 没链接
            include_images=False,    # 根据需要决定是否保留 img
            include_tables=True,     # 保留 table 结构
            include_comments=False,
            no_fallback=False,
            output_format='html'     # 输出格式保持 html 方便后续正则/LLM处理
        )
        
        if not cleaned_content:
            print("[-] Warning: No content extracted.")
            return ""
            
        print(f"[*] Success. Length: {len(cleaned_content)} chars")
        return cleaned_content

    except Exception as e:
        print(f"[-] Cleaning Error: {e}")
        return ""

if __name__ == '__main__':
    ctx = fetch_html('https://www.cnblogs.com/swizard/p/19332596')
    print(ctx)