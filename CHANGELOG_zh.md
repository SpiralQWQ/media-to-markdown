# Changelog（简体中文）

<p align="center"><a href="CHANGELOG.md"><kbd>🇺🇸 English</kbd></a> · <kbd>🇨🇳 中文</kbd></p>

本项目的所有重要变更都记录在此，格式遵循
[Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与
[Semantic Versioning](https://semver.org/lang/zh-CN/)。

1.0.0 之前的版本记录的是这个工具作为个人工作脚本的阶段。为保留历史而全部保留，
内容已按原始工作日志重写——内部流程记录已剔除，变更本身未做改动。

## [1.0.0] - 2026-10-06

_首个公开发布：完成打包、清除所有与本机绑定的内容、面向贡献者开放。_

### Added

- 可安装的打包：`src/media_to_markdown/` 目录结构、`pip install -e .`、`python -m media_to_markdown` 入口，以及 `media-to-markdown` 命令行脚本。
- `pyproject.toml`：把语音引擎做成可选依赖组（`.[asr]`），只做 OCR 的用户不必安装 PyTorch。
- 持续集成：测试在 Linux / Windows / macOS 三平台、Python 3.10 / 3.11 / 3.12 三个版本上运行，另加语法门禁与入口点冒烟测试。
- 社区文件：`CONTRIBUTING.md`、`SECURITY.md`、`CODE_OF_CONDUCT.md`、issue 与 PR 模板、`ROADMAP.md`。
- README 新增「配置」一节，逐个说明环境变量；新增「路线图」一节。
- 向导可选**画面变化才抽帧**（省帧模式）——这是引擎早就支持、但命令行一直没暴露的能力。

### Changed

- 向导不再问"问了也不生效"的问题。课程名、笔记命名、笔记风格、说话人、批量模式、缓存位置，这些都属于本工具已经不再做的"生成笔记"环节，已一并移除。换上来的是真正生效的四项：抽帧间隔、抽帧方式、产物目录、中间文件处理。
- 保存过的向导配置会丢弃已不存在的键，不再让它们永远残留。
- 向导保存的 GLM 密钥现在与 GLM 引擎读取的是同一个 `.env`。此前向导存在 `configs/.config/`，而引擎读的是 `engines/.config/`——向导刚验证通过的密钥，引擎永远找不到。
- `ASR_PY` / `OCR_PY` 默认改为当前解释器，不再指向作者机器上的固定路径。
- 向导显示的默认输出根目录改为当前工作目录，与管线实际落盘位置一致。
- 全部测试样例改为合成数据，仓库不再携带任何第三方素材。

### Fixed

- `clean/visual.py` 不再把「知识点」当作水印词。这是学习类素材里最常见的词之一，过滤规则此前在误删正文。
- 段落清洗不再把「不含 ASCII 字母/数字、也不含中日汉字」的整行清空——俄文、韩文、阿拉伯文、全角字母此前会被静默丢掉。
- GLM 重试改为最多 3 次，超过就只写 OCR 内容；此前密钥缺失时会无限重试，把整批任务卡死。
- 交错组装不再丢弃 99 分钟之后的画面帧（长视频结尾画面此前会无声消失）。
- 转写 JSON 里 `segments` / `sentences` 显式为 `null` 时不再崩溃；时间戳非数字也不再中断组装。
- 英文大小写归一不再改写更长单词内部（`MyPOWERSHELLish` 保持原样），同时中英混排里照常归一。
- CLI 在任何输入失败时返回非 0 退出码，脚本和 CI 才能感知。
- 缺少 `ffmpeg` 时抛出的错误会说明怎么装，不再是裸的 `FileNotFoundError`。
- 抽帧上限警告只在真的被截断时才打印；此前长视频即使抽全了也会误报"已被截断"。
- 清理死代码：未使用的 `numpy` 导入、未使用的 `re` 导入、转写去重里形同虚设的中英文分支，以及两个没有调用方的函数。

### Removed

- PDF 图片线的三个辅助脚本（`batch_images.py`、`embed_image_notes.py`、`fix_md_image_refs.py`）与 `legacy/` 旧脚本目录没有带进本次发布。它们是为一条私有的笔记流水线写的，并且依赖另一个独立项目，拿出去单独跑不起来。

### Security

- 源码树中不再残留任何凭证或与本机绑定的绝对路径。
- 随仓库发布的测试样例不含任何第三方截图、媒体或书籍正文。

## [0.10.1] - 2026-08-29
_图片输出格式对齐，清洗接入图片转写，嵌入脚本迁入 src/scripts/。_

### Changed

- **图片输出格式对齐**：`process_images_to_mds` 输出改为 `## 图片内容（OCR）` + `## GLM 画面理解`，与已转换的存量图片格式一致，新老输出无缝衔接。
- **清洗接入图片转写**：`process_images_to_mds` 接上 `clean_plain_text`（删除界面噪音行与标签、标点规整），转写即清洗。
- **嵌入脚本归位**：`embed_image_notes.py`（在 full.md 图片位置嵌入对应图笔记，输出 AI 友好的自包含文档）迁入 `src/scripts/`；`main` 支持 argv 传参；补 4 个单测（嵌入 / 缺笔记保留 / 分卷递归找笔记 / dry-run）。

### Fixed

- `embed_image_notes.py` 入口不传递退出码（传错路径永远 exit 0）→ 改为 `sys.exit(main())`，传错路径实测 exit=2。
- 边界加固：空笔记文件、无 GLM 段笔记、同图重复引用、中文 stem、自定义目录名（`--images-dir` / `--notes-dir`）均有用例锁定。

## [0.10.0] - 2026-08-23
_PDF 图片模式、批量转换与图片引用改写。_

### Added

- **PDF 图片模式**：`core/image.py` `process_images_to_mds()`——图片文件夹内每张图输出独立同名 md，收进源目录同级 `images_notes/`；支持断点续传（已生成跳过）+ GLM 失败重试直到成功。
- **图片向导多询问**：`configs/wizard.py` 在转换前问清「合成一份 vs 每张独立」「GLM 用 flashx 稳定版还是 flash 免费版」「请求间隔几秒」「断点续传还是从头」「跳过哪些文件夹」，配置落盘后续沿用。
- **cli 图片文件夹**：`python -m media_to_markdown <图片文件夹>` 输出每张独立 md；`--wizard` 可选「合成一份」；glm / delay / model / resume 全透传。
- **批量遍历**：`src/scripts/batch_images.py`——`--root` 递归扫描含图文件夹逐个转换，`--skip` 跳过指定，断点内建，向导配置兜底 + CLI 覆盖。
- **引用改写**：`src/scripts/fix_md_image_refs.py`——full.md 中的图片引用改写为 `images_notes/*.md` 链接，缺对应 md 时保留原样。

### Changed

- `process_images_to_mds` 真限流：两次 GLM 请求间 `sleep(delay)`（免费版防 429）；模型透传（flashx / flash）经环境变量覆盖；`resume="no"` 全部重转。

## [0.9.5] - 2026-08-22

_实时进度反馈与批处理错误恢复。_

### Added

- **进度反馈**：实时打印 ASR/OCR 子进程输出，带 [ASR]/[OCR] 标签
- **批处理序号**：视频/音频循环加 [1/N] 序号，多文件处理时清晰可见
- **错误恢复**：`_progress.json` 记录全部完成状态，清洗 + 组装断点跳过

### Changed

## [0.9.4] - 2026-08-22

_按目录契约重构，根目录 13 → 5。_

### Changed

- 根目录整理：13 → 5（src/ output/ docs/ tests/ + 入口）
- 源码集中到 src/（assemble/clean/configs/core/engines/scripts）
- 产物隔离到 output/（cache/temp/验证）
- cli.py 及所有模块、测试的路径引用同步更新

## [0.9.3] - 2026-08-21

_稳定性修复：时间线排序与空源防呆。_

### Fixed

- 音频时间线补时间排序
- core/video | audio 引擎失败时空源防呆（返回 error 不再崩溃）
- cli._classify 空值防呆
- core/image GLM 异常外层 try 降级

### Changed

- 新增 76 个单元测试（tests/，含 sample 样例），全部通过

## [0.9.2] - 2026-08-19
_向导按媒体类型感知，只问相关问题。_

### Added

- **向导类型感知**：`run_wizard(media_type=…)` 按类型只问相关项——视频全问（画面 / GLM / 说话人 / 课程），图集只问 GLM（逐张看懂），音频只问说话人；提示文案与收尾 summary 均贴合类型。
- **cli `--wizard`**：按媒体类型弹出对应向导并透传 glm；不带 `--wizard` 时沿用默认 / `--glm`（兼容旧行为）。
- 边界用例（非法 / 超长 / 空回车）均不崩溃；cli、批量等调用路径产物一致。

## [0.9.1] - 2026-08-19
_图片输出对齐视频，图集合并为一份。_

### Changed

- **图片链路对齐视频**：每张图输出 `【图片N】+ [画面文字 OCR] + [GLM 画面理解]`（同引擎 OCR 坐标排序 + GLM），仅无时间线（用图片编号）。
- **cli 图集批量**：`python -m media_to_markdown 图1 图2 图3` 合成一份图集 md（`【图片1】…【图片N】`），不再各成一份；视频 / 音频仍各自独立。
- 多图合并输出已实测通过。

## [0.9.0] - 2026-08-19
_新增图片、音频链路，与视频并列。_

### Added

- **图片链路**：`core/image.py` + `assemble/album.py`——图片 / 图集 → OCR（必做，坐标排序）+ 可选 GLM → 清洗 → 图序半成品 md。
- **音频链路**：`core/audio.py` + `assemble/timeline.py`——音频 → ASR → json → 清洗 → 按时间排序 md。
- `engines/ocr.py` 复用图片 OCR（`ocr_image_to_text` / `ocr_images_to_text`），与视频帧共用坐标排序。
- `cli.py` 三模态路由（视频 / 图片 / 音频），六类防呆保留。

### Changed

- 产物同步：视频 = 时间交错、图片 = 图序、音频 = 按时间；半成品 md 只清洗不整理；json 始终音频转写、txt 始终画面 / 图片。
- 图片 / 音频默认输出归入转写缓存目录（图片 / 音频），不污染根目录。
- 调用路径一致性抽样通过；真实图片 / 音频跑通。

### Security

- ASR / OCR 解释器走环境变量 + 包默认；GLM 可选降级；`.env.example` 无密钥。

## [0.8.0] - 2026-08-19

_目录重构：入口薄 + 业务域 + 分层。_

### Changed

- 脚本平铺 → 目录契约：`cli.py`（薄入口路由）→ `core`（业务域：base/video）→ `engines`（asr/ocr/glm_vision/ffmpeg）+ `clean`（transcript/visual/plain）+ `assemble`（interleave）+ `configs`（wizard/.env.example）。
- 旧 `scripts/` 与旧主流程归档至 `scripts/_legacy/`；文档归 `docs/`；旧任务/日志归 `temp/_legacy_tasks/`。
- 转写引擎 → `engines/asr.py`；帧/图 OCR（含坐标排序）→ `engines/ocr.py`；清洗零依赖内置（不再依赖 text-cleaning-engine）。
- 真实数据端到端测试（音频 107 / 图片 179）零回归。

### Added

- `core`/`engines`/`clean`/`assemble` 各域零外部依赖，单向依赖 core → {engines,clean,assemble,configs}。
- `cli.py` 三模态识别（视频已接入；图片/音频为二阶段 stub）+ 六类防呆。

### Security

- ASR/OCR 解释器走环境变量 + 包默认；.env.example 仅示例，无硬编码密钥。

## [0.7.1] - 2026-08-11

_补丁 C 闭环：review 提示现在列出具体段。_

### Changed

- `course_video_to_notes.py` review_hint：从"只有数量"改为**列出具体段**
  - 每段带 `[MM:SS]` 时间戳 + 前 60 字文本
  - 最多列 10 段，超 10 段提示"其余 N 段略"（防提示过长）
  - 只读 review/confidence 字段，不改值
  - 示例：
    ```
    ⚠️ 转写有 3 段低置信待复核，笔记对应知识点处标 [复核]（保留原文，仅提示存疑）：
      [00:03] w s l 粘连残留
      [01:05] 另一个存疑段内容比较长需要截断显示
    ```
- 4 场景测试（3段/12段截断/无review/字段只读）通过；全脚本语法 + 向导回归 31 PASS + 补丁集成无破坏。

## [0.7.0] - 2026-08-11

_听写能力 5 项补丁（195 仓调研驱动）。_

### Added

- **VAD 静音预过滤**（silero-vad）：转写前用 silero-vad 裁剪纯静音头尾，降幻觉词+省 ASR 算力；guard 逻辑（语音占比/首尾静音阈值）防误删讲课停顿
- **热词后处理纠错层**（asr-hotword 思路）：三层纠错——精确替换（corrections.json）+ 中文同音字滑动窗口（拼音≥95% 才纠）+ 英文专名大小写归一；防误伤（字数不同不纠）
- **低置信段标记复核**（transcript-critic 思路）：confidence<0.5 的段标 `review:true`，笔记生成提示"有 N 段转写存疑待复核，对应处标 [复核]"
- **深度学习降噪隔离化**：denoiser 与 FunASR 的 omegaconf 冲突会破坏转写 → 改为独立环境（`DENOISE_PY` 环境变量），未配置安全跳过
- **ct-punc 标点**：确认已集成（SenseVoice `punc_model="ct-punc"`），实机验证补标点正常
- 新增依赖：silero-vad 6.2.1 / pypinyin 0.55 / onnxruntime 1.28（rapidfuzz 已有）

### Fixed

- **Bug · silero 样本索引 vs 毫秒单位错配**：VAD 检测 start/end 是样本数，误当毫秒算占比 → 修复 `/sr` 转秒（防误裁剪）
- **Bug · 英文 fuzz 误伤**：整词 fuzz 对英文无效且 I→AI 误伤 → 改中文同音滑动窗口（字数相同+拼音≥95%）+ 英文大小写归一
- **Bug · omegaconf 冲突破坏转写**：denoiser 依赖 omegaconf 1.x 与 FunASR(需≥2.0)冲突，安装会破坏核心转写 → 隔离为 DENOISE_PY 独立环境

### Changed

- 向导回归 31 PASS / 全补丁集成 7 PASS / 降噪安全 3 PASS / 全脚本语法通过。

## [0.6.6] - 2026-08-10
_实时进度条与阶段耗时总览。_

### Added

- 恢复实时进度显示：新增 `run_stream()`，子进程 stdout 直接透传到终端，stderr 单独捕获供错误诊断，转写/OCR 的逐段进度不再被吞进内存。
- 转写、OCR、GLM 三处进度条：由逐行 print 改为单行刷新，显示百分比、当前/总数和预估剩余时间。
- 阶段耗时总览：每阶段结束打印用时，最终阶段显示总运行时间。

### Changed

- `course_video_to_notes.py`：新增 `run_stream()` 和 `_fmt_dur()`；转写/OCR 改用 `run_stream()`；`process()` 三阶段计时。
- `scripts/transcribe_funasr.py`：新增 `_progress_bar()`；转写循环改进度条；stdout reconfigure。
- `scripts/video_frames_ocr.py`：新增 `_progress_bar()`；OCR/GLM 循环改进度条；stdout reconfigure。
- 向导回归 31 项测试通过。

## [0.6.5] - 2026-08-10
_课程名规则加入向导，问题顺序重排。_

### Added

- 问题6 课程名规则：三种规则存配置，之后所有视频沿用。此前课程名由 `detect_parts()` 自动推断，用户无法选择。
  - A. 自动识别（默认）：从路径/文件名推断，识别不到用所在文件夹名。
  - B. 固定课程名：所有视频归到同一个课程，输入课程名后显示路径预览并确认。
  - C. 源文件名：统一用视频所在文件夹名做课程。
  - 每项选择后都显示具体路径预览并确认，N 打回重选。
- 配置持久化：DEFAULT_CONFIG 加 `course_rule`（auto/fixed/folder）和 `course_fixed`，主脚本通过环境变量传递。
- 主脚本应用：`process()` 在 `detect_parts` 后按规则覆盖 course。
- 命名预览联动：命名预览里的「课程名」按课程名规则显示。
- 收尾清单联动：`_print_summary` 显示课程名来源说明。

### Changed

- 问题顺序重排：笔记结构三问（存储根→课程名→命名）连续，中间产物两问放最后。
- `wizard.py`：新增 `_ask_course_rule()`；`_preview_naming()` 加 `course_txt` 参数；`_ask_naming()` 按课程名规则联动；run_wizard 问题 6/7 与 8/9 互换。
- `course_video_to_notes.py`：main() 传 `COURSE_RULE`/`COURSE_FIXED` 环境变量；`process()` 应用规则。

## [0.6.4] - 2026-08-10
_存储根目录与命名问题增加路径可视化确认。_

### Fixed

- 问题5 默认位置不透明：选「用默认目录」时也显示具体绝对路径预览，确认后继续。
- 问题8 命名无路径反馈：选定命名后显示完整最终路径（如 `课程/第XX讲/NN_XX_X_小节名.md` 或 `前缀_小节名.md`），确认后继续。
- 问题8 空前缀：自定义前缀不填时提示并打回重选。

### Changed

- 新增 `_default_root()`：自动推导默认根目录（与主脚本项目根逻辑一致，向上 3 级）。
- 新增 `_ask_storage_root()` / `_ask_naming()`：统一「预览 → 确认 → N 打回重选」交互。
- `_preview_storage()` 增强：输出含具体绝对路径的存储结构预览。
- 新增 `_preview_naming()`：按命名规则显示最终笔记文件路径示例。
- 主脚本命名接线（`NOMENCLATURE` 环境变量）不变，无回归。

## [0.6.3] - 2026-08-10
_笔记命名规则增强。_

### Added

- 问题8 自定义命名：新增选项 C「自定义前缀」，输入前缀生成 `前缀_小节名.md`。
- 命名配置接线：向导 naming 配置（default/simple/custom）通过环境变量传递到主脚本，`process()` 生成笔记时提示按所选规则命名。

## [0.6.2] - 2026-08-10

_GLM 错误分类、字幕转 JSON、清洗钩子预留。_

### Added

- GLM 错误分类：测试失败区分 401/403（Key 无效）、400/404（模型名错误）、网络错误（重试），分别给出明确提示，不再笼统提示"模型名有误"误导用户。
- 字幕轨提取转 JSON：`extract_subtitle_to_json()` 检测到内嵌字幕轨后，通过 ffmpeg 提取并解析为与 ASR 同构的 JSON（confidence 0.99），跳过音频转写，更准确且更省资源。
- 清洗钩子预留：`clean_transcript_hook()` 占位，未来接入清洗工具清理 JSON 噪音，当前返回 False，不影响现有流程。

### Changed

- 转写输出统一为 JSON（含时间戳和 confidence），无论来源是音频 ASR 还是视频字幕。
- SRT 仅作为回看产物，由 JSON 导出。
- 清洗对象为 JSON（数据源），而非 SRT（展示格式）。

## [0.6.1] - 2026-08-10

_交互体验修复。_

### Fixed

- "默认"标签重复：选项文案"开启（默认，推荐）"与系统自动标记重复，改为"开启（推荐）"。
- 存储确认选 N 后未返回重填：确认选 N 直接退默认，改为回到重填路径（选 N 后重输，回车才退默认）。
- GLM 测试失败未返回：失败直接跳走，改为循环重试（重新填 Key/模型或退出）。
- 缓存路径错位：确认自定义根目录后缓存仍落默认位置，验证 `global` 覆盖正确跟随（选 Y 确认后缓存存至自定义根目录下的 `_转写缓存`）。

## [0.6.0] - 2026-08-10

_GLM 配置增强、课程归类、存储预览、失败处理。_

### Added

- GLM 配置显示三选：已配置时显示供应商/模型/接口，A 用当前 / B 换供应商/模型 / C 只换模型。
- 换供应商：预置智谱/阿里/百度/OpenAI + 自定义填地址 + Key + 模型名，测试连接成功才保存。
- 只换模型：保留供应商/地址/Key，填新模型名，测试门禁通过才保存（失败不改）。
- 多供应商持久化：`.env` 新增 `GLM_MODEL` 和 `GLM_PROVIDER` 字段，`glm_vision.py` 从 `.env` 读取自定义供应商/模型。
- 课程归类 4 选项：`detect_parts` 识别失败时，提供 A 父目录名 / B 自定义 / C 系统推荐 / D 未分类课程，显示完整路径预览并确认。
- `detect_parts` 父目录回退：不再默认硬编码课程名，改用视频父目录名作为课程。
- 存储根目录路径预览：输入后显示笔记/视频/缓存完整结构，确认（Y/N/无效重填）。
- GLM 失败处理：内容敏感（400）不重试，逐帧三选（跳过/停止/重试）；网络错误重试 3 次后三选；不再 `sys.exit` 卡死，停止/跳过保留已处理内容并标记未处理内容，流程继续。
- 实时进度：转写逐段显示"第 N/总段 + 时间 + %"，OCR 逐帧显示"第 N/帧 + %"。

### Fixed

- 向导模块缺少 `import re`：`ask_course_classification` 使用了 `re` 但未导入，已补上。
- `detect_parts` 课程回退回归：改空默认后示例课程路径无法解析，增强目录名识别并加父目录回退双保险。
- "默认"标签重复：选项文案混写"（默认）"与自动标记重复，统一由系统自动标记，文案只留"（推荐）"。

## [0.5.0] - 2026-08-10

_路径动态化与存储配置向导。_

### Added

- 路径动态推导：BASE 为脚本所在目录，项目根目录为其上级，缓存/笔记目录相对推导，脚本迁移或换盘自动跟随，不再硬编码绝对路径。
- 自定义根目录：环境变量 `NOTES_ROOT` 覆盖默认根，只需填最外层地址，内层 `NoteBooks/`、`_转写缓存/`、`课程/第XX讲_标题/` 结构自动固定。
- 向导存储问题 5-8：新增四问——存储根目录（默认/自定义）、中间产物清理（保留/精简/全清理）、缓存位置（独立/跟笔记）、命名规则（默认/只留小节名）。
- 存储配置持久化：保存/加载包含存储字段，兼容旧配置（缺省自动补默认）。

### Fixed

- `main()` 缺少 `global` 声明：`main()` 里覆盖项目根目录/缓存/笔记目录是局部变量，不影响 `process()` 用的全局变量，已加 `global` 声明，否则自定义根目录不生效。
- 真实路径讲次解析失败：目录名 `第02讲_标题`（含下划线）不匹配 `isdigit()`，讲次落到默认 00，改为从文件名正则回填（`2-1` → 讲次 `02`）。
- `OCR_INTERVAL` 读取时机：模块加载时固化 0.5，`main` 里向导设 1.0 不生效，`process()` 改为调用时读取环境变量。

## [0.4.0] - 2026-08-10

_工作流能力升级——基于 200 个转写工作流仓库的调研，对工作流进行系统升级。_

### Added

- **前置热词注入**：FunASR 升级 1.4.0 → 1.4.1；`corrections.json` 中的目标词升级为模型级 `hotword=` 解码偏置，从源头提升识别准确率，而非事后纠错
- **置信度字段**：转写 JSON 的 segments/sentences 新增 `confidence` 字段（启发式评估：碎片 / 粘连 / 重复 / 长度），低置信段可标记交人工复核
- **SRT 字幕导出**：转写后自动导出 .srt 文件，便于复习、切片与回看
- **笔记说明书补丁**：`note_style_spec.md` 新增重要性规则、[unclear] 规则、三分法分节与章节分层生成（先出大纲再分层撰写）
- **口语规范化增强**：重复词分级清理——删除无意义填充词（如"呃呃呃"），保留语气重复（如"重要！重要！"）
- **帧预算自适应**：抽帧上限按视频时长动态计算（100 分钟 → 12000 帧），不再固定 6000 帧截断长视频
- **GLM 失败重试**：关键帧 GLM 调用失败自动重试 3 次，仍失败则停下等待处理，绝不静默跳过
- **依赖预检**：入口新增 `--precheck`，检查 ffmpeg / ffprobe / rapidocr，缺失即报错并定位
- **降噪开关 + 自动检测**：ffmpeg 能量分析自动检测噪声水平（DENOISE=auto/on/off），噪声素材自动提示
- **音频重建缓存**：音频重建加入视频指纹（大小 + 时间）缓存，修复过的视频直接复用，免重复修复
- **转写配置向导**：新增 `wizard.py` 交互式向导（精读 / 快速 + 抽帧 + GLM 多供应商配置 + 说话人），批量模式记忆设置；`--no-wizard` 可跳过
- **字幕自动检测**：新增 `detect_subtitle_track()` 探测内嵌字幕轨，有字幕时优先使用字幕，OCR 降频至 5s 仅看图表
- **批量并行**：新增 `--parallel N` 多进程并行转写（默认关闭，精读模式用串行）

### Fixed

- **置信度误判**：孤立单字母正则误判正常冠词（如 "is a" 中的 a）→ 改为连续两个孤立单字母才判定
- **GBK 解码崩溃**：ffmpeg volumedetect 输出含非 UTF-8 字节 → 增加 `encoding="utf-8", errors="replace"`
- **噪声阈值误判**：干净课程语音（mean=-23.6）被误判为 noisy → 阈值 -28 → -18，动态范围 42
- **向导 emoji 崩溃**：✔/✗ 在 GBK 终端触发 UnicodeEncodeError → 换用 ASCII 字符 + stdout reconfigure
- **英文粘连残留**：SenseVoice 音节级拆分（"O kay" → "Okay"）→ 新增 `_SENSEVOICE_SPLITS` 字典（50+ 词）与 `merge_sensevoice_splits()`，不误伤正常冠词（如 "a few"）
- **OCR scene 集成**：`OCR_INTERVAL=scene` 时 smart_frame 分支把 `scene` 当固定间隔传给 `--interval` 导致报错 → 重构 OCR 参数逻辑（scene / 固定 / 字幕 3 种组合正确分流）

## [0.3.0] - 2026-08-09

_全量自我检查后的修复工作流。_

### Added

- **音频自动重建**：检测到 AAC 流损坏时，自动按 60s 分段探测可解区并拼接完整音频。实测一段损坏视频 1 秒自动拼出 218s（比手动拼接 205s 更完整）
- **命名统一**：课程目录 = `01-样本课程`、缓存讲次 = `第03讲`、笔记讲次 = `第03讲_Minimum Edit Distance`、小节 = `源数据_3-1_标题`（讲次-小节不补零）

### Fixed

- **音频损坏误判**：音频时长校验在 wav 损坏读不出时长时返回 True（误判为一致），会跳过音频重建 → 改为 wav 不可读（ad≤0）返回 False，触发自动重建
- **拼接可靠性**：音频重建的段拼接用 `-c copy`（不重编码），对头部异常的段可能失效 → 改为重编码拼接（`-ar 16000 -ac 1` 统一参数）
- **OCR 截断提示不明确**：`MAX_FRAMES=6000` 截断超长视频时提示模糊 → 改为明确提示"约 XX 分钟视频被截断，需调大 MAX_FRAMES"
- **讲次标题映射**：脚本讲次名 `第03讲`（无标题）与笔记目录名 `第03讲_Minimum Edit Distance`（带标题）不一致，导致视频复制到错误目录分层 → 新增 `LECTURE_TITLES` 映射与 `lecture_note_name()`：缓存用无标题，笔记用带标题
- **断点续跑误判**：损坏音频生成的 json（覆盖度低）被误判为已完成 → 改为校验 json 覆盖度（≥70% 才算完成），不足则重新转写
- **无扩展名视频被跳过**：缺 .mp4 后缀的文件被 `endswith` 过滤 → 改为 ffprobe 探测格式识别

## [0.2.1] - 2026-08-09

_CPU 限线程优化。_

### Changed

- **OCR 线程控制**：`RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1)` 使用官方 config 参数。效果：线程 95 → 3-4，单帧快 33%（3.03s → 2.02s），CPU 占用降 96%。关键点：环境变量（OMP/ORT_*）对 onnxruntime 无效，必须用官方参数（已调研 GitHub 源码确认）

## [0.2.0] - 2026-08-09

_目录规则确立。_

### Added

- **目录结构**：

  ```
  笔记目录/课程/第XX讲_标题/        ← 笔记平铺外层 + 源数据子文件夹（只留视频）
  转写缓存/课程/第XX讲/源数据_XX_X/   ← 中间产物（wav + json + visual.txt）
  ```

- **质检铁律**：每转完一个检查 ① 音频 vs 视频时长一致 ② 转写质量 ③ 画面 OCR/GLM ④ 笔记格式
- **讲次标题映射表**：为样本课程（23 讲）建立讲次标题映射

## [0.1.0] - 2026-08-08

_初始搭建。_

### Added

- **主脚本**：创建 `course_video_to_notes.py`（本地版，去掉在线视频下载，直接读取本地 mp4）
- **复用既有引擎**：`transcribe_funasr.py`（SenseVoice auto 中英）/ `video_frames_ocr.py`（OCR + GLM）/ `glm_vision.py`
- **默认配置**：OCR 每秒 2 帧（OCR_INTERVAL=0.5）· GLM 只分析关键帧 · 中文笔记 · 费曼 6/4/3 · 保留转写附录
- **时长校验**：音频时长 < 视频 80% 时告警
- **--job 批量**：通过 JSON 文件传入视频列表，规避命令行引号问题

## [0.0.x] - 2026-08-08

_首讲踩坑修复。_

### Fixed

- **音频缺失**：AAC 流损坏（330-563s 无法解码），手动分段拼接 0-330 + 600-771 后重新转写
- **ffmpeg AAC 报错**：返回非 0 但 wav 成功 → 改为检查 wav 是否生成而非 returncode
- **GBK 崩溃**：`run()` 用 UTF-8 读子进程输出（原默认 GBK 读中文崩溃）
- **断点续跑**：json/visual 存在则跳过（靠文件存在判断，不靠计数器）

已知限制：

- `MAX_FRAMES=6000` 对应每秒 2 帧 × 50 分钟，超长视频画面会截断（有 WARN 提示，可调大）
- 音频重建在每次损坏时都会重建（覆盖 rebuild.wav），断点场景下可接受但非最优
- 讲次标题映射目前只覆盖样本课程，其他课程需补充
