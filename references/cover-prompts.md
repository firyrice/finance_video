# 封面提示词模板

封面是点击率的最大杠杆之一。财经视频封面要在1秒内传达三件事：**讲哪只股票、什么情绪（涨/跌/警示）、一句勾人的大字**。

## 硬规则：封面必须出现公司名字

每一张封面（B站版和抖音版都是）**必须清晰地显示公司的具体中文名字**，例如"兆易创新""贵州茅台""保利物业"。观众划到封面第一眼就得知道这条视频讲的是哪家公司，不能只有一句情绪大字却看不出是谁。

- 公司名可以是**主标题本身**（比如大字直接写"兆易创新"），也可以作为**副标题/角标**和勾人大字并存（比如大字"闭眼捡钱？"+ 醒目副标"保利物业"）。
- 无论哪种排布，公司名字都要**足够大、足够清晰、不被遮挡**，用真实全称或通用简称，不要用代码代替、不要缩写到认不出。
- 写提示词时，必须显式要求把公司名字写在图上（见下方写法），不能省略。

## 两个平台的差异

| | B站 | 抖音 |
|---|---|---|
| 比例 | 16:9 横版 | 9:16 竖版 |
| 文字量 | 可稍多，主标题+副标题 | 极简，一句大字为主 |
| 构图 | 左右布局，主体+文字分区 | 上下布局，大字压顶或居中 |
| 观看场景 | 桌面/横屏，看得清细节 | 手机竖屏刷流，要更大更冲 |

同一条视频，两版封面的**大字文案可以不同**：B站可以稍完整，抖音要更短更狠。

## 提示词写法

gpt-image-2 对画面描述用英文更稳定，但**需要出现在图上的中文大字，直接在提示词里用中文并明确要求**。一个提示词包含这几块：

1. **画面主体**：K线图/上升或下跌箭头/公司logo氛围/人物表情/大额数字
2. **情绪配色**：
   - 看涨/利好 → 红色为主（中国市场红涨），暖色、上升箭头
   - 看跌/警示 → 绿色或暗色 + 警示黄，下跌箭头
   - 科技股 → 深蓝/黑金、科技感光效
   - 中性分析 → 稳重的深色 + 金色，专业财经感
3. **大字标题**：明确写"图中央用醒目大号中文写：'XXXX'"，字数越少越好（4-8字最佳）
4. **公司名字（必须）**：明确要求图上出现公司中文名，例如"顶部用醒目中文写公司名：'兆易创新'"。可以是主标题，也可以是副标题/角标，但一定要写进提示词、且要求清晰可读。
5. **风格词**：professional financial thumbnail, high contrast, bold typography, cinematic lighting, eye-catching, 4k
6. **排版要求**：文字清晰不被遮挡、主体不要太满、留出文字空间

## 模板示例

**B站版（16:9，看空茅台的选题）：**
```
A professional YouTube-style financial thumbnail, 16:9 horizontal.
Left side: a dramatic downward red candlestick chart trending down.
Right side: dark moody background with dramatic lighting, space for text.
In the center-right, bold large Chinese text: "茅台还能追吗".
Below it, clear medium-size Chinese company name: "贵州茅台".
Bottom smaller Chinese text: "用财报算清楚".
Color scheme: deep red and dark navy, high contrast, warning tone.
All Chinese text must be crisp, correctly written and fully readable, not cropped.
Style: cinematic, high-contrast, bold typography, professional finance channel, eye-catching, 4k.
```

**抖音版（9:16，同一选题）：**
```
A professional vertical thumbnail, 9:16 portrait, for a finance short video.
Background: dramatic dark red gradient with a falling stock chart and downward arrow.
Top-center huge bold Chinese text taking up the top third: "茅台别追".
Directly below, clear bold Chinese company name: "贵州茅台".
Center: a large glowing red downward arrow and blurred candlestick chart.
Color scheme: intense red and black, maximum contrast, urgent emotional tone.
All Chinese text must be crisp, correctly written and fully readable, not cropped.
Style: mobile-first, oversized bold typography, punchy, eye-catching, 4k.
```

## 调用脚本

```bash
python3 scripts/generate_cover.py --platform bilibili --prompt "上面的英文提示词" --output cover_bilibili.png
python3 scripts/generate_cover.py --platform douyin  --prompt "上面的英文提示词" --output cover_douyin.png
```

`--platform` 会自动选择对应的画幅尺寸（bilibili=1536x1024近似16:9，douyin=1024x1536近似9:16）。

## 提示

- 大字文案要和标题、口播稿观点一致，别封面看空、内容看多。
- gpt-image-2 生成的中文偶尔会有错别字，生成后**检查图上文字是否正确**，尤其确认**公司名字有出现、写对了、清晰可读**；错了就调整提示词重生成，或建议用户后期用设计工具替换文字。
- 公司名字上封面是硬要求：如果生成图里公司名缺失或糊掉，必须重生成，不能交付一张看不出讲哪家公司的封面。
- 一次可以先只生成一版让用户看效果，满意了再生成另一版，省额度。
