import requests
from bs4 import BeautifulSoup

def fetch_webpage_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = response.apparent_encoding
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        content_parts = []
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4']):
            text = tag.get_text().strip()
            if len(text) > 20:
                content_parts.append(text)
        
        full_text = '\n'.join(content_parts)
        
        if len(full_text) > 8000:
            full_text = full_text[:8000] + "\n... (内容过长，已截断)"
        
        return full_text
    
    except Exception as e:
        return f"抓取失败: {str(e)}"