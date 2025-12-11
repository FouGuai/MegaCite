import re
from openai import OpenAI
from core.config import OPENAI_CONFIG

def convert_html_to_markdown(html_source: str) -> dict:
    """
    【全能优化版】
    1. 严格 HTML 映射 (H1-H6)
    2. 锚点续写 (长文完整性)
    3. 盘古之白 (中英文自动空格)
    4. 智能去重 (移除正文开头的重复标题，不限 H1)
    5. 列表修正 (强制列表前插入空行，修复渲染问题)
    """
    client = OpenAI(
        api_key=OPENAI_CONFIG["api_key"],
        base_url=OPENAI_CONFIG["base_url"]
    )

    # 1. 记忆阶段
    CHUNK_SIZE = 10000 
    chunks = [html_source[i:i+CHUNK_SIZE] for i in range(0, len(html_source), CHUNK_SIZE)]
    total_parts = len(chunks)
    
    # [System Prompt] 强调排版专家身份
    messages = [
        {"role": "system", "content": (
            "You are a strict HTML to Markdown converter and a typography expert. "
            "You strictly enforce Markdown syntax rules, especially regarding spacing, lists, and structure."
        )}
    ]

    for i, chunk in enumerate(chunks[:-1]):
        part_num = i + 1
        user_msg = (
            f"[Part {part_num}/{total_parts} of HTML Source]\n"
            f"```html\n{chunk}\n```\n\n"
            f"Instruction: Read and memorize this HTML content. Reply 'ACK'."
        )
        messages.append({"role": "user", "content": user_msg})
        
        print(f"[*] Loading Part {part_num}...")
        client.chat.completions.create(
            model=OPENAI_CONFIG["model"],
            messages=messages,
            temperature=0.1
        )
        messages.append({"role": "assistant", "content": "ACK"})

    # 2. 初始指令
    final_chunk = chunks[-1]
    
    initial_prompt = (
        "TASK: Convert the HTML content to standard Markdown with PERFECT typography.\n\n"
        "--- STRICT TAG MAPPING RULES ---\n"
        "1. **Headings**: `<h1>`-`<h6>` -> `# `-`###### `. Do NOT treat bold text as headers unless wrapped in <h> tags.\n"
        "2. **Code**: `<pre>`/`<code>` -> Fenced blocks (```language).\n"
        "3. **Lists (CRITICAL FIX)**: \n"
        "   - Convert `<ul>` to `- ` and `<ol>` to `1. `.\n"
        "   - **MANDATORY**: You MUST insert a **BLANK LINE** before the start of any list.\n"
        "   - **Example**:\n"
        "     [GOOD]:\n"
        "     This is a paragraph.\n"
        "     (Empty Line Here)\n"
        "     - List item 1\n"
        "     [BAD]:\n"
        "     This is a paragraph.\n"
        "     - List item 1\n"
        "4. **Basic**: `<b>` -> `**`, `<i>` -> `*`, `<blockquote>` -> `> `.\n"
        "\n"
        "--- SPACING RULES (PAN GU ZHI BAI) ---\n"
        "1. Insert a single space between Chinese and English/Numbers (e.g., `在 C++ 中`).\n"
        "2. No space inside URLs or code blocks.\n"
        "\n"
        "--- REDUNDANCY CONTROL (CRITICAL) ---\n"
        "1. The `===TITLE===` is rendered separately by the system.\n"
        "2. **CHECK THE START OF CONTENT**: If the `===CONTENT===` body starts with text that is identical or very similar to the Article Title (regardless of whether it is H1, Bold, or Plain text), **REMOVE IT**.\n"
        "3. The content should start directly with the introduction text or the first sub-header.\n"
        "\n"
        "--- OUTPUT FORMAT ---\n"
        "1. `===TITLE===` [Article Title]\n"
        "2. `===SUMMARY===` [One-line Summary]\n"
        "3. `===CONTENT===` [Markdown Body]\n"
        "\n"
        "--- GENERATION ---\n"
        "Output as much content as possible. Do NOT use `===END===` until the absolute end."
    )
    
    user_msg_final = (
        f"[Part {total_parts}/{total_parts} of HTML Source]\n"
        f"```html\n{final_chunk}\n```\n\n"
        f"Instruction: {initial_prompt}"
    )
    
    messages.append({"role": "user", "content": user_msg_final})
    
    print(f"[*] Starting Generation (List Fix & Smart Dedup)...")
    
    full_raw_text = ""
    loop_count = 0
    max_loops = 20 
    
    while loop_count < max_loops:
        loop_count += 1
        
        response = client.chat.completions.create(
            model=OPENAI_CONFIG["model"],
            messages=messages,
            temperature=0.1
        )

        content = response.choices[0].message.content
        messages.append({"role": "assistant", "content": content})
        
        if "===END===" in content:
            clean_part = content.replace("===END===", "")
            full_raw_text += clean_part
            print(f"    -> Segment {loop_count}: '===END===' detected. Done.")
            break
        else:
            full_raw_text += content
            
            # 锚点逻辑
            anchor_length = 200
            anchor_text = content[-anchor_length:] if len(content) > anchor_length else content
            
            print(f"    -> Segment {loop_count}: Continuing from anchor...")
            
            continuation_prompt = (
                f"I received your output ending with:\n"
                f"--- BEGIN SNIPPET ---\n"
                f"{anchor_text}\n"
                f"--- END SNIPPET ---\n\n"
                f"**INSTRUCTION**: \n"
                f"1. Continue converting starting **EXACTLY** after the snippet.\n"
                f"2. **Strictly enforce List Spacing** (Blank line before lists).\n"
                f"3. **Strictly enforce Chinese-English Spacing**.\n"
                f"4. Only output `===END===` when finished."
            )
            
            messages.append({"role": "user", "content": continuation_prompt})

    # 3. 解析结果
    print(f"[*] Stitching complete. Total length: {len(full_raw_text)} chars.")
    
    clean_text = full_raw_text
    clean_text = re.sub(r"^```(markdown|text)?", "", clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r"```$", "", clean_text)
    
    try:
        title_match = re.search(r"===TITLE===\s*(.*?)\s*(?:===SUMMARY===|$)", clean_text, re.DOTALL)
        title = title_match.group(1).strip() if title_match else "Untitled"
        
        summary_match = re.search(r"===SUMMARY===\s*(.*?)\s*(?:===CONTENT===|$)", clean_text, re.DOTALL)
        description = summary_match.group(1).strip() if summary_match else "No description"
        
        content_match = re.search(r"===CONTENT===\s*(.*)", clean_text, re.DOTALL)
        context = content_match.group(1).strip() if content_match else clean_text
        
        if not content_match and "===CONTENT===" not in clean_text:
            context = clean_text

    except Exception as e:
        print(f"[-] Parsing Error: {e}. Returning raw text.")
        title = "Parse Error"
        description = "Error"
        context = clean_text

    return {
        "title": title,
        "description": description,
        "context": context
    }