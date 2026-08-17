#!/usr/bin/env python3
"""
抓取雪球的「全市场热榜」：人气热股榜、当日涨幅榜/跌幅榜、成交额榜，
清洗成结构化 JSON，供「选题发现」阶段（阶段零）反推"今天全市场哪些票在热/在被讨论"。

这是选题发现模块唯一新增的脚本——现有 xueqiu_quote.py / xueqiu_hot_posts.py 都要求
先知道股票代码，没有"全市场今天哪些票在热"这一层，本脚本补上这个能力缺口。

用法:
    python3 xueqiu_hot_stocks.py                          # 沪深全部四个榜，各取默认条数
    python3 xueqiu_hot_stocks.py --market cn --top 30
    python3 xueqiu_hot_stocks.py --boards hot,losers --top 20 --out /tmp/hot.json
    python3 xueqiu_hot_stocks.py --market hk --show       # 港股，调试显示浏览器窗口

原理:
    与 xueqiu_quote.py / xueqiu_hot_posts.py 完全一致——雪球接口受阿里云 WAF 保护，
    纯 curl 会被 JS 挑战 / 滑块拦截。这里【整段复用】xueqiu_quote.py 的方案：
    Playwright 驱动真实 Chromium 打开一个股票页过 WAF 拿匿名 token（全站通用），
    再用 ctx.request（复用 WAF cookie、不受 CORS 限制）依次请求各榜单接口。

    榜单接口（可能随雪球风控调整，失效时脚本对单个榜优雅降级，其它榜照常返回；
    实在拿不到就退回 web_search.py 搜"今日涨停/热门板块/龙虎榜"）：
      人气热股  https://stock.xueqiu.com/v5/stock/hot_stock/list.json?size=N&type=<market>
      涨跌幅/成交额  https://stock.xueqiu.com/v5/stock/screener/quote/list.json
                    ?order_by=percent&order=desc&page=1&size=N&type=sha,sza,kcb

注意:
    - 仅作个人研究，请控制频率，避免给对方服务器造成压力。
    - 热榜里的数字是接口当日返回，做选题发现足够；真正写稿时基础行情仍以
      xueqiu_quote.py 对选定个股单独核对为准。
"""
import argparse
import glob
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")

HOT_API = "https://stock.xueqiu.com/v5/stock/hot_stock/list.json"
SCREENER_API = "https://stock.xueqiu.com/v5/stock/screener/quote/list.json"

# 反检测脚本：隐藏 headless / webdriver 特征，降低被风控识别的概率（复用 xueqiu_quote.py）
STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
window.chrome = window.chrome || {runtime: {}};
"""

# 市场 → 各接口参数。hot_stock 用 type 数字口径；screener 用 market + type 字符串口径
# （实测 market=CN&type=sh_sz 才返回数据，缺 market= 会返回空列表）。
MARKET_CONF = {
    "cn": {"hot_type": 12, "screener_market": "CN", "screener_type": "sh_sz",
           "probe_symbol": "SH600519"},   # 用茅台页过 WAF
    "hk": {"hot_type": 30, "screener_market": "HK", "screener_type": "hk",
           "probe_symbol": "HK00700"},     # 用腾讯页过 WAF
    "us": {"hot_type": 11, "screener_market": "US", "screener_type": "us",
           "probe_symbol": "BABA"},
}

# 榜单定义：screener 榜用 order_by 排序方向拉；hot 榜走独立接口。
BOARD_DEFS = {
    "hot":     {"kind": "hot",      "label": "人气热股"},
    "gainers": {"kind": "screener", "label": "涨幅榜", "order_by": "percent", "order": "desc"},
    "losers":  {"kind": "screener", "label": "跌幅榜", "order_by": "percent", "order": "asc"},
    "amount":  {"kind": "screener", "label": "成交额榜", "order_by": "amount", "order": "desc"},
}


# --------------------------------------------------------------------------- #
#  工具函数（复用 xueqiu_quote.py）
# --------------------------------------------------------------------------- #
def round_or_none(v, n=2):
    """数字统一保留 n 位小数，None / 非数字原样返回。"""
    if v is None:
        return None
    try:
        return round(float(v), n)
    except (TypeError, ValueError):
        return v


def humanize_cap(v):
    """把市值(元)换算成「亿」，方便口播直接用。"""
    if v is None:
        return None
    try:
        return round(float(v) / 1e8, 2)
    except (TypeError, ValueError):
        return None


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


def ctx_fetch_json(ctx, url):
    """用 context 的 APIRequestContext 请求，返回 (status, dict|None, raw)。

    榜单接口在 stock.xueqiu.com，与页面 (xueqiu.com) 跨子域，页面内 fetch 会被
    CORS 拦。改用 ctx.request：复用浏览器已拿到的 WAF cookie，但不受 CORS 限制。
    """
    r = ctx.request.get(url, headers={
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": UA,
        "Referer": "https://xueqiu.com/",
    })
    status = r.status
    text = r.text()
    try:
        return status, json.loads(text), ""
    except (ValueError, json.JSONDecodeError):
        return status, None, text[:200]


# --------------------------------------------------------------------------- #
#  结构化
# --------------------------------------------------------------------------- #
def struct_row(item: dict) -> dict:
    """把榜单接口返回的一条精简成做选题发现要用的记录。

    hot_stock 与 screener 两个接口字段名略有差异，这里做归一（取存在的那个）。
    """
    def pick(*keys):
        for k in keys:
            if item.get(k) is not None:
                return item.get(k)
        return None

    market_cap = pick("market_capital", "mc", "total_market_capital")
    amount = pick("amount", "amt")
    return {
        "symbol": pick("symbol", "code"),
        "name": pick("name", "stock_name"),
        "current": round_or_none(pick("current", "current_price", "price")),
        "percent": round_or_none(pick("percent", "pct", "change_percent")),  # 当日涨跌幅 %
        "chg": round_or_none(pick("chg", "change")),
        "market_capital_yi": humanize_cap(market_cap),
        "pe_ttm": round_or_none(pick("pe_ttm", "pettm")),
        "pb": round_or_none(pick("pb")),
        "amount_yi": humanize_cap(amount),                  # 成交额(亿)
        "turnover_rate": round_or_none(pick("turnover_rate", "tr")),
        "follow": pick("follow", "followers", "popularity"),  # 关注/人气(热股榜给)
    }


# --------------------------------------------------------------------------- #
#  榜单抓取
# --------------------------------------------------------------------------- #
def fetch_hot_board(ctx, conf, top):
    url = f"{HOT_API}?size={top}&type={conf['hot_type']}"
    status, body, raw = ctx_fetch_json(ctx, url)
    if status != 200 or not body or body.get("error_code") not in (0, None):
        raise RuntimeError((body or {}).get("error_description") or raw or f"status={status}")
    data = (body or {}).get("data", {}) or {}
    items = data.get("items") or data.get("list") or []
    # 热股榜每条常把行情包在 item['quote'] 或直接铺平，两种都兜住
    rows = []
    for it in items[:top]:
        base = dict(it)
        if isinstance(it.get("quote"), dict):
            base.update(it["quote"])
        rows.append(struct_row(base))
    return rows


def fetch_screener_board(ctx, conf, board, top):
    url = (f"{SCREENER_API}?order_by={board['order_by']}&order={board['order']}"
           f"&page=1&size={top}"
           f"&market={conf['screener_market']}&type={conf['screener_type']}")
    status, body, raw = ctx_fetch_json(ctx, url)
    if status != 200 or not body or body.get("error_code") not in (0, None):
        raise RuntimeError((body or {}).get("error_description") or raw or f"status={status}")
    data = (body or {}).get("data", {}) or {}
    items = data.get("list") or data.get("items") or []
    return [struct_row(it) for it in items[:top]]


def scrape(market, boards, top, headless=True):
    conf = MARKET_CONF[market]
    exe = find_chromium()
    launch_kwargs = {
        "headless": headless,
        "args": ["--disable-blink-features=AutomationControlled"],
    }
    if exe:
        launch_kwargs["executable_path"] = exe
        print(f"[info] 使用浏览器: {exe}", file=sys.stderr)

    result_boards = []
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        ctx = browser.new_context(user_agent=UA, locale="zh-CN",
                                  viewport={"width": 1440, "height": 900})
        ctx.add_init_script(STEALTH_JS)
        pg = ctx.new_page()

        def has_token():
            return any(c["name"] == "xq_a_token" for c in ctx.cookies())

        # 用一只票的页面过 WAF 拿 token（token 全站通用）
        probe = conf["probe_symbol"]
        try:
            resp = pg.goto(f"https://xueqiu.com/S/{probe}",
                           wait_until="networkidle", timeout=45000)
            print(f"[info] 探针页状态: {resp.status if resp else '?'}", file=sys.stderr)
        except Exception as e:
            print(f"[warn] 探针页导航: {e}", file=sys.stderr)

        for _ in range(15):
            pg.wait_for_timeout(1000)
            if has_token():
                break
        if not has_token():
            print("[warn] 未拿到 xq_a_token，接口可能仍被拦截", file=sys.stderr)
        else:
            print("[info] token 就绪，开始拉取榜单", file=sys.stderr)

        for name in boards:
            bd = BOARD_DEFS[name]
            try:
                if bd["kind"] == "hot":
                    rows = fetch_hot_board(ctx, conf, top)
                else:
                    rows = fetch_screener_board(ctx, conf, bd, top)
                result_boards.append({"board": name, "label": bd["label"],
                                      "count": len(rows), "symbols": rows})
                print(f"[board] {bd['label']}: {len(rows)} 条", file=sys.stderr)
            except Exception as e:
                # 单个榜失败优雅降级，其它榜照常返回
                print(f"[warn] {bd['label']} 抓取失败: {e}", file=sys.stderr)
                result_boards.append({"board": name, "label": bd["label"],
                                      "error": str(e), "symbols": []})
            pg.wait_for_timeout(800)  # 控制频率

        browser.close()
    return result_boards


def main():
    ap = argparse.ArgumentParser(
        description="抓取雪球全市场热榜(人气热股/涨幅/跌幅/成交额), 供选题发现阶段反推今天哪些票在热")
    ap.add_argument("--market", default="cn", choices=list(MARKET_CONF.keys()),
                    help="市场: cn 沪深(默认) / hk 港股 / us 美股")
    ap.add_argument("--boards", default="hot,gainers,losers,amount",
                    help="逗号分隔的榜单: hot,gainers,losers,amount (默认全部)")
    ap.add_argument("--top", type=int, default=30, help="每个榜取多少条(默认30)")
    ap.add_argument("--out", default=None, help="输出 JSON 文件路径 (默认打印到 stdout)")
    ap.add_argument("--show", action="store_true", help="显示浏览器窗口(调试)")
    args = ap.parse_args()

    boards = [b.strip() for b in args.boards.split(",") if b.strip() in BOARD_DEFS]
    if not boards:
        print(f"[error] --boards 无有效榜单，可选: {','.join(BOARD_DEFS)}", file=sys.stderr)
        sys.exit(2)

    result_boards = scrape(args.market, boards, args.top, headless=not args.show)

    result = {
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "market": args.market,
        "count": len(result_boards),
        "boards": result_boards,
    }
    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"\n已写入 {args.out}，共 {len(result_boards)} 个榜单", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
