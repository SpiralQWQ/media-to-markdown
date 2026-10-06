# 验收报告 · media-to-markdown v1.0.0

> 验收日期：2026-10-06
> 验收对象：`media-to-markdown` 首个公开发布版（v1.0.0）
> 验收方式：对照【开源转正】通用提示词 v1.0 的硬门槛与加分项逐条核查，**每条附可复现的命令与输出**
> 报告语言：中文（项目工作语言；README 默认英文，双语并行）

---

## 一、验收范围

把一个"本地能跑"的个人工具，升级为可对外发布、他人可开箱即用的规范开源项目。验收覆盖：

| 维度 | 内容 |
|---|---|
| 代码结构 | 目录布局、入口、打包元数据、死代码 |
| 隐私安全 | 密钥、机器路径、内部项目名、第三方素材、git 历史 |
| 文档 | README（中英）、CHANGELOG、LICENSE、贡献指南、行为准则 |
| 工程质量 | 测试、CI、社区文件 |

---

## 二、硬门槛逐条核查

### 2.1 代码结构 ✅

| 要求 | 结果 | 证据 |
|---|---|---|
| 统一 `src/` 布局，消灭根目录散落脚本 | ✅ | 根目录只有文档与配置文件；全部源码在 `src/media_to_markdown/`；原根目录 `cli.py` 已收进包内 |
| 统一 `python -m {包名}` 入口 | ✅ | `python -m media_to_markdown --version` → `media-to-markdown 1.0.0`（退出码 0） |
| `pyproject.toml` 齐全（版本号/依赖/协议/作者） | ✅ | 含 name / dynamic version（单一事实源）/ requires-python / license / authors / dependencies / optional-dependencies / console script / package-dir |
| 删除死代码 | ✅ | 移除 2 个无调用方函数（`probe_duration`、`ask_course_classification`，共 71 行）、2 个未使用 import、1 处形同虚设的条件分支、1 个死配置键组；复核：重复定义 0、未使用 import 0 |

### 2.2 隐私安全 ✅

| 要求 | 结果 | 证据 |
|---|---|---|
| 密钥 / Token 改环境变量 | ✅ | `GLM_API_KEY` / `ASR_PY` / `OCR_PY` 全部走环境变量或 `.env`；引擎解释器默认当前解释器，不再指向某台机器 |
| 机器绝对路径清零 | ✅ | 全库扫描 `C:\` / `E:\` / `/home/` 形态路径：**0 命中** |
| 密钥在日志/文档中打码 | ✅ | 全库无任何打印密钥的代码；示例文件均为占位符（如 `GLM_API_KEY=your-key`） |
| 私有数据不进仓库 | ✅ | 转写产物目录、密钥文件、运行时配置均已排除；`.gitignore` 覆盖 `output/`、`.env`、本机配置 |
| git 历史排查 + 清理 | ✅ **无需执行** | 本仓在验收时为**零提交**（`git log` → `your current branch 'master' does not have any commits yet`），不存在需要 filter-branch 的历史 |
| 第三方素材 | ✅ | 测试样例全部为合成内容；原先携带的第三方视频截图与衍生文本素材已全部替换 |

**隐私扫描规则**（工作区 + 若存在的全部历史一起扫）：Windows/Unix 绝对路径、`API_KEY/AUTH_TOKEN/SECRET/PASSWORD` 赋值、32 位十六进制形式的密钥、邮箱、内部项目名。
**扫描结果：0 命中。**

### 2.3 文档 ✅

| 要求 | 结果 | 证据 |
|---|---|---|
| README 中英双语，含徽章/特性/安装/使用/配置/FAQ/Roadmap | ✅ | `README.md`（英文，默认）+ `README_zh.md`；章节含徽章行、What It Does、Why、Installation、**Configuration**、Usage、Output Layout、Architecture、File Tree、Testing、**Roadmap**、FAQ、Legal/Disclaimer、License、打赏码 |
| CHANGELOG 用 Keep a Changelog 格式 | ✅ | 两份 CHANGELOG 均为 `## [x.y.z] - 日期` + Added/Changed/Deprecated/Removed/Fixed/Security 六类小节；**26 个版本**（历史 25 个 + v1.0.0），中英版本链一一对应 |
| LICENSE | ✅ | AGPL-3.0 全文 + 双授权声明 |
| CONTRIBUTING.md | ✅ | 含开发环境搭建、分层约定、测试要求、提交规范、代码风格 |
| CODE_OF_CONDUCT.md | ✅ | Contributor Covenant v2.1（中英对照） |

---

## 三、加分项核查

| 项 | 结果 | 证据 |
|---|---|---|
| pytest 单元测试 | ✅ | **125 个用例全部通过**（`python -m pytest tests -q`） |
| GitHub Actions 自动跑测试 | ✅ | `.github/workflows/ci.yml`：Linux / Windows / macOS × Python 3.10 / 3.11 / 3.12，三步门禁——语法检查（`compileall`，可拦住只在 3.12+ 才合法的写法）、单元测试、入口点冒烟 |
| lint | 🔸 部分 | 以 `compileall` 作为语法层门禁；未引入独立 linter（避免在首次发布就引入风格争议），列为后续可选改进 |
| Git tag 版本号 | ⬜ 待首推时执行 | 计划打 `v1.0.0` |
| GitHub Release | ⬜ 待首推时执行 | — |
| PyPI 发布（可选） | ⬜ 未决策 | 待所有者决定 |
| issue / PR 模板 | ✅ | `.github/ISSUE_TEMPLATE/` 两个模板 + `PULL_REQUEST_TEMPLATE.md`（含自检清单） |
| SECURITY.md | ✅ | 含受支持版本、私密漏洞上报路径、安全须知（本工具只读本地文件、不外传） |

---

## 四、发布前审计发现并修复的问题

发布前对全部源码做了一轮逐文件审计（覆盖 core / engines / clean / assemble / cli / configs / tests / 文档），并对高危项做了对抗式复核。归并后修复的问题：

### 4.1 会静默损坏内容的

| 问题 | 后果 | 处置 |
|---|---|---|
| 清洗词表把「知识点」当作水印词 | 学习素材里最常见的词之一，**在误删正文** | 摘除并加回归测试（断言反转为"不得被误删"） |
| 段落清洗只认 ASCII 字母/数字与中日汉字 | 俄文、韩文、阿拉伯文、全角字母**整行静默消失** | 改用 Unicode 感知判断 |
| 交错组装的时间戳只认两位分钟数 | **≥100 分钟的视频结尾画面全部丢失** | 支持 1–3 位分钟 |
| 英文大小写归一无边界保护 | 改写更长单词内部（`MyPOWERSHELLish` → `MyPOWERSHELLish` 被改坏） | 增加拉丁字母前后向环视 |

### 4.2 会导致挂起或崩溃的

| 问题 | 后果 | 处置 |
|---|---|---|
| GLM 重试无上限 | 密钥缺失时**整批任务永久卡死** | 上限 3 次，超限退化为纯 OCR |
| 转写 JSON 中 `segments` 显式为 `null` | 清洗直接崩溃 | 安全兜底 |
| 时间戳非数字 | 组装直接崩溃 | 安全跳过 |

### 4.3 会误导使用者的

| 问题 | 后果 | 处置 |
|---|---|---|
| 命令行工具恒返回 0 | 全部失败也报成功，**脚本与 CI 无法感知** | 统计失败数，有失败即返回非 0 |
| 缺少 ffmpeg 时报裸异常 | 用户无从下手 | 抛出带安装指引的错误 |
| 抽帧上限警告 | 长视频抽全了仍**误报"画面被截断"** | 只在真的截断时打印 |

### 4.4 配置与文档一致性

| 问题 | 后果 | 处置 |
|---|---|---|
| 向导保存的 GLM 密钥与引擎读取位置不一致 | 向导刚验证通过的密钥，引擎**永远找不到** | 统一到运行时目录的同一份 `.env` |
| 向导提问的一半设置无人消费 | 用户以为调了参数，实际**没有任何效果** | 该接的接（抽帧间隔、抽帧方式、产物目录、中间文件处理），该删的删（笔记命名/课程名/说话人/批量模式等已随"生成笔记"环节废弃的概念） |
| 文档描述与代码不符 | README 声明的能力与实际不符 | 逐条核对修正（含测试数量、命令写法、链接目标） |

---

## 五、可复现的验证命令

```bash
# 1. 单元测试
python -m pytest tests -q                 # 125 passed

# 2. 入口点
python -m media_to_markdown --version     # media-to-markdown 1.0.0

# 3. 轻量环境下的测试（模拟 CI：不含语音引擎依赖）
#    语音引擎为延迟导入，故无 PyTorch 时全部用例仍应通过
python -m pytest tests -q                 # 125 passed

# 4. 语法门禁
python -m compileall -q src

# 5. 隐私扫描（绝对路径 / 密钥 / 内部名）
#    见内部过程报告中的扫描脚本；工作区与历史均 0 命中
```

---

## 六、已知限制与取舍

1. **语音引擎依赖较重**：FunASR + PyTorch 约 2GB，已拆为可选依赖组 `.[asr]`；只做画面 OCR 的用户无需安装。测试套件同样不依赖它（引擎为延迟导入）。
2. **抽帧默认仍为固定间隔**：新暴露的"画面变化才抽帧"为可选项，默认保持与历史行为一致，避免发布时改变既有输出密度。
3. **清洗规则面向中文素材**：噪声词表与标点为中文 ASR/OCR 场景调校；非中文素材未经调优，已写入 README 与路线图。
4. **本次未发布的能力**：原工具中为某条私有笔记流水线服务的脚本未纳入本仓（它们依赖另一个独立项目，无法单独运行），已在 CHANGELOG 的 v1.0.0 中以 Removed 明确记录。
5. **未引入独立 linter**：以语法门禁替代，避免首次发布即引入风格争议；列为后续改进项。

---

## 七、结论

**通过。**

三条硬门槛（代码结构 / 隐私安全 / 文档）全部达成；加分项中测试与 CI、社区文件已具备，版本标签与 Release 待首次推送时一并执行。

本报告所列结论均可由第五节命令复现。
