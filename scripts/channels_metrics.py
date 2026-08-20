#!/usr/bin/env python3
"""
视频号（微信）创作者后台数据自动抓取 → 落盘到 workspace/账号数据/视频号.md（单文件）。

与抖音（douyin_account.py + douyin_metrics.py 两套）不同，视频号一个脚本一次抓全：
    · 账号总览：总粉丝数 + 近 7 天分流量来源的互动汇总
    · 全部视频：每条视频的播放/点赞/评论/转发/收藏/涨粉/完播率/平均时长/快划率/昨日播放

原理（同抖音那套的思路）：
    视频号助手（channels.weixin.qq.com）是 SPA，数字来自登录态签名接口。纯 requests
    无法自己算签名，所以用 Playwright 注入会话 cookie 打开后台页面，让页面自己发这些
    带签名的请求，我们在 response 事件里把 JSON 截下来解析。三个关键接口：
        - statistic/get-finder-total-statics  → 账号总粉丝数 fansNum
        - statistic/new_post_total_data        → 近 7 天分来源(关注/推荐/分享/主页…)逐日序列
        - post/post_list                       → 全部视频的聚合指标（一次返回，无需逐条点开）

用法：
    python3 channels_metrics.py                # 抓取并落盘 workspace/账号数据/视频号.md
    python3 channels_metrics.py --dry-run      # 只打印不落盘
    python3 channels_metrics.py --save-raw     # 额外归档原始 JSON
    python3 channels_metrics.py --show         # 显示浏览器窗口（调试）

cookie：
    读技能根目录 .channels_cookie（已 gitignore，chmod 600）。cookie 过期会抓到空数据，
    报错后重新从浏览器复制 document.cookie 覆盖该文件即可，脚本不用改。

依赖：
    pip install playwright   （复用 ms-playwright 的 Chromium 内核）
"""
import argparse
import glob
import json
import os
import sys
from datetime import datetime, timedelta
from http.cookies import SimpleCookie

from playwright.sync_api import sync_playwright

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COOKIE_FILE = os.path.join(SKILL_DIR, ".channels_cookie")
ACCOUNT_DIR = os.path.join(SKILL_DIR, "workspace", "账号数据")
OUT_MD = os.path.join(ACCOUNT_DIR, "视频号.md")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36")

ACCOUNT_URL = "https://channels.weixin.qq.com/platform/statistic/post"
POSTLIST_URL = "https://channels.weixin.qq.com/platform/post/list"

# new_post_total_data 的流量来源 tabType → 中文（对齐后台「流量来源」）
TAB_LABELS = {
    3: "关注", 4: "推荐", 6: "分享", 20: "主页", 8: "朋友",
    16: "订阅号消息", 15: "PC微信", 25: "看一看", 0: "其他",
}
# 每个来源里可用的互动子指标 → 中文
SRC_METRICS = [
    ("browse", "播放"), ("like", "点赞"), ("comment", "评论"),
    ("forward", "转发"), ("fav", "收藏"), ("follow", "涨粉"),
]

# post_list 单条视频字段 → (中文标签, 类型)。type: int=计数, pct=百分比小数, sec=秒
VIDEO_FIELDS = [
    ("readCount",         "播放",       "int"),
    ("likeCount",         "点赞",       "int"),
    ("commentCount",      "评论",       "int"),
    ("forwardCount",      "转发",       "int"),
    ("favCount",          "收藏",       "int"),
    ("followCount",       "涨粉",       "int"),
    ("fullPlayRate",      "完播率",     "pct"),
    ("avgPlayTimeSec",    "平均时长",   "sec"),
    ("fastFlipRate",      "快划率",     "pct"),
    ("yesterdayReadCount","昨日播放",   "int"),
]


def find_chromium():
    env = os.environ.get("PW_CHROMIUM")
    if env and os.path.exists(env):
        return env
    pats = [
        os.path.expanduser("~/Library/Caches/ms-playwright/chromium-*/chrome-mac*/*.app/Contents/MacOS/Google Chrome for Testing"),
        os.path.expanduser("~/Library/Caches/ms-playwright/chromium-*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium"),
        os.path.expanduser("~/Library/Caches/ms-playwright/chromium-*/chrome-linux/chrome"),
    ]
    for p in pats:
        hits = sorted(glob.glob(p), reverse=True)
        if hits:
            return hits[0]
    return None


def parse_cookies(raw):
    """视频号 cookie 覆盖 .weixin.qq.com 与 .qq.com 两个域。"""
    ck = SimpleCookie()
    ck.load(raw)
    out = []
    for k, m in ck.items():
        for dom in (".weixin.qq.com", ".qq.com"):
            out.append({"name": k, "value": m.value, "domain": dom, "path": "/"})
    return out


def fmt(val, typ):
    if val is None or val == "":
        return "-"
    try:
        f = float(val)
    except (TypeError, ValueError):
        return str(val)
    if typ == "int":
        return f"{int(round(f)):,}"
    if typ == "pct":
        return f"{f * 100:.2f}%"
    if typ == "sec":
        return f"{f:.1f}s"
    return str(val)


def scrape(headless=True, wait=12):
    """被动截获两张后台页面自己发出的接口 JSON，返回 dict。"""
    raw = open(COOKIE_FILE, encoding="utf-8").read().strip()
    cookies = parse_cookies(raw)
    print(f"[channels] 加载 {len(cookies) // 2} 个 cookie（双域注入）", file=sys.stderr)

    captured = {"fans": None, "post_total": None, "videos": {}}

    def on_response(resp):
        u = resp.url
        try:
            if "statistic/get-finder-total-statics" in u:
                captured["fans"] = resp.json().get("data")
            elif "statistic/new_post_total_data" in u:
                body = resp.json().get("data") or {}
                # 取字段最全的一次（含 dataByTabtype 全来源）
                if body.get("dataByTabtype") and (
                    not captured["post_total"]
                    or len(json.dumps(body)) > len(json.dumps(captured["post_total"]))
                ):
                    captured["post_total"] = body
            elif "post/post_list" in u:
                for v in (resp.json().get("data", {}).get("list") or []):
                    oid = v.get("objectId")
                    # collection 条目没有 readCount，跳过
                    if oid and "readCount" in v:
                        captured["videos"][oid] = v
        except Exception:
            pass

    exe = find_chromium()
    kw = {"headless": headless, "args": ["--disable-blink-features=AutomationControlled"]}
    if exe:
        kw["executable_path"] = exe
        print(f"[channels] 浏览器: {exe}", file=sys.stderr)

    with sync_playwright() as p:
        b = p.chromium.launch(**kw)
        ctx = b.new_context(user_agent=UA, locale="zh-CN",
                            viewport={"width": 1600, "height": 1000})
        ctx.add_cookies(cookies)
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
        pg = ctx.new_page()
        pg.on("response", on_response)
        try:
            # 1) 账号数据页：自动触发 get-finder-total-statics + new_post_total_data
            pg.goto(ACCOUNT_URL, wait_until="domcontentloaded", timeout=60000)
            pg.wait_for_timeout(wait * 1000)
            pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            pg.wait_for_timeout(3000)

            # 2) 作品列表页：自动触发 post_list（一次返回全部视频指标），滚动翻页兜底
            pg.goto(POSTLIST_URL, wait_until="domcontentloaded", timeout=60000)
            pg.wait_for_timeout(wait * 1000)
            for _ in range(6):
                pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                pg.wait_for_timeout(2500)
        finally:
            b.close()

    if not captured["videos"]:
        raise RuntimeError("未抓到 post_list 视频数据 —— cookie 可能已过期，"
                           "请重新从浏览器复制 document.cookie 覆盖 .channels_cookie")
    return captured


def build_markdown(data):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    fans = (data.get("fans") or {}).get("fansNum")
    videos = list(data["videos"].values())
    # 按播放降序
    videos.sort(key=lambda v: int(v.get("readCount") or 0), reverse=True)

    out = []
    out.append("# 视频号数据（财经蛋炒饭 · 视频号）\n")
    out.append(f"\n> 最近更新：{stamp}　｜　抓取脚本：scripts/channels_metrics.py（自动抓取，视频号助手后台）\n")
    out.append(f"> 口径：账号总览为当前累计，视频指标为各条累计值　｜　共 {len(videos)} 条视频\n\n")

    # 账号总览
    out.append("## 账号总览\n\n")
    out.append("| 指标 | 数值 |\n| --- | --- |\n")
    out.append(f"| 总粉丝数 | {fmt(fans, 'int')} |\n")
    out.append(f"| 视频总数 | {len(videos)} |\n")

    pt = data.get("post_total") or {}
    total = pt.get("totalData") or {}
    if total:
        out.append("\n### 近 7 天互动合计（全部来源）\n\n")
        out.append("| 指标 | 近7天合计 |\n| --- | --- |\n")
        for key, label in SRC_METRICS:
            seq = total.get(key) or []
            s = sum(int(x) for x in seq if str(x).lstrip("-").isdigit())
            out.append(f"| {label} | {s:,} |\n")

    # 分流量来源（近 7 天各来源播放合计 + 占比）
    tabs = pt.get("dataByTabtype") or []
    if tabs:
        rows = []
        for t in tabs:
            br = t.get("data", {}).get("browse") or []
            s = sum(int(x) for x in br if str(x).lstrip("-").isdigit())
            rows.append((TAB_LABELS.get(t.get("tabType"), str(t.get("tabType"))), s))
        grand = sum(s for _, s in rows) or 1
        rows.sort(key=lambda r: r[1], reverse=True)
        out.append("\n### 近 7 天播放来源占比\n\n")
        out.append("| 来源 | 播放 | 占比 |\n| --- | --- | --- |\n")
        for name, s in rows:
            out.append(f"| {name} | {s:,} | {s / grand * 100:.1f}% |\n")

    # 近 7 天逐日播放（totalData.browse，旧→新，末位=最近一天）
    if total.get("browse"):
        seq = total["browse"]
        n = len(seq)
        today = datetime.now().date()
        out.append("\n### 近 7 天逐日播放\n\n")
        out.append("| 日期 | 播放 | 点赞 | 评论 | 转发 | 涨粉 |\n| --- | --- | --- | --- | --- | --- |\n")
        for i in range(n):
            d = today - timedelta(days=(n - 1 - i))
            row = [d.strftime("%m-%d")]
            for key, _ in [("browse", ""), ("like", ""), ("comment", ""), ("forward", ""), ("follow", "")]:
                s = (total.get(key) or [])
                row.append(f"{int(s[i]):,}" if i < len(s) and str(s[i]).lstrip('-').isdigit() else "-")
            out.append("| " + " | ".join(row) + " |\n")

    # 视频明细
    out.append("\n## 视频明细（按播放降序）\n\n")
    header = "| # | 视频 | " + " | ".join(l for _, l, _ in VIDEO_FIELDS) + " | 发布时间 |"
    out.append(header + "\n")
    out.append("| --- | --- | " + " | ".join(["---"] * len(VIDEO_FIELDS)) + " | --- |\n")
    for i, v in enumerate(videos, 1):
        desc = (v.get("desc") or {}).get("description") or ""
        title = desc.split("\n")[0].replace("|", "｜").strip()[:24]
        ts = v.get("createTime")
        pub = datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d") if ts else "-"
        cells = [str(i), title]
        for key, _, typ in VIDEO_FIELDS:
            cells.append(fmt(v.get(key), typ))
        cells.append(pub)
        out.append("| " + " | ".join(cells) + " |\n")

    out.append("\n> 说明：完播率=完整看完占比，平均时长=人均观看秒数，快划率=开头快速划走占比（越低越好）。\n")
    return "".join(out)


def main():
    ap = argparse.ArgumentParser(description="视频号后台数据 → workspace/账号数据/视频号.md")
    ap.add_argument("--show", action="store_true", help="显示浏览器窗口（调试）")
    ap.add_argument("--wait", type=int, default=12, help="每页加载后等待秒数（默认 12）")
    ap.add_argument("--dry-run", action="store_true", help="只打印结果，不落盘")
    ap.add_argument("--save-raw", action="store_true", help="把原始 JSON 存到账号数据 raw/ 下")
    args = ap.parse_args()

    data = scrape(headless=not args.show, wait=args.wait)
    md = build_markdown(data)

    if args.dry_run:
        sys.stdout.write(md)
        return

    os.makedirs(ACCOUNT_DIR, exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"已写入：{OUT_MD}")

    if args.save_raw:
        raw_dir = os.path.join(ACCOUNT_DIR, "raw")
        os.makedirs(raw_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_path = os.path.join(raw_dir, f"channels_raw_{stamp}.json")
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已归档原始 JSON：{raw_path}")


if __name__ == "__main__":
    main()
