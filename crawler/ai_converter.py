import json
import re
from openai import OpenAI
from core.config import OPENAI_CONFIG

def convert_html_to_markdown(html_source: str) -> dict:
    """调用 Kimi API 将 HTML 清洗为结构化数据 (分块发送模式)"""
    client = OpenAI(
        api_key=OPENAI_CONFIG["api_key"],
        base_url=OPENAI_CONFIG["base_url"]
    )

    # 1. 定义分块参数
    # Kimi 8k 模型总上下文约 12k 字符。分块太大会导致后期历史记录溢出。
    # 建议在 core/config.py 中使用 moonshot-v1-32k 以支持更长文章。
    CHUNK_SIZE = 6000 
    
    # 2. 切割 HTML
    chunks = [html_source[i:i+CHUNK_SIZE] for i in range(0, len(html_source), CHUNK_SIZE)]
    total_parts = len(chunks)
    
    # 3. 初始化对话历史
    messages = [
        {"role": "system", "content": "You are a web scraper helper. I will send you HTML source code in parts. Please read and remember the content for the final task."}
    ]

    # 4. 循环处理前 N-1 个块 (记忆阶段)
    for i, chunk in enumerate(chunks[:-1]):
        part_num = i + 1
        user_msg = (
            f"[Part {part_num}/{total_parts} of HTML Source]\n"
            f"```html\n{chunk}\n```\n\n"
            f"Instruction: This is part {part_num}. Just read and remember this content internaly. "
            "Do NOT output the analysis result yet. Just reply 'Received part X'."
        )
        
        messages.append({"role": "user", "content": user_msg})
        
        print(f"[*] Sending HTML Part {part_num}/{total_parts}...")
        response = client.chat.completions.create(
            model=OPENAI_CONFIG["model"],
            messages=messages,
            temperature=0.1
        )
        
        # 将 AI 的回复加入历史，维持对话连贯性
        assistant_reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_reply})
        # print(f"    AI: {assistant_reply}")

    # 5. 发送最后一个块 (分析阶段)
    final_chunk = chunks[-1]
    final_prompt = (
        "Analyze ALL provided HTML parts (from history and this final part) and output a STRICT JSON object with keys: 'title', 'description', 'context'.\n"
        "Rules:\n"
        "1. 'context': Convert the main article content to standard Markdown.\n"
        "2. FORMATTING: You MUST use double newlines (\\n\\n) between paragraphs.\n"
        "3. CLEANING: Remove advertisements, navigation bars, scripts, and recommended links.\n"
        "4. OUTPUT: Return ONLY the raw JSON string. Do not use Markdown code blocks.\n"
        "5. ESCAPING: Ensure the JSON is valid. Escape all double quotes (\") within the content strings."
    )
    
    user_msg_final = (
        f"[Part {total_parts}/{total_parts} of HTML Source]\n"
        f"```html\n{final_chunk}\n```\n\n"
        f"Instruction: This is the final part. {final_prompt}"
    )
    
    messages.append({"role": "user", "content": user_msg_final})
    
    print(f"[*] Sending Final Part & Requesting Analysis...")
    response = client.chat.completions.create(
        model=OPENAI_CONFIG["model"],
        messages=messages,
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content
    
    # 6. 清洗 Markdown 标记
    if content.strip().startswith("```"):
        content = re.sub(r"^```json\s*", "", content.strip())
        content = re.sub(r"^```\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

    return json.loads(content)