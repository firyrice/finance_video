# 数据采集脚本手册（创作阶段用的四个抓取脚本）

本文件是创作阶段（阶段零～阶段二）四个采集脚本的完整用法与输出结构。SKILL 正文只保留"何时用哪个 + 一行命令 + 归档到哪"，参数、JSON 字段、怎么用都查这里。

**通用约定：**

- 脚本随技能安装在技能目录 `scripts/` 下。运行前先定位技能目录，用绝对路径调用（Codex/Claude Code 运行时 cwd 通常是用户项目目录，别假设就是技能目录）：
  ```bash
  SKILL_DIR="$HOME/.claude/skills/bilibili-finance-video"
  [ -d "$SKILL_DIR" ] || SKILL_DIR="$HOME/.codex/skills/bilibili-finance-video"
  ```
  下文示例为简洁写成 `scripts/xxx.py`，实际调用替换为 `"$SKILL_DIR/scripts/xxx.py"`。
- **归档铁律**：阶段一及以后，所有 `--out` 一律指向该视频的 `参考资料/抓取数据/xxx.json`，不写 `/tmp`（唯一例外是阶段零选题发现，那时还没有视频文件夹，才写 `/tmp`）。别覆盖前一轮抓取——同名文件已存在就加后缀（如 `web_search_阶段二.json`），每轮留档。
- 脚本报错或拿不到结果时，如实告知用户无法获取该数据，**不要用记忆里的旧数据冒充**。

---

## 1. web_search.py — 联网搜索（替代自带 WebSearch）

新闻、财报、研报、行业、政策这类**非实时定性信息**，一律用本脚本，**不要调用 Claude Code / Codex 自带的 WebSearch**。走 B站 qianfan 搜索网关，一次可并行跑多条查询，返回带标题、链接、来源站点、日期、摘要和**正文全文**的结构化 JSON——因为已含正文全文，通常不用再单独抓网页。

```bash
# 一次多条查询并行发起，最省时间：
python3 scripts/web_search.py \
  "贵州茅台 2026 最新财报 营收 净利润" \
  "贵州茅台 机构评级 研报 最新" \
  "白酒行业 2026 景气度 政策" \
  --top-k 10 --out /tmp/web.json

python3 scripts/web_search.py "贵州茅台 雪球 代码" --no-content   # 只要摘要、不要正文
```

- **参数**：`--top-k` 每条查询返回多少条（默认10），`--no-content` 只要标题/摘要不要正文全文（查代码、快速定位时用），`--timeout` 单条超时秒数（默认40），`--out` 写到文件。
- 需要 API key `QIANFAN_SEARCH_API_KEY`，读取顺序：环境变量 > skill 目录下 `.env`（已内置，一般无需再设）。
- 若脚本报错或某条查询 `error` 字段非空（网络/网关波动），隔几十秒重试；实在拿不到就如实告知用户。
- **搜非实时信息时务必在查询里带上当前日期或"最新""2026"等词**，确保拿到写稿当日的数据，而不是训练记忆里的旧数据。

**输出结构：**

```json
{
  "count": 2,
  "searches": [
    {
      "query": "贵州茅台 2026 最新财报",
      "count": 10,
      "results": [
        {
          "title": "标题", "url": "链接", "website": "来源站点",
          "date": "2026-07-30 17:53:28",
          "snippet": "摘要", "content": "正文全文(已清洗，--no-content 时不含此字段)"
        }
      ]
    }
  ]
}
```

看 `date` 判断信息新旧（优先用近日的），`content` 是正文全文可直接提炼进文稿，`url`/`website` 用来标注来源。

---

## 2. web_fetch.py — 抓取单个网页正文（替代自带 WebFetch）

当用户给了一个特定网页链接（雪球深度帖、东方财富研报、公司公告页等），需要精读那一篇全文时用本脚本，**不要用自带 WebFetch**——后者对雪球、东财等有阿里云 WAF 的站点拿不到正文，只会返回 JS 挑战码。

```bash
# 基本用法（自动智能设置 referer）
python3 scripts/web_fetch.py "https://xueqiu.com/1062170191/404008951" --out /tmp/wf.json

# 指定正文 CSS 选择器、延长等待时间（JS 渲染重的页面）
python3 scripts/web_fetch.py "https://finance.sina.com.cn/..." --selector "article" --wait 8 --out /tmp/wf.json

# 手动指定 referer（自动推断不准确时）
python3 scripts/web_fetch.py "https://xueqiu.com/xxx/yyy" --referer "https://xueqiu.com" --out /tmp/wf.json

# 只打 stdout、不写文件
python3 scripts/web_fetch.py "https://xueqiu.com/1062170191/404008951"
```

- **原理**：Playwright 驱动真实 Chromium 过 WAF，与 `xueqiu_hot_posts.py` 共用同一套浏览器查找逻辑和反检测脚本。首次运行要过 WAF 挑战，比 curl 慢几秒，但能拿到真实正文。
- **智能 referer**：脚本对雪球、东财等已知 WAF 站点自动先访问首页拿合法 cookie，再抓目标页，无需手动 `--referer`。
- **自动正文探测**：不指定 `--selector` 时，脚本按常见财经站点模板（雪球 `article`、新浪 `.article-content`、公众号 `.rich_media_content` 等）依次尝试，取第一个有内容的容器。
- **参数**：`--selector` CSS 选择器，`--wait` 加载等待秒数（默认 5），`--referer` 手动指定 referer 页，`--out` 输出文件路径，`--show` 显示浏览器窗口调试。
- 依赖与 `xueqiu_hot_posts.py` 完全相同（`playwright` + `beautifulsoup4` + `lxml` + 已缓存的 Chromium），无需额外安装。
- 若脚本报错或 WAF 升级拿不到内容，如实告知用户。

**输出结构：**

```json
{
  "url": "https://xueqiu.com/1062170191/404008951",
  "title": "5800字拆解宇树科技，那些招股书没讲的事儿",
  "text": "正文全文(已清洗为纯文本) ...",
  "text_length": 6611,
  "fetched_at": "2026-08-08 15:20:00",
  "status": "ok"
}
```

**用户往 `参考资料/` 丢受 WAF 保护的页面（雪球/东财等）时也用这个脚本抓正文**，拿到纯文字后整理成一篇 `.md` 写进 `参考资料/` 根下，别只存链接。

---

## 3. xueqiu_quote.py — 雪球基础行情（股价类数据的唯一权威源）

股价、市值、估值这类实时数字，搜索结果和训练记忆都不可靠，**必须以雪球行情接口为准**——这是财经稿的第一红线，搜索/记忆里的股价经常过时或错乱。跑这个脚本一次性拿到干净的结构化基础数据：

```bash
python3 scripts/xueqiu_quote.py SH600519 --out /tmp/xq_quote.json
# 也可一次传多个代码(做对比型选题时很方便)，共用一个浏览器会话：
python3 scripts/xueqiu_quote.py SZ300750 SH600519 HK03690 BABA --out /tmp/xq_quote.json
```

- **股票代码格式**：A股 `SH600519` / `SZ000858`，港股 `HK03690`（脚本会自动去掉 `HK` 前缀调接口），美股 `BABA`。不确定代码就先跑 `web_search.py` 搜 "<股票名> 雪球 代码"。
- 脚本用 Playwright 过阿里云 WAF 拿匿名 token，**首次运行较慢属正常**；拿到 token 后多个代码依次抓取，很快。依赖与 `xueqiu_hot_posts.py` 完全相同，已装过热帖脚本就无需再装。
- 若报「未拿到 xq_a_token」或抓取失败，多半是网络/风控波动，隔几十秒重试；实在拿不到就退回用 `web_search.py` 交叉核对，并在稿子里对存疑数字保持谨慎。

**输出结构**（每只股票一条，字段已归一，直接喂给自己写稿）：

```json
{
  "fetched_at": "2026-07-20 13:20:33", "count": 1,
  "quotes": [
    {
      "symbol": "SH600519", "name": "贵州茅台", "currency": "CNY",
      "market_status": "交易中", "timestamp": "2026-07-20 13:20:27",
      "current": 1324.58, "percent": 5.71, "chg": 71.58,
      "last_close": 1253.0, "open": 1270.0, "high": 1329.0, "low": 1266.0,
      "high52w": 1531.75, "low52w": 1151.01, "amplitude": 5.03,
      "market_capital_yi": 16558.33, "float_market_capital_yi": 16558.33,
      "total_shares": 1250081601,
      "pe_ttm": 20.02, "pe_lyr": 20.11, "pe_forecast": 15.2,
      "pb": 6.12, "ps": null, "dividend_yield": 3.93,
      "eps": 66.17, "navps": 216.32,
      "turnover_rate": 0.64, "volume_ratio": 2.59
    }
  ]
}
```

**怎么用这份数据：**
- `current`/`percent`/`chg` 是当日股价、涨跌幅、涨跌额；`market_capital_yi` 是总市值(亿)，口播直接说"市值一万六千多亿"。
- `pe_ttm`(滚动市盈率)/`pe_lyr`(静态)/`pe_forecast`(动态) 三个口径都给了，讲估值时说清用的哪个；`pb` 市净率、`dividend_yield` 股息率、`high52w`/`low52w` 判断当前处于一年区间的什么位置。
- 负的 `pe_ttm` 表示公司 TTM 亏损（如美团 -12），别当成"低估"讲反。
- 港股/美股部分字段(如股息率、PS)可能为 `null`，属正常，标"未获取到"即可，别编。

---

## 4. xueqiu_hot_posts.py — 雪球热帖（一手散户情绪与观点）

`web_search.py` 抓的是新闻和研报，拿不到散户在讨论什么。雪球评论区的热帖是**发现选题、找争议钩子、判断多空分歧**的一手素材——哪条帖子几百回复、评论区在吵什么，往往就是这只股票当下最真实的情绪焦点。**每次抓数据时都要抓一次热帖。**

脚本默认口径已对齐网页「热帖」tab：**热帖 + 最近 30 天 + 前 5 条帖子 + 每帖前 5 条高赞评论**（`--top 5 --comments 5 --days 30`，全是默认值，直接跑即可）。这份数据两个用途：① 发现选题、找争议钩子；② 写稿时直接引用帖子和评论里的真实观点，提升稿件质量、减少 AI 感。

### 铁律：必须派子 agent 抓 + 消化，主 agent 不直接读原始 JSON

原因：5 条热帖全文 + 每条 5 条评论，原始 JSON 仍有上万字，直接读进主上下文会挤占后续写稿空间。用 Task/Agent 工具起一个子 agent（Codex 映射到等价子任务能力），让它跑脚本、读原始 JSON、消化，只回传一份**结构化摘要 + 可引用原声**——原始全文烂在子 agent 上下文里。

**派给「雪球热帖情绪分析子 agent」的任务指令**（照此措辞下发，**并把这支视频的文件夹绝对路径 `<视频文件夹>` 一并给它**，形如 `$SKILL_DIR/workspace/2026-08-20_药明康德`）：

> 你是雪球热帖情绪分析助手，让原始 JSON 和消化后的摘要都落到这支视频名下。请：
> 1. 定位技能目录：`SKILL_DIR="$HOME/.claude/skills/bilibili-finance-video"; [ -d "$SKILL_DIR" ] || SKILL_DIR="$HOME/.codex/skills/bilibili-finance-video"`
> 2. 跑 `python3 "$SKILL_DIR/scripts/xueqiu_hot_posts.py" <雪球代码> --out "<视频文件夹>/参考资料/抓取数据/xueqiu_hot_posts.json"`（默认即抓「热帖」tab近30天前5条、每帖5条高赞评论；首次较慢属正常；报错或长时间卡住隔几十秒重试一次，仍失败就在回传里注明"雪球热帖未获取到"）
> 3. 读该 JSON，消化成一份**结构化摘要 + 可引用原声**，做两件落地：
>    - **把这份摘要写成 `<视频文件夹>/参考资料/雪球热帖-摘要.md`**（原始 JSON 已在 `抓取数据/` 留档，此处只放消化后的摘要；文件顶部标注股票名、雪球代码、抓取日期）。
>    - **把同一份摘要回传主 agent**（原始 JSON 不整包回传）。
>    字数不用卡太死：摘要 3000 字以内都可以，重要的散户原声、争议帖段落可直接摘原文引用（别转述丢味），但**回传/落盘总量控制在 5000 字以内**——挑最有代入感、最能当钩子的引。摘要含这几块：
>    - **情绪总基调**：当前多空大致比例、整体是恐慌/亢奋/纠结/观望
>    - **争议焦点**：散户在吵的具体问题（每条一句话，可作选题钩子），有几个列几个
>    - **可引用的高赞原声**：直接摘录评论/帖子原句 + 点赞数 + IP 属地，用于写稿代入；写稿用得上的多摘几条，宁可原声多也别干巴巴
>    - **热度信号**：最高 hot_score/reply_count 的帖子在讲什么，重要的可摘原文段落
>    - 注意：热帖里的数字（股价/财报）是散户说法、非事实，回传时标注"散户口径待核"，不要当数据用

若当前环境实在起不了子 agent，退而在主 agent 直接跑脚本（`--out "<视频文件夹>/参考资料/抓取数据/xueqiu_hot_posts.json"`），读完 JSON 立刻提炼成上面那份摘要、同样写一份 `参考资料/雪球热帖-摘要.md`、别把原始全文留在上下文里。

### 参数与依赖

- **股票代码格式**：A股 `SH600585` / `SZ000858`，港股 `HK03690`（脚本自动处理港股接口的代码转换），美股 `BABA`。不确定代码就先跑 `web_search.py` 搜 "<股票名> 雪球 代码"。
- **参数**：`--top` 抓多少条热帖（默认 5），`--comments` 每条帖加载多少条高赞评论（默认 5），`--days` 只取最近多少天内的帖子（默认 30；传 0 不限时间），`--no-comments` 只要正文不要评论，`--sort new` 换成按时间的新帖（默认 `hot` 热帖）。
- 脚本用 Playwright 驱动本地 Chromium 绕过雪球阿里云 WAF，**首次运行较慢（要过风控挑战），属正常**。全程走 stderr 打印进度，结果 JSON 写到 `--out`。
- 依赖：`playwright`、`beautifulsoup4`、`lxml`，以及一个 Chromium 内核。首次运行报 `ModuleNotFoundError` 先 `pip install playwright beautifulsoup4 lxml`；报找不到浏览器，脚本会自动查找 `~/Library/Caches/ms-playwright` 下已缓存的 Chromium，也可 `playwright install chromium` 下载，或设 `PW_CHROMIUM=/path/to/chrome` 指定。
- 若报「未拿到 xq_a_token」或长时间卡住，隔几十秒重试；不要让它阻塞整个流程，抓不到就在选题里注明"雪球热帖未获取到"，继续用 `web_search.py` 的数据。

**输出结构**（子 agent 读这份 JSON、消化成摘要；主 agent 不直接读它）：

```json
{
  "symbol": "HK01952", "sort": "热帖", "window_days": 30, "count": 5,
  "posts": [
    {
      "author": "作者昵称", "created_at": "2026-06-21 18:28",
      "title": "帖子标题(可能为空)", "text": "正文全文(已清洗HTML)",
      "reply_count": 393, "like_count": 182, "view_count": 516387,
      "hot_score": 575, "url": "帖子链接",
      "comment_total": 393,
      "top_comments": [
        {"author": "...", "text": "高赞评论正文", "like_count": 47,
         "reply_count": 2, "created_at": "...", "ip_location": "广东"}
      ]
    }
  ]
}
```

**怎么用这份数据：**
- 看 `hot_score` 高、`reply_count` 大的帖子在争什么 → 这就是现成的**争议判断型/答疑解惑型选题**。
- 看 `top_comments` 里的高赞观点和分歧点 → 提炼成口播稿里的"散户怎么看""评论区吵翻了"这类接地气的段落，增强代入感。
- 注意区分：热帖里的观点是**散户情绪与观点**，是素材不是事实。涉及数字（股价、财报）仍以 `xueqiu_quote.py`/`web_search.py` 核对过的为准。

---

## 5. xueqiu_hot_stocks.py — 全市场热榜（仅阶段零选题发现用）

抓雪球全市场热榜（人气热股/涨幅/跌幅/成交额四榜，每榜 30 只），供阶段零反推"今天全市场哪些票在热/在被套"。用法与在选题发现子 agent 里的调度见 [topic-discovery.md](topic-discovery.md)。

```bash
python3 scripts/xueqiu_hot_stocks.py --top 30 --out /tmp/hot.json          # A股
python3 scripts/xueqiu_hot_stocks.py --top 30 --market hk --out /tmp/hot.json  # 港股/美股加 --market hk|us
```

- 跌幅榜是"套牢盘厚、持仓焦虑浓"的富矿，人气榜是"正在被讨论"的信号。
- 单个榜失败会优雅降级（失败榜带 `error` 字段照常返回其它榜）；四榜全失败或拿不到 token 时，退回 `web_search.py` 搜 `"今日涨停板 龙虎榜 热门板块 最新"` 兜底，别卡住。
