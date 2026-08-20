# 分镜规划书 · 兆易创新（花生 AI 成片输入）
> 口播稿唯一真源：本目录 视频基础信息.md 第一节；分镜断句逐字复用，勿改字改标点。
> 制作方案：B 素材混合 MG 动画

## 一、成片需求（含 MG 画风设计）

### 📋 基础信息
- 视频标题：净利暴增1091%，股价却逼近腰斩，兆易创新也能算成长股？
- 内容摘要：兆易创新上半年净利暴增1091%，股价却逼近腰斩。视频用「涨价 vs 放量」这把尺子拆穿暴增真相：核心是存储芯片行业性涨价撑起的周期红利，而非技术突破的成长；PE从185倍一路跌到22倍、净利率反超毛利率的异常，暴露利润里掺了投资收益的水分；叠加董事长高位减持44亿的信号，给出「别用成长逻辑追周期股」的判断框架，并列出三个可验证的观察信号。
- 年代背景：2026年 · 现代
- 制作方案：B 素材混合 MG 动画
- 参考风格：严肃财经调查 / 深度解说类 UP 主风格
- BGM 需求：整体沉稳压抑、带警示感的电子底鼓，中段数据段可加紧张弦乐推进，收尾信号清单回归克制冷静

### 🎥 素材要求
- 素材类型：半年报/财报截图、股票异常波动公告截图、存储芯片晶圆/产线实拍、雪球/研报截图、行业价格走势资料
- 素材偏好：数据类画面留白给 MG 叠加；避免素人正脸；镜头偏硬朗、审视感；晶圆/电路特写反复出现作贯穿视觉锚点；K线走势图/具体股价不检索（对不上，走势与数字全由 MG 画）
- 时效性：使用 2025 年后素材
- 地域限定：中国
- 专名要求：兆易创新（公司）、NOR Flash / SLC NAND / DRAM / MCU（产品线）、TrendForce集邦咨询（机构）、雪球（平台）、华鑫证券（机构）、长鑫（关联方）、朱一明（人名）、三星 / 美光 / 铠侠（公司）、华友钴业（预告下期，仅提及不展开）
- 用户硬性要求：无

### 🎨 MG 动画风格
- 固定基因：严肃财经调查 / 硬朗商务；炭灰墨黑底 + 暖金点缀；标题极粗黑体 / 数字数字展示体 / 正文硬朗黑体；图标庄重（Serious）
- 情绪温度：看跌/警示——压暗基调，暖金点缀降权，加警示黄强调下跌与风险段落
- 视觉母题（本期共振）：沿用封面核心意象——存储芯片晶圆的网格/电路纹理，与下跌K线的「压制」关系。晶圆网格作 MG 边框底纹与分割线，K线作转场与压暗时刻的元素，价格标签的上/下箭头贯穿全片数据段

```json
{ "visual_style": "严肃财经调查/硬朗商务",
  "color_system": {"color_style": "深色浓郁系", "main_hsb_hue": 42},
  "typography": {"title_font": {"font_family": "得意黑一类极粗黑体", "font_weight": "black"},
                  "body_font": {"font_family": "硬朗黑体", "font_weight": "regular"},
                  "number_font": {"font_family": "数字展示体", "font_weight": "semibold"}},
  "icon_library": {"style": "Serious"} }
```

## 二、分镜脚本（JSON 内嵌）

```json
{
  "schema_version": "1.0",
  "scenes": [
    {
      "scene_id": "A01",
      "scene_title": "矛盾开场·芯片压K线",
      "scene_design": "专名清单：兆易创新（公司）／ 国家：中国 ／ 年代：现代 ／ 素材来源：存储芯片晶圆特写 ／ 素材偏好：晶圆纹理与下跌K线叠加，呼应封面「芯片被K线压住」核心意象，压暗警示黄",
      "shots": [
        {
          "shot_id": "S01",
          "visual_type": "mg_frame",
          "source": "cloud_only",
          "script": "兆易创新，上半年净利润暴增1091%，股价却从846块一路跌到436块，几乎腰斩。利润翻了十一倍，股票反而跌掉近一半。这么赚钱的公司，凭什么还算不上成长股？",
          "visual_description": "全屏晶圆纹理底，左侧「1091%↑」暖金大字砸入，右侧「846→436」警示黄配下跌箭头砸入，两侧数字在画面中央剧烈碰撞，晶圆被K线压出裂纹，收在问句时定格黑底大字反问"
        }
      ]
    },
    {
      "scene_id": "A02",
      "scene_title": "品牌锚",
      "scene_design": "专名清单：无 ／ 国家：中国 ／ 年代：现代 ／ 素材来源：主播口播实拍/品牌片头 ／ 素材偏好：简洁不抢戏",
      "shots": [
        {
          "shot_id": "S02",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "关注蛋炒饭财经，带你深度巡礼1000只股票，今天我们聊兆易创新。",
          "visual_description": "主播口播镜头或品牌片头，节奏平稳，不加MG"
        }
      ]
    },
    {
      "scene_id": "A03",
      "scene_title": "尺子框架·成长vs周期",
      "scene_design": "专名清单：兆易创新（公司）／ 国家：中国 ／ 年代：现代 ／ 素材来源：抽象图解素材、晶圆实拍 ／ 素材偏好：二元对比图解，简洁不喧宾夺主",
      "shots": [
        {
          "shot_id": "S03",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "先给你一把尺子，后面所有数据都围着它转。",
          "visual_description": "暗底浮现一把发光尺子的MG图标，随后数字符号围绕尺子悬浮排列"
        },
        {
          "shot_id": "S04",
          "visual_type": "mg_frame",
          "source": "cloud_only",
          "script": "一家公司利润暴涨，赚钱的方式其实分两种：一种是把产品卖得更多、卖得更贵，技术真变强了，这种增长市场愿意给高估值；另一种，是撞上了一轮涨价，东西没多卖几颗，只是赶上价格暴涨，利润被风刮起来了。",
          "visual_description": "左右分屏框架，左侧「卖多卖贵·技术变强」配上升曲线与齿轮图标，右侧「涨价·被风刮起」配价格标签与风吹动效，两侧同步生长对比"
        },
        {
          "shot_id": "S05",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "前一种叫成长，后一种，就是周期。",
          "visual_description": "左侧标签定格「成长」，右侧标签定格「周期」，两枚印章式落定"
        },
        {
          "shot_id": "S06",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "你带着这把尺子去看兆易创新，答案自己就浮出来了。",
          "visual_description": "尺子图标缓慢移向晶圆实拍画面，过渡到下一段"
        }
      ]
    },
    {
      "scene_id": "A04",
      "scene_title": "半年报数据炸裂",
      "scene_design": "专名清单：兆易创新（公司）／ 国家：中国 ／ 年代：现代 ／ 素材来源：2026年半年报截图、财报发布会资料 ／ 素材偏好：数据留白给MG叠加",
      "shots": [
        {
          "shot_id": "S07",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "先看这轮业绩有多猛。",
          "visual_description": "半年报文件封面实拍，镜头缓慢推进"
        },
        {
          "shot_id": "S08",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "8月18号晚上，兆易创新发2026年半年报，营业收入115.66亿，同比增长178%；最唬人的是归母净利润，68.57亿，同比暴涨1091.5%，翻了十一倍。",
          "visual_description": "半年报截图暗化作底，「115.66亿」「同比+178%」先滚动砸入，随后「68.57亿」「+1091.5%」以更大字号、暖金高亮砸入，晶圆网格底纹微闪"
        },
        {
          "shot_id": "S09",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "什么概念？它去年一整年才赚16个亿，今年半年赚的钱，是去年全年的四倍还多，放全A股都是最炸的那一档。",
          "visual_description": "柱状对比图，「去年全年16亿」矮柱 vs「今年半年68.57亿」高柱拔起，中间「四倍+」箭头强调"
        },
        {
          "shot_id": "S10",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "看到这儿，你多半会问，这不就是妥妥的大牛股吗？凭啥股价反而往下走？",
          "visual_description": "主播口播镜头，语气带疑问，画面压暗制造悬念，切入下一段"
        }
      ]
    },
    {
      "scene_id": "A05",
      "scene_title": "转场·钱从哪来",
      "scene_design": "专名清单：无 ／ 国家：中国 ／ 年代：现代 ／ 素材来源：主播口播实拍 ／ 素材偏好：短句留白，节奏停顿",
      "shots": [
        {
          "shot_id": "S11",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "问题就出在，这68个亿，是怎么来的。",
          "visual_description": "主播口播镜头，语气停顿，画面短暂留白"
        }
      ]
    },
    {
      "scene_id": "A06",
      "scene_title": "主业介绍·四条产品线",
      "scene_design": "专名清单：兆易创新（公司）、NOR Flash（产品）、SLC NAND（产品）、DRAM（产品）、MCU（产品）／ 国家：中国 ／ 年代：现代 ／ 素材来源：芯片产线实拍、产品发布资料 ／ 素材偏好：产品实拍配头衔卡片",
      "shots": [
        {
          "shot_id": "S12",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "兆易创新干的是存储芯片。",
          "visual_description": "存储芯片晶圆特写实拍"
        },
        {
          "shot_id": "S13",
          "visual_type": "mg_frame",
          "source": "cloud_only",
          "script": "旗下四条产品线，NOR Flash全球第二、国内第一，SLC NAND国内第一，利基型DRAM今年一季度已经占到总收入的三分之一，MCU国内第一。",
          "visual_description": "四宫格框架依次弹出四张产品卡片：NOR Flash（全球第二·国内第一）、SLC NAND（国内第一）、利基型DRAM（占营收1/3）、MCU（国内第一），卡片边框沿用晶圆网格纹理"
        },
        {
          "shot_id": "S14",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "这些头衔都很硬，全球前十的芯片设计公司，中国半导体的隐形冠军，都没错。",
          "visual_description": "实拍产线画面暗化作底，「全球前十芯片设计公司」「隐形冠军」两枚庄重徽章依次浮现"
        },
        {
          "shot_id": "S15",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "但它这轮利润暴涨，真正的引擎很简单：它卖的东西，涨价了，而且涨疯了。",
          "visual_description": "价格标签图标从平稳突然急速上蹿并抖动，暖金转警示黄"
        }
      ]
    },
    {
      "scene_id": "A07",
      "scene_title": "涨价成因·巨头退出供给",
      "scene_design": "专名清单：TrendForce集邦咨询（机构）、三星（公司）、美光（公司）、铠侠（公司）、兆易创新（公司）／ 国家：中国 ／ 年代：现代 ／ 素材来源：行业价格走势资料、存储大厂产线资料画面 ／ 素材偏好：多公司产能迁移用拓扑图呈现",
      "shots": [
        {
          "shot_id": "S16",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "根据TrendForce集邦咨询的数据，2026年上半年，NOR Flash和SLC NAND这两类芯片的合约价，累计涨幅全都突破了100%。",
          "visual_description": "机构名角标出现，合约价折线图暗化作底，涨幅折线冲破「100%」红线标记"
        },
        {
          "shot_id": "S17",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "兆易创新的毛利率，也从2024年的38%，一路飙到今年一季度的57%多。",
          "visual_description": "毛利率柱状图从38%攀升至57%，柱体暖金渐染"
        },
        {
          "shot_id": "S18",
          "visual_type": "mg_frame",
          "source": "cloud_only",
          "script": "注意，这个涨价的根子，不在下游需求突然爆发，而在供给端——三星、美光、铠侠这些全球存储巨头，这两年全把产能往HBM、往高层3D NAND这些AI赚钱的先进存储上搬，主动退出了NOR Flash、SLC NAND这些成熟制程、低毛利的小众市场。",
          "visual_description": "拓扑框架图，三星/美光/铠侠三个节点，箭头把产能从「NOR Flash/SLC NAND低毛利区」拉向「HBM/3D NAND高毛利区」，低毛利区随箭头拉走逐渐留出空洞，晶圆网格底纹贯穿"
        },
        {
          "shot_id": "S19",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "巨头看不上这点小钱，撤了，留下一个供给的坑，兆易创新这些国内厂商填上了坑，顺手把价格抬了起来。",
          "visual_description": "延续上一镜留出的空洞，兆易创新标识填入空洞位置，价格标签同步上扬"
        }
      ]
    },
    {
      "scene_id": "A08",
      "scene_title": "PE三档下滑·周期定价",
      "scene_design": "专名清单：兆易创新（公司）、雪球（平台）／ 国家：中国 ／ 年代：现代 ／ 素材来源：雪球实时数据截图 ／ 素材偏好：多档数字下滑用漏斗/时间轴呈现",
      "shots": [
        {
          "shot_id": "S20",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "所以这轮利润，核心是「涨价」撑起来的，是巨头退出让出来的红利，跟兆易创新自己把产品做出多大突破，关系其实不大。",
          "visual_description": "实拍暗化底，「涨价」「红利」两枚标签卡片并列浮现作小结"
        },
        {
          "shot_id": "S21",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "这也就解释了一个让很多人想不通的现象。",
          "visual_description": "主播口播镜头过渡"
        },
        {
          "shot_id": "S22",
          "visual_type": "mg_frame",
          "source": "cloud_only",
          "script": "兆易创新现在的市盈率，我拉的是雪球8月18号的实时数据：静态市盈率185倍，滚动市盈率38.65倍，动态市盈率22倍。这三个数从185到38到22，一路往下掉。",
          "visual_description": "雪球截图角标，漏斗型框架从上到下依次落下三个数字：185倍→38.65倍→22倍，数字越往下字号不变但底色越压暗，晶圆网格底纹分割三档"
        },
        {
          "shot_id": "S23",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "这说明什么？它的利润正在飞快释放，一年比一年猛，但市场给它每一块钱利润的定价，却一年比一年低。",
          "visual_description": "两条箭头反向发散，「利润」箭头向上冲，「估值定价」箭头向下压"
        },
        {
          "shot_id": "S24",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "利润越高、估值倍数反而越低——这就是典型的周期股走法。",
          "visual_description": "「周期股」印章式标签落定，警示黄描边"
        },
        {
          "shot_id": "S25",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "市场用22倍的动态市盈率在给你算账，潜台词是：它默认你今年全年能赚一百三十多个亿，但它压根不信这个利润能年年都有。",
          "visual_description": "计算器风格MG，「22倍 × 130亿+」算式浮现，随后叠加问号图标表达市场存疑"
        }
      ]
    },
    {
      "scene_id": "A09",
      "scene_title": "周期股逻辑·预期price in",
      "scene_design": "专名清单：无 ／ 国家：中国 ／ 年代：现代 ／ 素材来源：散户交易实拍/评论区资料 ／ 素材偏好：抽象因果配简单图解",
      "shots": [
        {
          "shot_id": "S26",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "周期股最狠的地方就在这。",
          "visual_description": "主播口播镜头，语气加重"
        },
        {
          "shot_id": "S27",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "咱们散户的直觉是，利润暴增，股价该涨，于是追进去。",
          "visual_description": "手机炒股软件下单实拍（无正脸）"
        },
        {
          "shot_id": "S28",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "但真正懂行的资金，看的从来都是另一件事：你这一季的利润，到底是能年年都有的正常利润，还是撞上风口、来去一阵风的暂时利润。",
          "visual_description": "暗化底上并列两张标签卡「正常利润·年年有」与「暂时利润·风给的」，风吹动效掠过后者"
        },
        {
          "shot_id": "S29",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "撞上风口的，风一停，利润从哪儿来就回哪儿去，而股价早在利润见顶之前，就先跌给你看。",
          "visual_description": "风力图标停止转动，利润箭头回落，K线在利润峰值标记之前已开始下行"
        },
        {
          "shot_id": "S30",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "你现在看到的腰斩，就是市场提前把「涨价会退潮」这个预期，打进了股价里。",
          "visual_description": "潮水退去动效叠加K线图，「涨价会退潮」标签沉入画面底部"
        }
      ]
    },
    {
      "scene_id": "A10",
      "scene_title": "净利率倒挂·投资收益水分",
      "scene_design": "专名清单：兆易创新（公司）／ 国家：中国 ／ 年代：现代 ／ 素材来源：半年报截图、财务数据资料 ／ 素材偏好：拆解式算式与占比图，避免堆砌",
      "shots": [
        {
          "shot_id": "S31",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "说到这，我还得泼一盆更实在的冷水。",
          "visual_description": "冷水泼溅动效叠加暗化实拍，画面色温骤降，警示黄边框浮现"
        },
        {
          "shot_id": "S32",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "这68.57亿的归母净利润里，有二十多亿，主业卖芯片赚不来，是它持有股权升值的收益。",
          "visual_description": "饼图将「68.57亿」拆成两块，「主业」大块与「二十多亿·投资收益」小块分色标注"
        },
        {
          "shot_id": "S33",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "半年报里白纸黑字写着，上半年公允价值变动收益22.28亿。",
          "visual_description": "半年报截图对应条目高亮框选，「公允价值变动收益 22.28亿」数字放大定格"
        },
        {
          "shot_id": "S34",
          "visual_type": "mg_frame",
          "source": "cloud_only",
          "script": "你甚至可以自己算一笔账：68.57亿的净利，除以115.66亿的营收，净利率接近六成，比它57%的毛利率还高。",
          "visual_description": "算式框架依次生长：「68.57亿 ÷ 115.66亿 = 净利率≈59%」，随后与「毛利率57%」并列成两根柱子，净利率柱反常地高于毛利率柱，警示黄标出倒挂缺口"
        },
        {
          "shot_id": "S35",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "正常公司，净利率都该比毛利率低一大截，因为它还得扣研发、销售这些费用。",
          "visual_description": "常规公司示意图，毛利率柱高、净利率柱低，中间箭头标注「减研发/销售费用」"
        },
        {
          "shot_id": "S36",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "兆易创新能倒挂，恰恰就是这二十多亿的投资收益，把净利润给顶穿了。",
          "visual_description": "延续S34倒挂柱图，投资收益箭头从底部顶穿净利率柱顶端"
        },
        {
          "shot_id": "S37",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "也就是说，那个响彻全网的「暴增1091%」，是掺了点水的，主业真正的成色，是扣非之后的796.9%。",
          "visual_description": "「1091%」大字表面浮现水滴质感覆层，缓慢溶解显出「796.9%」"
        },
        {
          "shot_id": "S38",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "当然，796.9%依然是爆炸级的好业绩，这个我不否认。",
          "visual_description": "主播口播镜头，语气平衡客观"
        },
        {
          "shot_id": "S39",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "但我之所以把这点挑出来，是想提醒你，看一家公司，别被最大的那个数字牵着走，得问一句，这钱是老老实实靠主业赚的，还是有一块是运气给的。",
          "visual_description": "主播口播镜头，正面陈述观点，画面克制无花哨MG"
        }
      ]
    },
    {
      "scene_id": "A11",
      "scene_title": "公司自曝风险公告",
      "scene_design": "专名清单：兆易创新（公司）／ 国家：中国 ／ 年代：现代 ／ 素材来源：股票异常波动公告截图 ／ 素材偏好：公告文本高亮划重点，不喧宾夺主",
      "shots": [
        {
          "shot_id": "S40",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "其实兆易创新自己，比谁都清楚这轮行情的风险。",
          "visual_description": "主播口播镜头过渡"
        },
        {
          "shot_id": "S41",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "今年6月30号，它发过一份股票异常波动的公告，原话说得特别直白：公司所处的存储芯片行业呈周期性波动，目前产品价格已处历史高位，持续上涨不可持续，供需终将再平衡，未来价格可能出现相当幅度的回落，将对公司售价、毛利率和盈利能力产生较大负面影响。",
          "visual_description": "公告截图暗化作底，逐句加下划线高亮同步文字滚动，警示黄描边"
        },
        {
          "shot_id": "S42",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "这是上市公司自己亲口说的，不是我在吓唬你。",
          "visual_description": "主播口播镜头，语气加重强调"
        }
      ]
    },
    {
      "scene_id": "A12",
      "scene_title": "时间线讽刺·高点买入+朱一明减持",
      "scene_design": "专名清单：兆易创新（公司）、华鑫证券（机构）、朱一明（人名）／ 国家：中国 ／ 年代：现代 ／ 素材来源：研报截图、公司公告资料 ／ 素材偏好：多事件用时间轴框架呈现，避免素人正脸",
      "shots": [
        {
          "shot_id": "S43",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "更讽刺的是时间线。",
          "visual_description": "主播口播镜头过渡，语气带讽刺"
        },
        {
          "shot_id": "S44",
          "visual_type": "mg_frame",
          "source": "cloud_only",
          "script": "6月25号，兆易创新股价冲到846.66的历史最高点，市值五千多亿；6月29号，华鑫证券发研报，维持「买入」评级，预测它相对大盘还能再涨20%以上；结果从那天起，股价一路往下，到8月初最低砸到340块，最大回撤逼近60%。",
          "visual_description": "横向时间轴框架，三个节点依次弹出：「6/25 股价846.66·市值5000亿+」「6/29 华鑫证券·买入评级」「8月初 340块·回撤近60%」，K线走势贯穿时间轴下行，晶圆网格作底纹"
        },
        {
          "shot_id": "S45",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "最高点那天的「买入」，成了最贵的一句荐股。",
          "visual_description": "延续时间轴，「买入」评级卡片上盖「最贵的荐股」讽刺印章"
        },
        {
          "shot_id": "S46",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "董事长朱一明呢，5到6月份减持套现了44个亿，7月底股价跌下来之后，又抛出一套组合拳，提议公司回购10到20亿注销、承诺12个月不减持、还计划自己再增持10个亿。",
          "visual_description": "四张动作卡片依次快切：「减持套现44亿」「回购10-20亿注销」「承诺12个月不减持」「增持10亿」，卡片切换节奏配合口播"
        },
        {
          "shot_id": "S47",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "这一减一增，散户在评论区吵翻了天，有人骂这是「高位套现、低位画饼」，也有人帮腔说「人家本来就可以不回购的」。",
          "visual_description": "评论区界面资料画面，两条对立评论气泡交替浮现"
        }
      ]
    },
    {
      "scene_id": "A13",
      "scene_title": "态度声明·硬信号",
      "scene_design": "专名清单：朱一明（人名）／ 国家：中国 ／ 年代：现代 ／ 素材来源：主播口播实拍 ／ 素材偏好：克制陈述，突出核心数字",
      "shots": [
        {
          "shot_id": "S48",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "我不站队去评判朱一明这个人到底是不是鸡贼，那是情绪。",
          "visual_description": "主播口播镜头，语气克制"
        },
        {
          "shot_id": "S49",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "我只想让你盯着一个更硬的信号：连最了解这家公司的人，在股价最高点附近，选择的是把44个亿落袋为安。",
          "visual_description": "实拍暗化底，「44亿」与「落袋为安」两处文字依次高亮聚焦"
        },
        {
          "shot_id": "S50",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "这本身，就是给所有想在这个位置追进去的人，一个无声的提醒。",
          "visual_description": "主播口播镜头，收束语气"
        }
      ]
    },
    {
      "scene_id": "A14",
      "scene_title": "过渡·框架非点位",
      "scene_design": "专名清单：兆易创新（公司）／ 国家：中国 ／ 年代：现代 ／ 素材来源：主播口播实拍 ／ 素材偏好：无",
      "shots": [
        {
          "shot_id": "S51",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "那兆易创新现在到底能不能碰？我给你我的判断，但这个判断，我给的是框架，不是点位。",
          "visual_description": "主播正面口播镜头，转折进入个人判断段"
        }
      ]
    },
    {
      "scene_id": "A15",
      "scene_title": "个人判断·好公司好价格",
      "scene_design": "专名清单：兆易创新（公司）／ 国家：中国 ／ 年代：现代 ／ 素材来源：晶圆产线实拍 ／ 素材偏好：核心金句大字强调",
      "shots": [
        {
          "shot_id": "S52",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "我个人这么看：兆易创新是一门还不错的生意，它在国产存储里的卡位是真的、技术是真的、这轮周期吃到的红利也是真的，这几点我不黑它。",
          "visual_description": "产线实拍暗化底，三枚打勾标签依次浮现：「卡位·真」「技术·真」「红利·真」"
        },
        {
          "shot_id": "S53",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "但「好公司」和「好价格」是两回事。",
          "visual_description": "核心金句极粗黑体大字砸屏，「好公司」与「好价格」两枚标签中间画一道断裂线"
        },
        {
          "shot_id": "S54",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "它现在最大的问题，恰恰就藏在那句最唬人的话里——利润暴增1091%，是靠涨价这个不可持续的变量堆出来的，而市场给它22倍的动态市盈率，恰恰是在说：我知道你现在赚翻了，但我不信这个价位的利润，能年年有。",
          "visual_description": "「1091%」与「22倍」两个核心数字并列回收再现，中间连一道问号箭头，收在问号定格"
        }
      ]
    },
    {
      "scene_id": "A16",
      "scene_title": "三个观察信号",
      "scene_design": "专名清单：兆易创新（公司）、长鑫（关联方）／ 国家：中国 ／ 年代：现代 ／ 素材来源：半年报截图、行业价格资料 ／ 素材偏好：清单式框架，三项并列不抢戏",
      "shots": [
        {
          "shot_id": "S55",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "所以我不会在这个位置，因为「业绩暴增」这四个字，就冲进去追。",
          "visual_description": "主播口播镜头，态度明确"
        },
        {
          "shot_id": "S56",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "我更愿意盯住下面几个信号，等它们给出答案。",
          "visual_description": "「信号清单」标题卡浮现，为下三镜的框架预留三个空位"
        },
        {
          "shot_id": "S57",
          "visual_type": "mg_frame",
          "source": "cloud_only",
          "script": "第一个，存储芯片的合约价，什么时候开始环比走平、甚至回落，这是利润的拐点信号，价格一停，毛利和利润立刻下修，这个信号出来之前，别谈什么底部；",
          "visual_description": "延续S56清单框架，第一格填入「合约价环比走平/回落」，配价格折线走平示意"
        },
        {
          "shot_id": "S58",
          "visual_type": "mg_frame",
          "source": "cloud_only",
          "script": "第二个，下半年在手订单的兑现情况，半年报披露已签订、还没履行完的合同金额有九十多亿，绝大部分要在2026年确认，这个要是能如期兑现，说明短期业绩还有支撑；",
          "visual_description": "清单框架第二格填入「在手订单九十多亿·2026年确认」，配合同文件图标"
        },
        {
          "shot_id": "S59",
          "visual_type": "mg_frame",
          "source": "cloud_only",
          "script": "第三个，利基DRAM能不能从「涨价撑起来的量」，变成「出货放起来的量」，也就是它和长鑫的代工绑定，能不能让出货量真的起来，把利润的成色，从「风给的」变成「自己挣的」。",
          "visual_description": "清单框架第三格填入「利基DRAM·涨价量→出货量」，配长鑫代工绑定的简化连线图，三格同框完整呈现收束"
        }
      ]
    },
    {
      "scene_id": "A17",
      "scene_title": "收尾结论·最后一棒",
      "scene_design": "专名清单：兆易创新（公司）／ 国家：中国 ／ 年代：现代 ／ 素材来源：主播口播实拍 ／ 素材偏好：核心金句放大，克制收尾",
      "shots": [
        {
          "shot_id": "S60",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "这三个信号没看清之前，我不会对兆易创新下任何「能买」或「不能买」的死结论。",
          "visual_description": "延续三项清单框架整体淡出，盖上「待观察」印章"
        },
        {
          "shot_id": "S61",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "看懂它是一门靠周期的生意，你就不会把「暴增11倍」当成「稳赚」的理由，也不会在它逼近腰斩之后，因为「跌多了」就盲目去抄底。",
          "visual_description": "主播正面口播镜头，语气沉稳"
        },
        {
          "shot_id": "S62",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "周期股最怕的，就是你在利润最高、报表最好看的时候，用成长股的逻辑，接了最后一棒。",
          "visual_description": "核心金句大字砸屏「接了最后一棒」，配一只手伸向坠落物体的简化图形，警示黄强调"
        }
      ]
    },
    {
      "scene_id": "A18",
      "scene_title": "合规声明",
      "scene_design": "专名清单：无 ／ 国家：中国 ／ 年代：现代 ／ 素材来源：主播口播实拍 ／ 素材偏好：标准免责声明，画面克制",
      "shots": [
        {
          "shot_id": "S63",
          "visual_type": "b-roll",
          "source": "cloud_only",
          "script": "踏踏实实做研究，本本分分看数据，以上都是我个人的分析，不构成投资建议，股市有风险，入市需谨慎。",
          "visual_description": "主播口播镜头，平实收尾，不加MG"
        }
      ]
    },
    {
      "scene_id": "A19",
      "scene_title": "互动结尾+预告华友钴业",
      "scene_design": "专名清单：兆易创新（公司）、华友钴业（公司，仅预告提及）／ 国家：中国 ／ 年代：现代 ／ 素材来源：主播口播实拍、下期预告素材 ／ 素材偏好：互动图标点缀，不过度堆砌",
      "shots": [
        {
          "shot_id": "S64",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "兆易创新现在这个价，你是把它当周期股，还是成长股？你觉得这轮存储涨价还能走多久？评论区聊聊。",
          "visual_description": "主播口播镜头叠加评论气泡图标与问号动效"
        },
        {
          "shot_id": "S65",
          "visual_type": "b-roll+mg",
          "source": "cloud_only",
          "script": "觉得这期有帮到你的，点个赞收藏一下，想继续看深度拆解的，关注蛋炒饭财经，提前预告下，下期我们聊最近同样腰斩的华友钴业，大家提前点个关注不迷路。",
          "visual_description": "点赞/收藏/关注图标依次弹出动效，末尾叠加「下期：华友钴业」预告小卡片"
        }
      ]
    }
  ]
}
```
