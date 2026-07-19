# bilibili-finance-video

把一支股票变成一条有观点、能涨播放量的 B 站/抖音财经视频。这是一个 **Agent Skill**（遵循 `SKILL.md` 规范），同时支持 **Claude Code** 和 **Codex**，也兼容其它读取 SKILL.md 的 agent。

输入一个股票名或代码（如"分析一下贵州茅台"、`600519`、"英伟达 NVDA"），技能会：

1. 联网抓取实时行情、财报、新闻，并抓一手雪球热帖（散户情绪）；
2. 先产出 **3 个带钩子的选题方案**，停下来等你选；
3. 采纳后一次性产出：**完整口播稿**（7-10 分钟）、**5 个爆款标题**、**B站(16:9) + 抖音(9:16) 两版封面**；
4. 最后从**专业财经观众视角**做一轮质量评估，给出优化建议；
5. 所有产出汇总到**同一个 Markdown 文档**，方便复制存档。

## 安装

### 一键安装（推荐）

```bash
git clone https://github.com/firyrice/finance_video.git
cd finance_video
./install.sh            # 软链接到 Claude Code + Codex 两个工具
pip install -r requirements.txt
```

`install.sh` 默认用软链接方式，之后 `git pull` 更新会自动对两个工具生效。其它模式：

```bash
./install.sh --copy     # 改为复制（不依赖仓库常驻）
./install.sh --claude   # 只装 Claude Code
./install.sh --codex    # 只装 Codex
```

### 手动安装

技能只需被放到对应工具的 skills 目录下（每个工具一个 `<skills>/bilibili-finance-video/SKILL.md`）：

| 工具 | 技能目录 |
|------|----------|
| Claude Code | `~/.claude/skills/bilibili-finance-video` |
| Codex | `~/.codex/skills/bilibili-finance-video`（部分版本为 `~/.agents/skills/`） |

把本仓库软链接或复制过去即可，例如：

```bash
ln -s "$(pwd)" ~/.claude/skills/bilibili-finance-video
ln -s "$(pwd)" ~/.codex/skills/bilibili-finance-video
```

安装后**重启** Claude Code / Codex，输入股票名即可触发。

## 依赖与环境变量

- Python 3.9+，依赖见 `requirements.txt`（`openai`、`playwright`、`beautifulsoup4`、`lxml`）。
- 雪球抓取脚本需要 Chromium 内核：`playwright install chromium`（或用 `PW_CHROMIUM=/path/to/chrome` 指定已有浏览器）。
- 封面生成脚本需要 B 站 LLM 网关的 key：`export LLM_GATEWAY_API_KEY=你的key`。

## 目录结构

```
.
├── SKILL.md                     # 技能主体（工作流、分析框架、合规红线）
├── install.sh                   # 跨工具安装脚本
├── requirements.txt
├── references/                  # 口播稿结构 / 标题公式 / 封面提示词模板
│   ├── script-structure.md
│   ├── title-formulas.md
│   └── cover-prompts.md
├── scripts/
│   ├── generate_cover.py        # gpt-image-2 生成封面（B站/抖音两版）
│   └── xueqiu_hot_posts.py      # 抓雪球热帖 + 高赞评论
└── evals/evals.json             # 技能评测用例
```

## 跨工具兼容说明

`SKILL.md` 里出现的 `WebSearch` / `WebFetch` / `Write` 等是 Claude Code 的工具名。在 Codex 下会自动映射到等价能力（联网搜索、网页读取、文件写入）。脚本均为纯 Python，通过 shell 调用，两个环境通用；调用时用技能目录的**绝对路径**，不要假设当前工作目录就是技能目录（详见 SKILL.md「跨工具适配」一节）。

## 免责声明

本技能产出的是内容创作素材，包含的任何"买入/卖出/观望"表述均为示例性观点，**不构成投资建议**。据此投资，风险自负。
