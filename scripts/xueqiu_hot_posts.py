#!/usr/bin/env python3
"""
抓取雪球指定股票的「热帖」，加载每条热帖的正文全文 + 高赞评论，
清洗成精简的结构化 JSON，供 LLM 做选题/写稿参考。

用法:
    python3 xueqiu_hot_posts.py SH600585
    python3 xueqiu_hot_posts.py HK03690 --top 12 --comments 30 --out meituan.json
    python3 xueqiu_hot_posts.py SZ000858 --sort new --no-comments

原理:
    雪球评论区数据来自接口:
      列表  https://xueqiu.com/query/v1/symbol/search/status.json   (sort=alpha 即「热帖」)
      详情  https://xueqiu.com/statuses/show.json?id=<id>            (正文全文)
      评论  https://xueqiu.com/statuses/comments.json?id=<id>        (评论区)
    这些接口受阿里云 WAF 保护，纯 curl 会被 JS 挑战 / 滑块验证拦截。
    这里用 Playwright 驱动真实 Chromium 打开股票页, 自动通过 WAF 挑战并拿到
    雪球匿名 token, 待 token 就绪后在【页面上下文内】fetch 接口——请求天然带
    合法 cookie, 不触发滑块。返回的 HTML 正文再清洗为纯文本结构化数据。

注意:
    - 列表接口每页硬上限 20 条, 想要更多靠翻页 (maxPage 通常 50, 共约 1000 条)。
    - 评论接口每页 20 条, 想要更多同样靠翻页。
    - 请控制频率, 仅作个人研究, 避免高并发给对方服务器造成压力。
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

LIST_API = "https://xueqiu.com/query/v1/symbol/search/status.json"
SHOW_API = "https://xueqiu.com/statuses/show.json"
COMMENTS_API = "https://xueqiu.com/statuses/comments.json"

PAGE_SIZE = 20  # 雪球接口单页硬上限

# 反检测脚本：隐藏 headless / webdriver 特征，降低被风控识别的概率
STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
window.chrome = window.chrome || {runtime: {}};
"""

# 排序参数说明:
#   alpha = 热帖 (按互动热度，对应网页上的「热帖」tab)
#   time  = 新帖 (按发布时间)
SORT_MAP = {"hot": "alpha", "热帖": "alpha", "new": "time", "新帖": "time"}


# --------------------------------------------------------------------------- #
#  工具函数
# --------------------------------------------------------------------------- #
def clean_html(raw: str) -> str:
    """把雪球正文/评论里的 HTML 清洗成纯文本，保留股票链接/@某人的可读文字。"""
    if not raw:
        return ""
    soup = BeautifulSoup(unescape(raw), "lxml")
    for img in soup.find_all("img"):
        img.replace_with("[图片]")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    text = soup.get_text(separator="", strip=False)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fmt_time(ts):
    if not ts:
        return None
    try:
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts / 1000))
    except Exception:
        return None


def api_symbol(symbol: str) -> str:
    """接口 symbol 参数格式与页面 URL 不同：
       - A股: 页面/接口都用 SH600585 / SZ000858
       - 港股: 页面用 HK03690，但接口要用纯数字 03690 (去掉 HK 前缀) 才有数据
       - 美股: SYMBOL 一致 (如 BABA)
    """
    s = symbol.strip().upper()
    if s.startswith("HK"):
        return s[2:]
    return s


def find_chromium():
    """优先用环境变量指定的浏览器，否则在 ms-playwright 缓存里找可用的 chromium。"""
    env = os.environ.get("PW_CHROMIUM")
    if env and os.path.exists(env):
        return env
    patterns = [
        # macOS
        os.path.expanduser("~/Library/Caches/ms-playwright/chromium-*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium"),
        os.path.expanduser("~/Library/Caches/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-mac*/chrome-headless-shell"),
        # Linux (Codex 等可能跑在 Linux 上)
        os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux/chrome"),
        os.path.expanduser("~/.cache/ms-playwright/chromium_headless_shell-*/chrome-linux/headless_shell"),
    ]
    for pat in patterns:
        hits = sorted(glob.glob(pat), reverse=True)
        if hits:
            return hits[0]
    return None


def page_fetch_json(pg, url):
    """在已通过 WAF 验证的页面上下文里 fetch，返回 (status, dict|None)。"""
    res = pg.evaluate(
        """async (u) => {
            const r = await fetch(u, {
                headers: {'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'},
                credentials: 'include'
            });
            const t = await r.text();
            try { return {status: r.status, body: JSON.parse(t)}; }
            catch (e) { return {status: r.status, body: null, raw: t.slice(0, 200)}; }
        }""",
        url,
    )
    return res.get("status"), res.get("body"), res.get("raw", "")


# --------------------------------------------------------------------------- #
#  数据抓取
# --------------------------------------------------------------------------- #
def fetch_hot_list(pg, symbol, top, sort):
    """翻页拉取热帖列表, 直到累计 top 条 (去重)。"""
    sym = api_symbol(symbol)
    items, seen = [], set()
    total = None
    page = 1
    while len(items) < top:
        url = (f"{LIST_API}?symbol={sym}&count={PAGE_SIZE}&source=all"
               f"&sort={sort}&page={page}&type=11&comment=0&hl=0")
        status, body, raw = page_fetch_json(pg, url)
        if status != 200 or not body:
            print(f"[warn] 列表 page {page} status={status} 无有效 JSON: {raw!r}",
                  file=sys.stderr)
            break
        total = body.get("count")
        max_page = body.get("maxPage", 1)
        lst = body.get("list", [])
        if not lst:
            break
        for it in lst:
            pid = it.get("id")
            if pid in seen:
                continue
            seen.add(pid)
            items.append(it)
        print(f"[list] page {page}: 累计 {len(items)} 条 (服务端共 {total})",
              file=sys.stderr)
        if page >= max_page:
            break
        page += 1
        pg.wait_for_timeout(1200)  # 控制频率
    return items[:top]


def fetch_detail(pg, post_id):
    """拉取帖子正文全文 (列表里的 text 可能被截断)。"""
    status, body, _ = page_fetch_json(pg, f"{SHOW_API}?id={post_id}")
    if status == 200 and body:
        return body
    return None


def fetch_comments(pg, post_id, want, scan_pages=3):
    """拉取评论。雪球评论接口只返回时间序、不支持按赞排序, 因此多抓几页,
    再在本地按点赞数降序取前 want 条 (拿到真正的高赞热评)。"""
    comments, seen = [], set()
    for page in range(1, scan_pages + 1):
        url = (f"{COMMENTS_API}?id={post_id}&count={PAGE_SIZE}&page={page}"
               f"&reply=true&asc=false&type=status")
        status, body, _ = page_fetch_json(pg, url)
        if status != 200 or not body:
            break
        lst = body.get("comments", [])
        if not lst:
            break
        for c in lst:
            cid = c.get("id")
            if cid in seen:
                continue
            seen.add(cid)
            comments.append(c)
        if page >= body.get("maxPage", 1):
            break
        pg.wait_for_timeout(800)
    # 本地按点赞降序取前 want 条 (点赞相同则保持时间序)
    comments.sort(key=lambda c: c.get("like_count", 0), reverse=True)
    return comments[:want]


# --------------------------------------------------------------------------- #
#  结构化 (精简版：去掉 id/truncated/reward 等噪音字段)
# --------------------------------------------------------------------------- #
def struct_comment(c: dict) -> dict:
    user = c.get("user", {}) or {}
    return {
        "author": user.get("screen_name"),
        "text": clean_html(c.get("text", "")),
        "like_count": c.get("like_count", 0),
        "reply_count": c.get("reply_count", 0),
        "created_at": fmt_time(c.get("created_at")),
        "ip_location": c.get("ip_location"),
    }


def struct_post(detail: dict, list_item: dict, comments: list) -> dict:
    """把详情 + 列表元信息 + 评论合并成一条精简结构化记录。"""
    src = detail or list_item
    user = src.get("user", {}) or {}
    reply_c = list_item.get("reply_count", src.get("reply_count", 0))
    like_c = list_item.get("like_count", src.get("like_count", 0))
    target = list_item.get("target") or src.get("target") or ""
    post = {
        "author": user.get("screen_name"),
        "created_at": fmt_time(src.get("created_at")),
        "title": (src.get("title") or "").strip() or None,
        "text": clean_html(src.get("text", "") or src.get("description", "")),
        "reply_count": reply_c,
        "like_count": like_c,
        "view_count": src.get("view_count", 0),
        "hot_score": (reply_c or 0) + (like_c or 0),
        "url": f"https://xueqiu.com{target}" if target else None,
    }
    if comments is not None:
        post["top_comments"] = [struct_comment(c) for c in comments]
        post["comment_total"] = list_item.get("reply_count", 0)
    return post


# --------------------------------------------------------------------------- #
#  主流程
# --------------------------------------------------------------------------- #
def scrape(symbol, top, sort, n_comments, with_comments, headless=True):
    exe = find_chromium()
    launch_kwargs = {
        "headless": headless,
        "args": ["--disable-blink-features=AutomationControlled"],
    }
    if exe:
        launch_kwargs["executable_path"] = exe
        print(f"[info] 使用浏览器: {exe}", file=sys.stderr)

    posts = []
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        ctx = browser.new_context(user_agent=UA, locale="zh-CN",
                                  viewport={"width": 1440, "height": 900})
        ctx.add_init_script(STEALTH_JS)
        pg = ctx.new_page()

        def has_token():
            return any(c["name"] == "xq_a_token" for c in ctx.cookies())

        try:
            resp = pg.goto(f"https://xueqiu.com/S/{symbol}",
                           wait_until="networkidle", timeout=45000)
            print(f"[info] 股票页状态: {resp.status if resp else '?'}", file=sys.stderr)
        except Exception as e:
            print(f"[warn] 股票页导航: {e}", file=sys.stderr)

        for _ in range(15):
            pg.wait_for_timeout(1000)
            if has_token():
                break
        if not has_token():
            print("[warn] 未拿到 xq_a_token，接口可能仍被拦截", file=sys.stderr)
        else:
            print("[info] token 就绪，开始拉取热帖列表", file=sys.stderr)

        # 1) 列表
        raw_list = fetch_hot_list(pg, symbol, top, sort)
        print(f"[info] 共取到 {len(raw_list)} 条热帖，逐条加载正文"
              + ("+评论" if with_comments else "") + " ...", file=sys.stderr)

        # 2) 逐条详情 + 评论
        for i, li in enumerate(raw_list, 1):
            pid = li.get("id")
            detail = fetch_detail(pg, pid)
            comments = None
            if with_comments:
                comments = fetch_comments(pg, pid, n_comments)
            posts.append(struct_post(detail, li, comments))
            ncmt = len(comments) if comments else 0
            print(f"[post {i}/{len(raw_list)}] {li.get('reply_count',0)}回复"
                  f" | 正文{'✓' if detail else '✗'} | 评论{ncmt}条", file=sys.stderr)
            pg.wait_for_timeout(1000)  # 控制频率

        browser.close()

    # 热帖按热度排序; 新帖保持时间序
    if sort == "alpha":
        posts.sort(key=lambda x: x["hot_score"], reverse=True)
    return posts


def main():
    ap = argparse.ArgumentParser(
        description="抓取雪球股票热帖(含正文全文+高赞评论), 输出精简结构化 JSON")
    ap.add_argument("symbol", help="股票代码: A股 SH600585/SZ000858, 港股 HK03690, 美股 BABA")
    ap.add_argument("--top", type=int, default=12, help="抓取热帖条数 (默认 12)")
    ap.add_argument("--comments", type=int, default=25,
                    help="每条帖子加载的评论条数 (默认 25)")
    ap.add_argument("--no-comments", action="store_true", help="不加载评论区")
    ap.add_argument("--sort", default="hot",
                    help="hot=热帖(默认) / new=新帖")
    ap.add_argument("--out", default=None, help="输出 JSON 文件路径 (默认打印到 stdout)")
    ap.add_argument("--show", action="store_true", help="显示浏览器窗口(调试)")
    args = ap.parse_args()

    sort = SORT_MAP.get(args.sort, args.sort)
    posts = scrape(args.symbol, args.top, sort, args.comments,
                   with_comments=not args.no_comments, headless=not args.show)

    result = {
        "symbol": args.symbol.upper(),
        "sort": "热帖" if sort == "alpha" else "新帖",
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(posts),
        "posts": posts,
    }
    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"\n已写入 {args.out}，共 {len(posts)} 条热帖", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
