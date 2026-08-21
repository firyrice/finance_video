# 发布后数据抓取手册（四平台账号级 + 稿件级）

本文件是**视频发布之后**追踪数据的完整说明。这是一条独立于创作的工作流——和"把股票变成视频"是两件事。SKILL 正文只保留触发语→脚本速查表，接口字段、cookie、范围规则都查这里。

**四平台并行**：本账号同时在 抖音 / 小红书 / B站 / 视频号 发布，各平台数据单独脚本、单独落盘。**稿件级数据一律落进该视频文件夹下的 `数据/` 子目录、一平台一文件、命名「平台_数据.md」**（旧的扁平命名 `数据.md`/`小红书数据.md`/`数据_B站.md` 已废弃）：

| 平台 | 账号级落盘 | 稿件级落盘 | cookie 文件 | 是否需浏览器 |
|---|---|---|---|---|
| 抖音 | `账号数据/抖音.md` | 各视频 `数据/抖音_数据.md` | `.douyin_cookie` | Playwright |
| 小红书 | `账号数据/小红书.md` | 各视频 `数据/小红书_数据.md` | `.xiaohongshu_cookie` | Playwright |
| B站 | `账号数据/账号数据_B站.md` | 各视频 `数据/B站_数据.md` | `.bilibili_cookie` | 纯 requests |
| 视频号 | `账号数据/视频号.md` | 各视频 `数据/视频号_数据.md`（`--video` 稿件级） | `.channels_cookie` | Playwright |

所有 cookie 文件在技能根目录、已 gitignore。**过期报错时，让用户从浏览器复制对应平台的 `document.cookie` 覆盖该文件即可，脚本无需改动。**

---

## 「更新数据」触发范围规则（四平台通用）

用户说"更新数据""刷新数据"时，**更新范围由用户当次描述决定**，不要自作主张扩大或缩小：

- **点名某支/某几支**（如"更新一下牧原""把茅台和迈瑞刷一下"）→ 只对被点名的视频跑稿件级脚本，`--url` 从各自 `视频基础信息.md` 的 `创作后台链接`/`noteId`/`BV` 字段读。
- **说"更新所有""全部刷一遍"** → 遍历 `workspace/*/视频基础信息.md`，对每支后台链接不是"待填"的依次跑（一支 cookie 失效/抓空不中断其余，最后汇总哪几支成功、哪几支失败）。
- **只说"更新数据"没指范围** → 默认理解为更新所有已发布的；范围有歧义时先问一句确认，别默认全量猛跑。
- **未指平台时先确认平台**（抖音 / 小红书 / B站 / 视频号，或多个）——别把三平台或稿件级/账号级混淆。
- 若某支 `创作后台链接` 还是"待填" → 提示用户补链接，别跳过时不吭声。
- **账号级数据是另一回事**（触发语"更新账号数据""更新B站账号数据"等），走各自的 account 脚本，别和稿件级"更新数据"混淆。

---

## 抖音

### 发布后必做：存后台链接

视频发到抖音后，用户给出创作者后台的作品详情页链接（形如 `https://creator.douyin.com/creator-micro/work-management/work-detail/<item_id>`）时，**第一件事就是把它回填进该视频 `视频基础信息.md` 元信息里 `创作后台链接（各平台）` 块的 `抖音:` 行**（同时能确认的话回填发布日期）。这条链接是后续「更新数据」的入口，必须落档。

### 稿件级（首选：自动抓取）

```bash
python3 scripts/douyin_metrics.py --url "<作品详情页链接>" --video "<创建日期>_<最终标题>" --save-raw
```

脚本用 Playwright 注入会话 cookie 打开页面，自动点开「流量分析」「评论管理」两个 tab，截获后台签名接口 JSON，解析后写入该文件夹的 `数据/抖音_数据.md`，原始 JSON 归档进 `raw/`。产出六个小节：①指标总览（播放/点赞/评论/分享/收藏/净涨粉/完播率/封面点击率/2s跳出率等全字段，来自 `item/mget`）②与本账号近期作品对标（`item_compare`）③逐小时趋势（播放量+涨粉，`metrics_trend`）④流量来源占比及对比7日（`item/play/source`）⑤进度分析逐段快进率/回看率、自动标出最大流失段（`progress/analysis`）⑥高赞评论 Top 20（`comment/list/select` 全量抓取后按点赞降序）。

- `--video` 传带日期前缀的完整文件夹名，须与 workspace 下文件夹名完全一致。
- 脚本报"未抓到 item/mget 数据"→ cookie 过期，让用户重导。
- 调试可加 `--dry-run`（只打印不落盘）或 `--show`（显示浏览器窗口）。

### 稿件级（备选：手动 xlsx 导入）

若拿不到链接或需要后台独有的进度分析字段，从创作者后台手动导出 xlsx，跑：

```bash
python3 scripts/ingest_metrics.py --video "<创建日期>_<最终标题>" 导出1.xlsx 导出2.xlsx
```

自动生成/更新该文件夹的 `数据/抖音_数据.md` 并把原件归档进 `raw/`。之后回填 `视频基础信息.md` 里的发布日期与视频链接。

### 账号级

触发语"更新账号数据""刷新账号数据"，跑：

```bash
python3 scripts/douyin_account.py --save-raw
```

脚本注入 cookie 打开创作者数据中心页，在页面 JS 环境里 fetch 两个 `janus/creator/data/overview/dashboard` 接口（`recent_days=30`，默认 30 天，`--days` 可改），把账号级每日数据（投稿量/播放/点赞/评论/分享/净增粉/新增粉/取关粉/回访粉/主页访问/封面点击率/5s完播率/2s跳出率/平均播放时长/总粉丝量）写进 `账号数据/抖音.md`，原始 JSON 归档 `账号数据/raw/`。产出：核心指标总览（近 N 天聚合）+ 三个逐日趋势表（每日互动/每日粉丝/每日质量）。

---

## 小红书

小红书创作者后台接口是登录态签名接口（`x-s`/`x-t` 签名，纯 requests 算不了），故用 Playwright 注入会话 cookie、在页面 `response` 事件里截 JSON。

### 账号级

触发语"更新小红书账号数据""刷新小红书账号数据"，跑：

```bash
python3 scripts/xiaohongshu_account.py --save-raw
```

抓 `datacenter/account/base`（近7天+近30天：观看/曝光/主页访问/点赞/收藏/评论/分享/新增粉/流失粉/净增粉/发布数/封面点击率/完播率/主页转粉率/人均时长，各带环比）+ `audience/source/account`（流量来源占比）+ `galaxy/user/info`（账号昵称/小红书号），写进 `账号数据/小红书.md`。产出：近7天/近30天两段总览+流量来源 + 近7天逐日趋势（每日互动/每日粉丝/每日质量）。

### 稿件级

用户给一条笔记数据页链接（含 noteId，形如 `https://creator.xiaohongshu.com/statistics/note-detail?noteId=...`），跑：

```bash
python3 scripts/xiaohongshu_metrics.py --url "<链接>" --video "<日期>_<标题>" --save-raw
```

抓 `datacenter/note/base`（观看/曝光/点赞/收藏/评论/分享/涨粉/60秒播放/封面点击率/5秒完播率/完播率/2秒退出率/粉丝观看占比/人均时长 + 逐小时趋势）+ `note/audience/source`（该笔记流量来源细分）。产出：指标总览+流量来源+逐小时互动/逐小时质量。写进该视频文件夹的 `数据/小红书_数据.md`。noteId 链接同样建议回填进 `视频基础信息.md` 的 `小红书:` 行。

---

## B站

B站后台接口是普通 cookie 鉴权 JSON、无签名，脚本纯 `requests` 即可，不用 Playwright。cookie 至少含 `SESSDATA`/`bili_jct`/`DedeUserID`；过期报错（`code!=0` 或"接口未返回 JSON"）就重导。

### 账号级

触发语"更新B站账号数据""刷新B站账号数据"，跑：

```bash
python3 scripts/bilibili_account.py --save-raw
```

抓 `index/stat`（九项累计+昨日新增：粉丝/播放/点赞/投币/收藏/分享/评论/弹幕/充电）+ `data/pandect`（近 30 天逐日趋势），写进 `账号数据/账号数据_B站.md`。

### 稿件级

用户给一条 B站稿件数据页链接（含 BV 号，形如 `https://member.bilibili.com/platform/upload-manager/article/data/BV...`），跑：

```bash
python3 scripts/bilibili_metrics.py --url "<链接>" --video "<日期>_<标题>" --save-raw
```

抓 `web-interface/view`+`data/archive`+`data/base`。产出：指标总览、播放行为（观看人数/时长/平均播放进度）、粉丝vs游客构成、观看地域Top10、账号观众画像（B站画像仅账号级，脚本已注明非稿件维度）。写进该视频文件夹的 `数据/B站_数据.md`。BV 链接同样建议回填进 `视频基础信息.md` 的 `B站:` 行。

---

## 视频号（微信）

视频号后台 `post/post_list` 接口**一次就返回全部视频的完整指标**，无需逐条点开、无需分链接——所以账号级抓一次就把每支视频的稿件级数据也拿到了。视频号助手（`channels.weixin.qq.com`）是 SPA、接口带登录态签名，故用 Playwright 注入会话 cookie、在 `response` 事件里截 JSON。cookie 双域注入（`.weixin.qq.com`/`.qq.com`），至少含 `sessionid`/`wxuin`；过期报"未抓到 post_list 视频数据"就重导。

### 账号级（默认）

触发语"更新视频号数据""刷新视频号数据"，跑：

```bash
python3 scripts/channels_metrics.py --save-raw
```

脚本先开账号数据页抓 `get-finder-total-statics`（总粉丝数）+ `new_post_total_data`（近7天分来源逐日互动），再开作品列表页抓 `post/post_list`（全部视频：播放/点赞/评论/转发/收藏/涨粉/完播率/平均时长/快划率/昨日播放），写进 `账号数据/视频号.md`，原始 JSON 归档 `账号数据/raw/`。产出：账号总览（总粉丝+视频数）、近7天互动合计、播放来源占比、近7天逐日播放、视频明细（按播放降序）。

### 稿件级（点名某支视频）

用户点名要某支视频的视频号数据时，跑：

```bash
python3 scripts/channels_metrics.py --video "<创建日期>_<最终标题>" --save-raw
```

脚本抓同一份 `post/post_list`，**按股票名/标题匹配出这一支**，把它的稿件级指标写进该视频文件夹的 `数据/视频号_数据.md`。注意：视频号后台在稿件级**不提供逐小时趋势、也不提供流量来源细分**（这两项只在账号级 `new_post_total_data` 里有），故 `视频号_数据.md` 只落该视频的核心指标（播放/点赞/评论/转发/收藏/涨粉/完播率/平均时长/快划率/昨日播放），没有逐小时/来源分解，这是接口限制、非脚本缺陷。匹配不到就提示用户核对标题/股票名。

---

## 分析复盘

需要分析"某视频为啥流量高但吸粉差""某视频为啥被限流"这类问题时，读账号级 `账号数据/抖音.md`（或 `小红书.md`/`账号数据_B站.md`/`视频号.md`）和相关视频 `数据/` 文件夹下对应平台的 `平台_数据.md`（如 `数据/抖音_数据.md`），把报告写进 `workspace/reports/`（命名 `YYYY-MM-DD_主题.md`），并把稳定规律回写到 `huasheng.md`，驱动后续创作迭代。
