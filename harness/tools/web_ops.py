"""
Web Operations & Content Extractor Tool (DeepSeek Harness Web Fetcher)
支持通过 HTTP 异步提取网页内容、去除 HTML 噪音并转换为紧凑 Markdown 文本
"""

import re
import httpx
from typing import Optional


async def read_url_content(url: str, timeout: int = 15, max_length: int = 8000) -> str:
    """通过 HTTP GET 请求获取 URL 内容并转换为紧凑纯文本/Markdown"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.8,*/*;q=0.7"
    }

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return f"Error fetching URL ({resp.status_code}): {resp.text[:500]}"

            content_type = resp.headers.get("content-type", "").lower()
            text = resp.text

            # 如果是 HTML，进行清洗提取纯文本
            if "html" in content_type or "<html" in text.lower():
                # 剔除 script 与 style 标签
                text = re.sub(r'<script[\s\S]*?</script>', '', text, flags=re.IGNORECASE)
                text = re.sub(r'<style[\s\S]*?</style>', '', text, flags=re.IGNORECASE)
                text = re.sub(r'<nav[\s\S]*?</nav>', '', text, flags=re.IGNORECASE)
                text = re.sub(r'<footer[\s\S]*?</footer>', '', text, flags=re.IGNORECASE)
                
                # 将常用标签转为 Markdown 样式
                text = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'\n\n### \1\n', text, flags=re.IGNORECASE)
                text = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n', text, flags=re.IGNORECASE)
                text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.IGNORECASE)
                text = re.sub(r'<li[^>]*>(.*?)</li>', r'\n- \1', text, flags=re.IGNORECASE)
                text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)

                # 去除所有其余 HTML 标签
                text = re.sub(r'<[^>]+>', '', text)
                # 清洗多余空行与空格
                text = re.sub(r'[ \t]+', ' ', text)
                text = re.sub(r'\n{3,}', '\n\n', text).strip()

            if len(text) > max_length:
                text = text[:max_length] + f"\n\n... [Content truncated, total {len(resp.text)} chars] ..."

            return text if text else "[Empty webpage content]"
    except Exception as e:
        return f"Failed to read URL content: {e}"
