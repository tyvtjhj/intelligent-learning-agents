import json
import sys
import urllib.request
import urllib.parse
import urllib.error
import re
from html import unescape

def _extract_text(html: str) -> str:
    clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<[^>]+>', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean)
    clean = unescape(clean)
    return clean.strip()[:3000]


def external_search(query: str) -> str:
    """
    联网搜索知识点。当本地题库没有答案时使用。
    适用场景：学生问的知识点不在数据库中，需要从互联网获取。
    """
    if not query or not query.strip():
        return json.dumps({"ok": False, "error": "搜索词不能为空"})

    try:
        encoded_query = urllib.parse.quote(query.strip())
        url = f"https://www.bing.com/search?q={encoded_query}&setlang=zh-cn"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })

        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="ignore")

        clean_text = _extract_text(html)

        snippets = re.findall(r'.{0,100}' + re.escape(query.strip()) + r'.{0,100}', clean_text, re.IGNORECASE)
        if not snippets:
            lines = [l.strip() for l in clean_text.split('.') if len(l.strip()) > 20]
            snippets = lines[:10]

        return json.dumps({
            "ok": True,
            "query": query,
            "result": "\n".join(snippets[:10]),
            "snippet_count": len(snippets[:10]),
        }, ensure_ascii=False)

    except urllib.error.URLError as e:
        return json.dumps({"ok": False, "error": f"网络错误: {e.reason}"})
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)})


_HANDLERS = {
    "external_search": external_search,
}


def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            req = json.loads(line.strip())
            method = req.get("method", "")
            if method == "tools/list":
                tools = [{"name": k, "description": v.__doc__ or ""} for k, v in _HANDLERS.items()]
                print(json.dumps({"tools": tools}, ensure_ascii=False), flush=True)
            elif method == "tools/call":
                tool_name = req.get("params", {}).get("name", "")
                arguments = req.get("params", {}).get("arguments", {})
                handler = _HANDLERS.get(tool_name)
                if handler:
                    result = handler(**arguments)
                    print(result, flush=True)
                else:
                    print(json.dumps({"ok": False, "error": f"未知工具: {tool_name}"}, ensure_ascii=False), flush=True)
        except Exception as e:
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
