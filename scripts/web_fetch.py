#!/usr/bin/env python3
"""
用 Playwright 驱动真实浏览器抓取单个网页的正文全文，
专门处理被阿里云 WAF / JS 挑战保护的站点（雪球、东财等）。

用法:
    python3 web_fetch.py "https://xueqiu.com/1062170191/404008951"
    python3 web_fetch.py "https://xueqiu.com/1062170191/404008951" --out /tmp/article.json
    python3 web_fetch.py "https://finance.sina.com.cn/..." --selector "article" --wait 3

原理:
    纯 curl/requests 会被阿里云 WAF 拦截（返回 JS 挑战页或滑块验证）。
    Playwright 驱动真实 Chromium 打开页面，自动通过 WAF 挑战，
    拿到合法 cookie 后再读取页面内容，清洗为纯文本。

依赖（与 xueqiu_hot_posts.py 完全共用）:
    pip install playwright beautifulsoup4 lxml
    以及 Chromium 内核（脚本自动查找 ~/Library/Caches/ms-playwright 下的缓存）

注意:
    - 首次运行较慢（要过 WAF 挑战），属正常现象。
    - 请控制频率，仅作个人研究，避免高并发给对方服务器造成压力。
"""
import argparse
import glob
import json
import os
import re
import sys
import time
from html import unescape

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# 反检测脚本：隐藏 headless / webdriver 特征
STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
window.chrome = window.chrome || {runtime: {}};
"""


def find_chromium():
    """优先用环境变量指定的浏览器，否则在 ms-playwright 缓存里找可用的 chromium。"""
    env = os.environ.get("PW_CHROMIUM")
    if env and os.path.exists(env):
        return env
    patterns = [
        os.path.expanduser("~/Library/Caches/ms-playwright/chromium-*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium"),
        os.path.expanduser("~/Library/Caches/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-mac*/chrome-headless-shell"),
        os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux/chrome"),
        os.path.expanduser("~/.cache/ms-playwright/chromium_headless_shell-*/chrome-linux/headless_shell"),
    ]
    for pat in patterns:
        hits = sorted(glob.glob(pat), reverse=True)
        if hits:
            return hits[0]
    return None


def clean_html(raw: str) -> str:
    """把 HTML 清洗成纯文本，保留可读格式。"""
    if not raw:
        return ""
    soup = BeautifulSoup(unescape(raw), "lxml")
    # 保留图片占位
    for img in soup.find_all("img"):
        alt = img.get("alt", "")
        img.replace_with(f"[图片: {alt}]" if alt else "[图片]")
    # 保留链接文字
    for a in soup.find_all("a"):
        href = a.get("href", "")
        if href and not a.get_text(strip=True):
            a.replace_with(f"[链接: {href}]")
    # 换行处理
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all(["p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6"]):
        p.append("\n")
    text = soup.get_text(separator="", strip=False)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_article_text(page, content_selector: str = None) -> str:
    """
    从已加载的 Playwright 页面里提取正文。
    优先用用户指定的 CSS 选择器；未指定则按常见财经站点规则自动探测。
    """
    if content_selector:
        try:
            el = page.query_selector(content_selector)
            if el:
                html = page.evaluate("(el) => el.innerHTML", el)
                return clean_html(html)
        except Exception:
            pass

    # 自动探测：按站点优先级匹配常见内容容器
    auto_selectors = [
        # 雪球长文
        "article",
        ".article__bd",
        ".article__content",
        ".detail__bd",
        # 新浪财经 / 百家号 / 公众号
        ".article-content",
        ".article_body",
        "#article_content",
        ".rich_media_content",
        # 凤凰网 / 腾讯新闻
        ".article-main",
        ".content-article",
        # 通用 fallback
        "main",
    ]
    for sel in auto_selectors:
        try:
            el = page.query_selector(sel)
            if el:
                html = page.evaluate("(el) => el.innerHTML", el)
                text = clean_html(html)
                if len(text) > 200:  # 正文至少要有一定长度
                    return text
        except Exception:
            continue

    # 最后兜底：取 body 全文
    try:
        body = page.evaluate("() => document.body ? document.body.innerText : ''")
        return body.strip()[:50000]
    except Exception:
        return ""


def fetch_page(url: str, content_selector: str = None, wait_seconds: int = 5,
               referer_site: str = None, headless: bool = True) -> dict:
    """
    用 Playwright 抓取单个 URL 的正文全文。

    参数:
        url: 目标页面地址
        content_selector: 正文容器的 CSS 选择器（可选，不指定则自动探测）
        wait_seconds: 页面加载后额外等待秒数（给 JS 渲染时间，默认 5）
        referer_site: 如果目标站需要先访问首页拿 cookie，传首页 URL
                      （如抓雪球文章时传 "https://xueqiu.com"）
        headless: 是否无头模式

    返回:
        {"url": ..., "title": ..., "text": ..., "fetched_at": ..., "status": "ok"|"error", ...}
    """
    exe = find_chromium()
    launch_kwargs = {
        "headless": headless,
        "args": ["--disable-blink-features=AutomationControlled"],
    }
    if exe:
        launch_kwargs["executable_path"] = exe
        print(f"[web_fetch] 使用浏览器: {exe}", file=sys.stderr)

    result = {
        "url": url,
        "title": "",
        "text": "",
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "error",
        "error": None,
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        ctx = browser.new_context(
            user_agent=UA,
            locale="zh-CN",
            viewport={"width": 1440, "height": 900},
        )
        ctx.add_init_script(STEALTH_JS)
        pg = ctx.new_page()

        try:
            # 第 0 步（可选）：先访问站点首页拿 WAF cookie
            if referer_site:
                print(f"[web_fetch] 先访问 {referer_site} 获取 cookie ...",
                      file=sys.stderr)
                try:
                    pg.goto(referer_site, wait_until="domcontentloaded",
                            timeout=20000)
                    pg.wait_for_timeout(3000)
                except Exception as e:
                    print(f"[web_fetch] referer 页访问异常 (可忽略): {e}",
                          file=sys.stderr)

            # 第 1 步：打开目标页面
            print(f"[web_fetch] 抓取 {url} ...", file=sys.stderr)
            pg.goto(url, wait_until="domcontentloaded", timeout=30000)

            # 等待 JS 渲染
            pg.wait_for_timeout(wait_seconds * 1000)

            # 滚动触发懒加载
            pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            pg.wait_for_timeout(1500)

            # 检查是否被 WAF 拦截（页面过短）
            html_len = pg.evaluate("() => document.body.innerHTML.length")
            if html_len < 3000:
                print(f"[web_fetch] 页面过短 ({html_len} chars)，可能被 WAF 拦截，"
                      f"额外等待 5 秒 ...", file=sys.stderr)
                pg.wait_for_timeout(5000)
                html_len = pg.evaluate("() => document.body.innerHTML.length")

            # 第 2 步：提取标题
            title_selectors = [
                "h1", ".article__title", ".article-title",
                "title", "meta[property='og:title']",
            ]
            for sel in title_selectors:
                try:
                    if sel == "title":
                        t = pg.evaluate("() => document.title")
                    elif sel.startswith("meta"):
                        t = pg.evaluate(
                            f"() => document.querySelector('{sel}')?.content || ''"
                        )
                    else:
                        el = pg.query_selector(sel)
                        t = pg.evaluate("(el) => el ? el.innerText.trim() : ''", el)
                    if t and len(t.strip()) > 1:
                        result["title"] = t.strip()
                        break
                except Exception:
                    continue

            # 第 3 步：提取正文
            text = extract_article_text(pg, content_selector)
            result["text"] = text
            result["status"] = "ok"
            result["text_length"] = len(text)

            print(f"[web_fetch] 标题: {result['title'][:80]}", file=sys.stderr)
            print(f"[web_fetch] 正文: {len(text)} chars", file=sys.stderr)

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"[web_fetch] 抓取失败: {e}", file=sys.stderr)
        finally:
            browser.close()

    return result


def main():
    ap = argparse.ArgumentParser(
        description="用 Playwright 抓取单个网页的正文全文（可过 WAF）")
    ap.add_argument("url", help="目标页面 URL")
    ap.add_argument("--selector", "-s", default=None,
                    help="正文容器的 CSS 选择器（可选，不指定则自动探测）")
    ap.add_argument("--wait", "-w", type=int, default=5,
                    help="页面加载后等待秒数 (默认 5)")
    ap.add_argument("--referer", "-r", default=None,
                    help="先访问此 URL 获取 cookie（如雪球需先访问 https://xueqiu.com）")
    ap.add_argument("--out", "-o", default=None,
                    help="输出 JSON 文件路径 (默认打印到 stdout)")
    ap.add_argument("--show", action="store_true",
                    help="显示浏览器窗口(调试)")
    args = ap.parse_args()

    # 智能推断 referer：如果目标是常见 WAF 站点，自动设 referer
    auto_referer = None
    if not args.referer:
        from urllib.parse import urlparse
        host = urlparse(args.url).netloc
        if "xueqiu.com" in host:
            auto_referer = "https://xueqiu.com"
            print(f"[web_fetch] 自动设置 referer: {auto_referer}", file=sys.stderr)
        elif "eastmoney.com" in host:
            auto_referer = "https://www.eastmoney.com"
            print(f"[web_fetch] 自动设置 referer: {auto_referer}", file=sys.stderr)

    referer = args.referer or auto_referer
    result = fetch_page(
        args.url,
        content_selector=args.selector,
        wait_seconds=args.wait,
        referer_site=referer,
        headless=not args.show,
    )

    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"\n[web_fetch] 已写入 {args.out}", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
