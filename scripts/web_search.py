#!/usr/bin/env python3
"""
联网搜索（走 B站 qianfan ai_search 网关，替代 Claude Code/Codex 自带的 WebSearch）。

一次可传多个查询，脚本会并行发起，把每条查询的搜索结果清洗成结构化 JSON——
每条结果带标题、链接、来源站点、日期、摘要(snippet)和正文全文(content)。因为返回
里已经包含正文全文，写财经稿时通常不需要再单独抓网页（即同时替代了 WebFetch）。

用法:
    python3 web_search.py "贵州茅台 最新股价"
    python3 web_search.py "宁德时代 财报 2026" "宁德时代 机构评级" --top-k 8 --out /tmp/web.json
    python3 web_search.py "英伟达 业绩" --no-content   # 只要摘要不要正文全文，输出更精简

API key 读取顺序（与 generate_cover.py 一致）:
    1. 环境变量 QIANFAN_SEARCH_API_KEY（优先，方便临时覆盖）
    2. skill 目录下的 .env 文件里的 QIANFAN_SEARCH_API_KEY=xxx（兜底，免去每次 export）
    .env 已在 .gitignore 中，不会被提交。

依赖: 仅标准库（urllib），无需额外安装。
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

GATEWAY_URL = "http://pre-qianfan.bilibili.co/v2/ai_search/web_search"
SEARCH_SOURCE = "baidu_search_v2"


def _load_api_key():
    """按优先级读取 API key：环境变量 > skill 目录下的 .env。"""
    key = os.environ.get("QIANFAN_SEARCH_API_KEY")
    if key:
        return key.strip()
    # 兜底：读取 skill 根目录（本脚本上一级）下的 .env
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, _, value = line.partition("=")
                if name.strip() == "QIANFAN_SEARCH_API_KEY":
                    return value.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return None


def _search_one(query, api_key, top_k, want_content, timeout):
    """对单条查询发起搜索，返回 (query, results_list, error_or_None)。"""
    payload = {
        "search_source": SEARCH_SOURCE,
        "resource_type_filter": [{"type": "web", "top_k": top_k}],
        "messages": [{"content": query, "role": "user"}],
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        GATEWAY_URL,
        data=body,
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:200]
        return query, [], "HTTP %s: %s" % (e.code, detail)
    except Exception as e:  # 网络超时、DNS 等
        return query, [], str(e)

    try:
        data = json.loads(raw)
    except (ValueError, json.JSONDecodeError):
        return query, [], "返回非 JSON: " + raw[:200]

    refs = data.get("references") or []
    results = []
    for r in refs:
        item = {
            "title": r.get("title"),
            "url": r.get("url"),
            "website": r.get("website"),
            "date": r.get("date"),
            "snippet": r.get("snippet"),
        }
        if want_content:
            item["content"] = r.get("content")
        results.append(item)
    return query, results, None


def search(queries, api_key, top_k=10, want_content=True, timeout=40):
    """并行搜索多条查询，返回与 queries 顺序一致的结果列表。"""
    out = [None] * len(queries)
    with ThreadPoolExecutor(max_workers=min(8, len(queries))) as pool:
        futures = {
            pool.submit(_search_one, q, api_key, top_k, want_content, timeout): i
            for i, q in enumerate(queries)
        }
        for fut in futures:
            i = futures[fut]
            query, results, err = fut.result()
            entry = {"query": query, "count": len(results), "results": results}
            if err:
                entry["error"] = err
                print("[warn] 查询 %r 失败: %s" % (query, err), file=sys.stderr)
            else:
                print("[ok] 查询 %r 命中 %d 条" % (query, len(results)), file=sys.stderr)
            out[i] = entry
    return out


def main():
    ap = argparse.ArgumentParser(
        description="联网搜索(走 B站 qianfan 网关), 输出结构化 JSON, 替代自带 WebSearch/WebFetch")
    ap.add_argument("queries", nargs="+", help="搜索查询(可传多个, 会并行发起)")
    ap.add_argument("--top-k", type=int, default=10, help="每条查询返回多少条结果(默认10)")
    ap.add_argument("--no-content", action="store_true",
                    help="只要标题/摘要, 不要正文全文(输出更精简)")
    ap.add_argument("--timeout", type=int, default=40, help="单条查询超时秒数(默认40)")
    ap.add_argument("--out", default=None, help="输出 JSON 文件路径 (默认打印到 stdout)")
    args = ap.parse_args()

    api_key = _load_api_key()
    if not api_key:
        print(
            "错误：未找到 QIANFAN_SEARCH_API_KEY。\n"
            "请二选一：export QIANFAN_SEARCH_API_KEY=你的key，"
            "或在 skill 目录下的 .env 里写入 QIANFAN_SEARCH_API_KEY=你的key。",
            file=sys.stderr,
        )
        return 1

    searches = search(
        args.queries, api_key,
        top_k=args.top_k,
        want_content=not args.no_content,
        timeout=args.timeout,
    )

    result = {"count": len(searches), "searches": searches}
    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        print("\n已写入 %s，共 %d 条查询" % (args.out, len(searches)), file=sys.stderr)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
