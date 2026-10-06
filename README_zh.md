# media-to-markdown

<p align="center">
  <a href="README.md"><kbd>🇺🇸 English</kbd></a> · <kbd>🇨🇳 中文</kbd>
</p>

<p align="center">
  <a href="https://github.com/SpiralQWQ/media-to-markdown/releases"><img src="https://img.shields.io/github/v/tag/SpiralQWQ/media-to-markdown?label=version" alt="version"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-3776AB" alt="Python 3.10+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-AGPL%203.0%20%7C%20Commercial-blue" alt="license"></a>
  <a href="https://github.com/SpiralQWQ/media-to-markdown/stargazers"><img src="https://img.shields.io/github/stars/SpiralQWQ/media-to-markdown?style=social" alt="stars"></a>
</p>

**本地视频 / 图集 / 音频 → 清洗过的、带时间轴的 Markdown。**

`media-to-markdown` 把**本地媒体文件**转成一份「半成品 md」：台词与画面文字按时间戳交错排好，图集按阅读顺序合成一份，音频转成带时间戳的行。转换过程中顺手清洗——去水印、去渠道标签、去 OCR 碎屑——但**不做总结、不改写、不生成教学笔记**，那是下一环，单独一个项目。

## 目录

- [它能做什么](#它能做什么)
- [为什么需要它](#为什么需要它)
- [安装](#安装)
- [配置](#配置)
- [用法](#用法)
- [产物结构](#产物结构)
- [架构](#架构)
- [目录树](#目录树)
- [测试](#测试)
- [路线图](#路线图)
- [常见问题](#常见问题)
- [法律 / 免责声明](#法律--免责声明)
- [许可](#许可)
- [💛 支持 / 打赏](#-支持--打赏)

## 它能做什么

| 模态 | 输入 | 链路 | 产物 |
|---|---|---|---|
| 🎬 视频 | `.mp4 .webm .mkv .mov .flv .avi` | 提音频 → ASR 转写；抽帧 → OCR（可选 GLM 画面理解）→ 清洗 → 按时间交错 | `🎤 台词` 与 `🖼 画面文字` 对齐在同一条时间轴上 |
| 🖼️ 图集 | `.jpg .jpeg .png .webp .gif .bmp`（多张文件或整个文件夹） | 逐张 OCR（按坐标还原阅读顺序）→ 清洗 → 合成 | `【图1】…【图N】` 合成一份，或每张独立一份 |
| 🎧 音频 | `.mp3 .wav .m4a .flac .ogg .aac .wma` | ASR 转写 → 清洗 → 按时间排 | `[MM:SS] 🎤 句子` |

产物统一落在 `output/cache/<名称>/` 下的 `<名称>_clean.md`，中间产物一起留在那里，重跑时直接复用、不重复转写。

## 为什么需要它

原始的 ASR 和 OCR 结果没法直接喂给下游：

- 转写丢掉了画面信息，视频原本的意思就散了；
- 逐帧 OCR 是一堆没有时间锚点的碎片；
- 两者都夹带水印、渠道名、页码和识别噪点。

这些是机械活，机械活就该交给代码而不是提示词。`media-to-markdown` 的产出是一份确定性的、带时间轴、已清洗的 Markdown——对下游来说是一个稳定契约。

## 安装

```bash
git clone https://github.com/SpiralQWQ/media-to-markdown.git
cd media-to-markdown
pip install -e .            # OCR + 清洗（视频抽帧 OCR、图集）
pip install -e ".[asr]"     # 需要语音转写（视频/音频）时再加装（FunASR + PyTorch，较重）
```

**ffmpeg** 是必须的系统程序（提音频、抽帧），要能在 `PATH` 里找到：

- Windows：`winget install Gyan.FFmpeg`
- macOS：`brew install ffmpeg`
- Linux：`sudo apt install ffmpeg`

**引擎解释器**：默认 ASR 和 OCR 都跑在和包同一个解释器下，所以装完 `pip install -e .` 就能用。如果你习惯把 FunASR 和 RapidOCR 各自放在独立虚拟环境里，用 `ASR_PY` / `OCR_PY` 指向它们的 python 可执行文件即可（见 `src/media_to_markdown/configs/.env.example`）。

**GLM（可选、付费）**：加 `--glm yes` 会让 `glm-4.6v-flashx` 描述每个采样画面里有什么——对讲义、图表有用，但完全可选。在运行目录放一个 `.env` 写 `GLM_API_KEY`；没有 key 时 `--glm` 会自动退回纯 OCR。

## 配置

全部可选——什么都不配也能跑：OCR 本地跑，GLM 关闭。

| 变量 | 默认值 | 作用 |
|---|---|---|
| `ASR_PY` | 当前解释器 | 跑 FunASR 引擎的解释器——只有 FunASR 装在另一个虚拟环境时才需要设 |
| `OCR_PY` | 当前解释器 | 跑 RapidOCR 引擎的解释器 |
| `GLM_API_KEY` | （未设） | 智谱 GLM 密钥；只有 `--glm yes` 时才需要 |
| `GLM_API_URL` | `https://open.bigmodel.cn/api/paas/v4/chat/completions` | GLM 接口地址 |
| `GLM_MODEL` | `glm-4.6v-flashx` | GLM 视觉模型 |

把它们写进**你运行命令所在目录**的 `.env` 文件（已被 git 忽略），或直接导出为普通环境变量。模板见 `src/media_to_markdown/configs/.env.example`。交互式向导（`--wizard`）写的就是引擎读的那份 `.env`。

## 用法

```bash
# 视频：台词 + 画面文字，按时间戳交错
python -m media_to_markdown lecture.mp4 --glm no

# 视频 + 画面理解（需要 GLM_API_KEY）
python -m media_to_markdown lecture.mp4 --glm yes

# 图集：多张合成一份
python -m media_to_markdown page1.png page2.png page3.jpg

# 整个图片文件夹（默认每张独立一份）
python -m media_to_markdown ./slides/

# 音频
python -m media_to_markdown interview.wav

# 交互式向导：抽帧间隔、是否用 GLM、产物目录、中间文件处理……
python -m media_to_markdown lecture.mp4 --wizard
```

各阶段实时打印进度（`[ASR]` / `[OCR]`），已完成的阶段重跑时自动跳过。

## 产物结构

```
output/cache/<名称>/
├── <名称>_clean.md          # ← 交付物
├── <名称>_clean.json        # 清洗后转写（保结构、保时间戳）
├── <名称>.json              # ASR 原始输出（毫秒级分段）
├── <名称>_visual.txt        # 逐帧 OCR 原始结果
└── <名称>_visual_clean.txt  # 清洗后逐帧结果，每段带 [MM:SS]
```

## 架构

```
cli.py                     薄入口：判断输入类型 → 路由到对应模态
└── src/
    ├── core/              各模态的编排（video / image / audio）
    ├── engines/           外部引擎（asr / ocr / glm_vision / ffmpeg）
    ├── clean/             清洗规则（transcript / visual / plain）
    ├── assemble/          产物组装（interleave / album / timeline）
    └── configs/           交互向导 + 配置
```

依赖单向：`cli → core → {engines, clean, assemble}`。引擎不知道流水线的存在，流水线也不碰 ffmpeg / FunASR 的内部细节——所以任何一个环节都能整体替换：换 ASR 引擎只需要改 `engines/asr.py`。

## 目录树

```
media-to-markdown/
├── cli.py
├── requirements.txt
├── src/
│   ├── core/                video.py · image.py · audio.py · base.py
│   ├── engines/             asr.py · ocr.py · glm_vision.py · ffmpeg.py
│   ├── clean/               transcript.py · visual.py · plain.py
│   ├── assemble/            interleave.py · album.py · timeline.py
│   └── configs/             wizard.py · .env.example
├── tests/                   108 个用例
│   ├── sample/              合成样例（不含任何第三方素材）
│   └── test_*.py
└── assets/                  打赏码
```

## 测试

```bash
python -m pytest tests -q
# 108 passed
```

`tests/sample/` 下的样例全部是合成数据、可复现——本仓库不携带任何第三方截图或媒体素材。

## 路线图

见 [`ROADMAP.md`](ROADMAP.md)。近期：视频自带字幕轨时优先用字幕、ASR 支持选用 GPU。

## 常见问题

**能从链接下载视频吗（抖音 / YouTube / B站）？**
不能。本项目只读**本地文件**。想要"贴链接出笔记"的流水线，那是另一个项目。

**会写学习笔记吗？**
不会。它止步于"清洗过的、带时间轴的 Markdown"。把它变成教学笔记是独立的一环，有独立项目负责。

**只支持中文吗？**
清洗规则是按中文 ASR 输出调的（中文标点、口头禅、渠道水印），偏笔记向的措辞也是中文。引擎本身是多语言的，但非中文输出没有专门调过、也没测过。

**一定要用 GLM 吗？**
不用。OCR 本地跑、免费（RapidOCR）。GLM 只是补一句"画面里有什么"，且只在你显式传 `--glm yes` 时才调用。

**中途断了要重头再来吗？**
不用。引擎产物会复用：`<名称>.json` / `<名称>_visual.txt` 已存在就跳过该阶段，从清洗接着往下走。

## 法律 / 免责声明

本工具面向**你有权处理的内容**——自己录的、已获授权的、或你依法可以访问的素材。转写并再分发他人的视频、课程或书籍可能侵犯其权利。使用方式由你负责，也请自行遵守所涉平台或服务的条款。本项目按"现状"提供，不附带任何担保，作者不对误用承担责任。

## 许可

开源版采用 [AGPL-3.0](LICENSE)；商业授权见 [COMMERCIAL.md](COMMERCIAL.md)。

## 💛 支持 / 打赏

如果这个项目帮你省了点时间，欢迎请我喝杯咖啡 ☕。打赏完全自愿——项目会一直免费开源。

<p align="center">
  <img src="assets/donate_wechat.jpg" alt="微信" width="200">
  <img src="assets/donate_alipay.jpg" alt="支付宝" width="200">
</p>
