import json
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import re
import socket
from html import unescape

socket.setdefaulttimeout(15)


def _extract_text(html: str) -> str:
    clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<[^>]+>', ' ', clean)
    clean = re.sub(r'&nbsp;|&#160;', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean)
    clean = unescape(clean)
    return clean.strip()[:5000]


def external_search(query: str) -> str:
    """
    联网搜索知识点。当本地题库没有答案时使用。
    适用场景：学生问的知识点不在数据库中，需要从互联网获取。
    自带3次重试+指数退避，返回结构化结果供Agent决策。
    """
    if not query or not query.strip():
        return json.dumps({"ok": False, "error": "搜索词不能为空", "retry_exhausted": False})

    last_error = None
    for attempt in range(1, 4):
        try:
            encoded_query = urllib.parse.quote(query.strip())
            url = f"https://www.bing.com/search?q={encoded_query}&setlang=zh-cn"

            if attempt == 1:
                ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
            else:
                ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"

            req = urllib.request.Request(url, headers={
                "User-Agent": ua,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
            })

            with urllib.request.urlopen(req, timeout=20) as response:
                html = response.read().decode("utf-8", errors="ignore")

            clean_text = _extract_text(html)

            snippets = re.findall(
                r'.{0,150}' + re.escape(query.strip()) + r'.{0,150}',
                clean_text, re.IGNORECASE
            )
            if not snippets:
                lines = [l.strip() for l in clean_text.split('。') if len(l.strip()) > 20]
                snippets = lines[:15]

            if snippets:
                return json.dumps({
                    "ok": True,
                    "query": query,
                    "result": "\n".join(snippets[:12]),
                    "snippet_count": len(snippets[:12]),
                    "source": "bing",
                    "attempt": attempt,
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    "ok": False,
                    "error": "未提取到有效内容，请尝试更具体的搜索词",
                    "retry_exhausted": False,
                })

        except (urllib.error.URLError, socket.timeout, TimeoutError) as e:
            last_error = str(getattr(e, 'reason', e))
            if attempt < 3:
                time.sleep(attempt * 2)
        except Exception as e:
            last_error = str(e)
            if attempt < 3:
                time.sleep(attempt * 2)

    return json.dumps({
        "ok": False,
        "error": f"联网搜索失败(已重试3次): {last_error}",
        "retry_exhausted": True,
        "suggestion": "请基于你已有的知识直接回答用户的问题，然后用 db_save_new_knowledge 将知识点存入本地数据库。",
    }, ensure_ascii=False)


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
