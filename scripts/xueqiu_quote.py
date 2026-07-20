#!/usr/bin/env python3
"""
抓取雪球指定股票的「基础行情数据」：实时股价、涨跌幅、市值、PE/PB/PS、
股息率、52周高低、换手率、EPS 等，清洗成结构化 JSON，供写财经稿时核对
基础数据（关系到观众真金白银，绝不能出量级错误）。

用法:
    python3 xueqiu_quote.py SH600519
    python3 xueqiu_quote.py SZ000858 HK03690 BABA --out /tmp/xq_quote.json
    python3 xueqiu_quote.py SH600519 --show   # 调试时显示浏览器窗口

原理:
    雪球行情数据来自接口:
      行情  https://stock.xueqiu.com/v5/stock/quote.json?symbol=SH600519&extend=detail
    该接口同样受阿里云 WAF 保护，纯 curl 会被 JS 挑战 / 滑块验证拦截。
    这里复用 xueqiu_hot_posts.py 的方案：用 Playwright 驱动真实 Chromium 打开
    股票页，自动通过 WAF 挑战拿到匿名 token，再在【页面上下文内】fetch 接口——
    请求天然带合法 cookie，不触发滑块。

注意:
    - 一次可传多个代码，脚本会依次抓取（共用同一个浏览器会话，省去重复过风控）。
    - PE/PB 等估值指标，A股/港股/美股字段口径可能略有差异，脚本尽量做归一。
    - 仅作个人研究，请控制频率，避免给对方服务器造成压力。
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

QUOTE_API = "https://stock.xueqiu.com/v5/stock/quote.json"

# 反检测脚本：隐藏 headless / webdriver 特征，降低被风控识别的概率
STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
window.chrome = window.chrome || {runtime: {}};
"""


# --------------------------------------------------------------------------- #
#  工具函数
# --------------------------------------------------------------------------- #
def fmt_time(ts):
    if not ts:
        return None
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts / 1000))
    except Exception:
        return None


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


def api_symbol(symbol: str) -> str:
    """接口 symbol 参数格式与页面 URL 不同：
       - A股: 页面/接口都用 SH600519 / SZ000858
       - 港股: 页面用 HK03690，但行情接口要用纯数字 03690 (去掉 HK 前缀) 才有数据
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


def ctx_fetch_json(ctx, url):
    """用 context 的 APIRequestContext 请求，返回 (status, dict|None, raw)。

    行情接口在 stock.xueqiu.com，与页面 (xueqiu.com) 跨子域，页面内 fetch 会被
    CORS 拦（Failed to fetch）。改用 ctx.request：它复用浏览器已拿到的 WAF cookie，
    但不受浏览器 CORS 限制，能直接拿到 stock.xueqiu.com 的 JSON。
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
def struct_quote(symbol: str, body: dict) -> dict:
    """把 quote.json 的返回精简成一条写稿要用的基础数据记录。"""
    data = (body or {}).get("data", {}) or {}
    q = data.get("quote", {}) or {}
    market = data.get("market", {}) or {}

    market_cap = q.get("market_capital")
    float_cap = q.get("float_market_capital")

    return {
        "symbol": symbol.upper(),
        "name": q.get("name"),
        "exchange": q.get("exchange"),
        "currency": q.get("currency"),
        "market_status": market.get("status"),
        "timestamp": fmt_time(q.get("timestamp")),
        # ---- 价格与涨跌 ----
        "current": round_or_none(q.get("current")),
        "percent": round_or_none(q.get("percent")),          # 当日涨跌幅 %
        "chg": round_or_none(q.get("chg")),                  # 当日涨跌额
        "last_close": round_or_none(q.get("last_close")),
        "open": round_or_none(q.get("open")),
        "high": round_or_none(q.get("high")),
        "low": round_or_none(q.get("low")),
        "high52w": round_or_none(q.get("high52w")),          # 52周最高
        "low52w": round_or_none(q.get("low52w")),            # 52周最低
        "amplitude": round_or_none(q.get("amplitude")),      # 当日振幅 %
        # ---- 市值与股本 ----
        "market_capital": market_cap,                        # 总市值(元)
        "market_capital_yi": humanize_cap(market_cap),       # 总市值(亿)
        "float_market_capital_yi": humanize_cap(float_cap),  # 流通市值(亿)
        "total_shares": q.get("total_shares"),
        "float_shares": q.get("float_shares"),
        # ---- 估值指标 ----
        "pe_ttm": round_or_none(q.get("pe_ttm")),            # 市盈率(TTM)
        "pe_lyr": round_or_none(q.get("pe_lyr")),            # 市盈率(静态)
        "pe_forecast": round_or_none(q.get("pe_forecast")),  # 市盈率(动态/预测)
        "pb": round_or_none(q.get("pb")),                    # 市净率
        "ps": round_or_none(q.get("ps")),                    # 市销率
        "dividend_yield": round_or_none(q.get("dividend_yield")),  # 股息率 %
        # ---- 每股指标 ----
        "eps": round_or_none(q.get("eps"), 4),               # 每股收益
        "navps": round_or_none(q.get("navps"), 4),           # 每股净资产
        # ---- 成交 ----
        "volume": q.get("volume"),                           # 成交量(股)
        "amount": q.get("amount"),                           # 成交额(元)
        "turnover_rate": round_or_none(q.get("turnover_rate")),  # 换手率 %
        "volume_ratio": round_or_none(q.get("volume_ratio")),    # 量比
    }


# --------------------------------------------------------------------------- #
#  主流程
# --------------------------------------------------------------------------- #
def scrape(symbols, headless=True):
    exe = find_chromium()
    launch_kwargs = {
        "headless": headless,
        "args": ["--disable-blink-features=AutomationControlled"],
    }
    if exe:
        launch_kwargs["executable_path"] = exe
        print(f"[info] 使用浏览器: {exe}", file=sys.stderr)

    quotes = []
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        ctx = browser.new_context(user_agent=UA, locale="zh-CN",
                                  viewport={"width": 1440, "height": 900})
        ctx.add_init_script(STEALTH_JS)
        pg = ctx.new_page()

        def has_token():
            return any(c["name"] == "xq_a_token" for c in ctx.cookies())

        # 用第一只票的页面过 WAF 拿 token（token 全站通用）
        first = symbols[0]
        try:
            resp = pg.goto(f"https://xueqiu.com/S/{first}",
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
            print("[info] token 就绪，开始拉取行情", file=sys.stderr)

        for i, sym in enumerate(symbols, 1):
            url = f"{QUOTE_API}?symbol={api_symbol(sym)}&extend=detail"
            status, body, raw = ctx_fetch_json(ctx, url)
            if status != 200 or not body or body.get("error_code") not in (0, None):
                errmsg = (body or {}).get("error_description") or raw
                print(f"[warn] {sym} 行情抓取失败 status={status}: {errmsg!r}",
                      file=sys.stderr)
                quotes.append({"symbol": sym.upper(), "error": errmsg or f"status={status}"})
            else:
                rec = struct_quote(sym, body)
                quotes.append(rec)
                print(f"[quote {i}/{len(symbols)}] {rec.get('name')} "
                      f"现价 {rec.get('current')} ({rec.get('percent')}%) "
                      f"PE(TTM) {rec.get('pe_ttm')} 市值 {rec.get('market_capital_yi')}亿",
                      file=sys.stderr)
            pg.wait_for_timeout(800)  # 控制频率

        browser.close()
    return quotes


def main():
    ap = argparse.ArgumentParser(
        description="抓取雪球股票基础行情数据(股价/涨跌幅/市值/PE/PB/PS等), 输出结构化 JSON")
    ap.add_argument("symbols", nargs="+",
                    help="股票代码(可多个): A股 SH600519/SZ000858, 港股 HK03690, 美股 BABA")
    ap.add_argument("--out", default=None, help="输出 JSON 文件路径 (默认打印到 stdout)")
    ap.add_argument("--show", action="store_true", help="显示浏览器窗口(调试)")
    args = ap.parse_args()

    quotes = scrape(args.symbols, headless=not args.show)

    result = {
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(quotes),
        "quotes": quotes,
    }
    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"\n已写入 {args.out}，共 {len(quotes)} 条行情", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
