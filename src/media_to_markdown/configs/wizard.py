#!/usr/bin/env python3
"""转写配置向导（交互式，产品经理风格）—— 每个问题讲清"干嘛的/选错会怎样/默认是啥"。

设计原则：
- 开箱即用：纯问答，每项有默认值，直接回车就用默认的
- 记忆设置：问过一次就记住，下次沿用（可中途改）
- 按类型问：视频 / 图集 / 音频 各自只问相关项

用法:
  from media_to_markdown.configs.wizard import run_wizard, load_config, save_config, DEFAULT_CONFIG

返回配置 dict（即 DEFAULT_CONFIG 的当前值）:
{
  "interval": 1.0,                # 视频抽帧间隔(秒)
  "smart_frame": False,           # False=固定间隔抽帧(默认) / True=画面变化才抽帧
  "glm": "yes|no",                # 是否让 AI 看懂画面/图片
  "notes_root": "",               # 产物根目录：空=当前工作目录
  "cleanup": "keep|slim|clean",   # 中间文件：保留 / 只删音频 / 全部清理
  "image_mode": "album|separate", # 图集：合成一份 / 每张独立
  "glm_model": "flashx|flash",    # GLM 模型档位
  "glm_delay": 5.0,               # GLM 请求间隔(秒)
  "skip_folders": [],             # 遍历时跳过的文件夹
  "resume": "yes|no",             # 断点续传 / 全部重转
}
"""
import os
import sys

# Windows 控制台 UTF-8 输出（防 gbk 编码崩溃，尤其是 emoji/中文混合）
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 配置文件位置（本地，不进 git）。.env 用当前工作目录，与 engines/glm_vision.py 读的是同一份。
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "wizard.json")
ENV_FILE = os.path.join(os.getcwd(), ".env")

DEFAULT_CONFIG = {
    "interval": 1.0,           # 视频抽帧间隔(秒)
    "smart_frame": False,      # False=固定间隔抽帧(默认) / True=画面变化才抽帧(省帧)
    "glm": "yes",              # 是否让 AI 看懂画面/图片
    # 产物与中间文件
    "notes_root": "",          # 产物根目录：空=当前工作目录；自定义填路径
    "cleanup": "keep",         # 中间文件: keep保留 / slim只删音频 / clean全部清理
    # 图片/图集专属
    "image_mode": "album",     # album=合成一份图集md / separate=每张独立md
    "glm_model": "flashx",     # flashx=稳定版(推荐) / flash=免费版(限流)
    "glm_delay": 5.0,          # GLM 请求间隔(秒)；免费版建议≥5
    "skip_folders": [],        # 遍历时跳过的文件夹(逗号分隔输入)
    "resume": "yes",           # yes=断点续传(已有md跳过) / no=全部重转
}


def load_config() -> dict:
    """读取已保存的向导配置（无则返回默认）。"""
    if not os.path.exists(CONFIG_FILE):
        return dict(DEFAULT_CONFIG)
    try:
        import json
        with open(CONFIG_FILE, encoding="utf-8") as f:
            d = json.load(f)
        cfg = dict(DEFAULT_CONFIG)
        # 只保留当前仍存在的键：历史配置里已删除的键自动清掉，不再残留
        cfg.update({k: v for k, v in d.items() if isinstance(d, dict) and k in DEFAULT_CONFIG})
        return cfg
    except Exception:
        return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    """保存向导配置到本地（供批量模式沿用 / 下次默认）。"""
    try:
        import json
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _ask(question: str, options: dict, default_key: str) -> str:
    """产品经理风格提问。options: {key: (label, desc)}，default_key 为默认。
    用户输入 key（不区分大小写）或回车（用默认）。"""
    print(f"\n{question}")
    for k, (label, desc) in options.items():
        mark = "（默认）" if k == default_key else ""
        print(f"  {k}. {label} {mark} —— {desc}")
    while True:
        ans = input(f"请输入 [{default_key}]: ").strip().upper()  # 统一大写匹配（options key 均为大写）
        if not ans:
            return default_key
        if ans in options:
            return ans
        print(f"  [X] 请输入 {list(options.keys())} 中的一个（或直接回车用默认）")


def _ask_glm_config() -> None:
    """GLM 视觉理解 API 配置引导（多供应商预置，Key 打码存 .env）。"""
    print("\n【画面理解设置】—— 让 AI 看懂图，需要连接一个视觉 AI")
    # 已配置 → 显示详情 + 三选（用当前/换供应商/只换模型）
    if _glm_configured():
        cur = _glm_current()
        print("  当前配置：")
        print(f"    ▸ 供应商：{cur.get('provider', '未知')}")
        print(f"    ▸ 模型：{cur.get('model', '未知')}")
        print(f"    ▸ 接口：{cur.get('url', '未知')}")
        action = _ask(
            "  接下来怎么做？",
            {
                "A": ("用当前配置", "直接用现有供应商/模型，推荐"),
                "B": ("换供应商/模型", "重新配置地址+Key+模型"),
                "C": ("只换模型", "供应商/地址/Key 不变，只改模型名"),
            },
            default_key="A")
        if action == "A":
            print("  [OK] 使用当前配置")
            return
        if action == "C":
            _ask_only_model()
            return
        # action == "B" → 走完整重新配置
    _ask_full_config()


def _glm_current() -> dict:
    """读取当前 GLM 配置详情（provider/model/url），用于显示。"""
    info = {"provider": "智谱 GLM", "model": "glm-4.6v-flashx",
            "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions"}
    try:
        if os.path.exists(ENV_FILE):
            with open(ENV_FILE, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GLM_API_URL="):
                        info["url"] = line.split("=", 1)[1]
                    elif line.startswith("GLM_MODEL="):
                        info["model"] = line.split("=", 1)[1]
        # 从 URL 推断供应商名
        url = info["url"]
        if "bigmodel" in url:
            info["provider"] = "智谱 GLM"
        elif "dashscope" in url:
            info["provider"] = "阿里通义千问"
        elif "openai" in url:
            info["provider"] = "OpenAI"
        elif "baidu" in url or "qianfan" in url:
            info["provider"] = "百度文心"
    except OSError:
        pass
    return info


def _ask_full_config() -> None:
    """完整配置（换供应商/模型）：预置地址 + 自定义 + Key + 模型名 + 测试连接。"""
    print("  ① 供应商（默认：智谱 GLM，中文最好；也可选其他）")
    providers = {
        "glm": ("智谱 GLM", "https://open.bigmodel.cn/api/paas/v4/chat/completions", "glm-4.6v-flashx"),
        "qwen": ("阿里通义千问", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", "qwen-vl-max"),
        "openai": ("OpenAI", "https://api.openai.com/v1/chat/completions", "gpt-4o-mini"),
        "baidu": ("百度文心", "https://qianfan.baidubce.com/v2/chat/completions", "ernie-4.5-vl-8b"),
    }
    print("     默认：智谱 GLM（地址已预填）；也可选 qwen/openai/baidu 或自定义")
    provider_input = input("  供应商[glm/qwen/openai/baidu，回车=智谱，或填自定义地址]: ").strip().lower()
    if "http" in provider_input:
        # 用户直接填了自定义地址
        api_url = provider_input
        default_model = "glm-4.6v-flashx"
        provider_name = "自定义"
    elif provider_input in providers:
        provider_name, api_url, default_model = providers[provider_input]
    else:
        provider_name, api_url, default_model = providers["glm"]
    print(f"  接口地址：{api_url}")
    api_key = input(f"  ② API Key（粘贴密钥，输入时打码不显示明文）: ").strip()
    if not api_key:
        print("  [X] 未输入 API Key，画面理解将无法使用")
        return
    model = input(f"  ③ 模型名（回车用默认 {default_model}）: ").strip() or default_model
    print(f"  ④ 测试连接（模型: {model}）...")
    # 测试失败 → 循环重试（可重新填 Key/模型，或退出用默认）
    while True:
        result = _test_glm(api_url, api_key, model)
        if result == "ok":
            _save_glm(provider_name, api_url, api_key, model)
            print("  [OK] 连接成功，配置已保存（.env，之后不再问）")
            return
        # 分类提示
        if result == "key":
            print(f"  [X] API Key 无效（服务器拒绝 401/403），请检查密钥是否正确")
        elif result == "model":
            print(f"  [X] 模型名可能有误（{model}）——服务器返回 400/404，请确认该模型名存在")
        else:
            print(f"  [X] 网络连接失败，请检查网络或接口地址")
        retry = input("  重新填 Key/模型(A) 还是 退出(B)? [A]: ").strip().upper() or "A"
        if retry == "B":
            print("  已取消画面理解配置")
            return
        # 重填 Key 和模型
        api_key = input("  重填 API Key（回车保留原值）: ").strip() or api_key
        model = input(f"  重填模型名（回车保留 {model}）: ").strip() or model
        print(f"  再测试（模型: {model}）...")


def _ask_only_model() -> None:
    """只换模型：保留供应商/地址/Key，填新模型名 + 测试成功才保存。"""
    cur = _glm_current()
    print(f"  当前供应商：{cur['provider']}（地址/Key 不变）")
    model = input(f"  新模型名（当前: {cur['model']}，直接填新名）: ").strip()
    if not model:
        print("  [X] 未输入模型名，取消")
        return
    # 测试失败 → 循环重试（重填模型名，或退出）
    while True:
        print(f"  测试连接（模型: {model}）...")
        result = _test_glm(cur["url"], _glm_key(), model)
        if result == "ok":
            _save_glm(cur["provider"], cur["url"], _glm_key(), model)
            print("  [OK] 连接成功，模型已更新（.env）")
            return
        # 分类提示：只换模型时 Key 已配置，重点提示模型名
        if result == "key":
            print(f"  [X] 检测到 API Key 无效（401/403）——当前已配置的 Key 可能过期，需在'换供应商'里重填 Key")
        elif result == "model":
            print(f"  [X] 模型名可能有误（{model}）——服务器返回 400/404，请确认该模型名存在")
        else:
            print(f"  [X] 网络连接失败，请检查网络或接口地址")
        retry = input("  重填模型名(A) 还是 退出(B)? [A]: ").strip().upper() or "A"
        if retry == "B":
            print("  已取消，模型未更改")
            return
        model = input("  重填模型名: ").strip()
        if not model:
            print("  [X] 未输入模型名，取消")
            return


def _glm_key() -> str:
    """读取 GLM API Key。"""
    if os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GLM_API_KEY="):
                        return line.split("=", 1)[1].strip()
        except OSError:
            pass
    return os.environ.get("GLM_API_KEY", "")


def _save_glm(provider: str, api_url: str, api_key: str, model: str) -> None:
    """保存 GLM 配置到 .env。"""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.write(f"GLM_API_KEY={api_key}\n")
            f.write(f"GLM_API_URL={api_url}\n")
            f.write(f"GLM_MODEL={model}\n")
            f.write(f"GLM_PROVIDER={provider}\n")
    except OSError:
        pass


def _glm_configured() -> bool:
    """检查是否已配置 GLM（.env 存在且含 Key）。"""
    if os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, encoding="utf-8") as f:
                return "GLM_API_KEY=" in f.read()
        except OSError:
            return False
    return bool(os.environ.get("GLM_API_KEY"))


def _validate_root(root: str) -> bool:
    """校验存储根目录：存在且可写，或可创建。"""
    if not root:
        return False
    try:
        if os.path.exists(root):
            return os.access(root, os.W_OK) or os.access(os.path.dirname(root), os.W_OK)
        # 不存在 → 检查父级可创建
        parent = os.path.dirname(root.rstrip("\\/")) or root
        return os.path.exists(parent) and os.access(parent, os.W_OK)
    except Exception:
        return False


def _default_root() -> str:
    """默认存储根目录：当前工作目录。

    核心链路（core/video.py 等）写的是相对 CWD 的 output/cache/，
    这里保持同一口径，向导预览的路径才与实际产物位置一致。
    """
    return os.getcwd()


def _preview_storage(root: str) -> None:
    """显示存储根目录下的实际产物结构（含具体路径）。"""
    cache = os.path.join(root, "output", "cache")
    print(f"\n  存储根目录：{root}")
    print("  转写产物会写到：")
    print(f"    ▸ 视频：  {cache}/<视频名>/<视频名>_clean.md（同目录另有转写/画面等中间文件）")
    print(f"    ▸ 音频：  {cache}/音频/<音频名>_clean.md")
    print(f"    ▸ 图集：  {cache}/图片/<名称>_clean.md")
    print()


def _ask_storage_root(cfg: dict) -> None:
    """问题3：产物根目录。默认/自定义都显示具体路径预览 → 确认；N 打回重选。"""
    while True:
        dr = _default_root()
        root_choice = _ask(
            "【问题3】转写产物存哪里？选\"默认\"就放在当前工作目录下的 output/cache/；"
            "选\"自定义\"只需填最外层地址，内层自动建。",
            {
                "A": ("用默认目录（推荐）",
                      f"例子：产物写到 {os.path.join(dr, 'output', 'cache')}"),
                "B": ("自定义目录",
                      "例子：填 D:\\我的学习 → 产物写到 D:\\我的学习\\output\\cache\\"),
            },
            default_key="A")
        if root_choice == "A":
            # 默认也要显示具体地址，让用户亲眼确认默认位置在哪
            _preview_storage(_default_root())
            confirm = input("  确认用这个默认位置？(Y/N，或直接回车=确认): ").strip().upper()
            if confirm == "" or confirm == "Y":
                cfg["notes_root"] = ""
                return
            print("  已取消默认位置，请重新选择（默认/自定义）")
            continue
        # B 自定义：填路径 → 校验 → 预览 → 确认（N 回到重填）
        while True:
            custom_root = input("  请输入存储根目录（如 D:\\我的学习）: ").strip()
            if not custom_root:
                print("  [X] 未输入路径，回到选择")
                break
            # 校验路径合法性（存在或可创建）
            if not _validate_root(custom_root):
                print(f"  [X] 目录不可写/不可创建: {custom_root}")
                ok = input("  重新填(A) 还是 回到选择(B)? [A]: ").strip().upper() or "A"
                if ok == "B":
                    break
                continue
            # 立即显示完整结构预览（视觉感，含具体路径）
            _preview_storage(custom_root)
            confirm = input("  确认使用此目录？(Y/N，或直接回车=确认): ").strip().upper()
            if confirm == "" or confirm == "Y":
                cfg["notes_root"] = custom_root
                return
            # N → 回到重填（不丢已填，可重输）
            print("  已取消该路径，请重新输入（或直接回车用默认）")


def _ask_image_options(cfg: dict) -> None:
    """图片/图集专属多询问（Task-03 通用化）—— 合成vs独立 / GLM模型 / 请求间隔 / 断点 / 跳过。

    普通图集 → 合成一份；PDF 图片 → 每张独立 md（收进 images_notes/）。
    GLM 开启时才问模型+间隔；独立模式才问断点；跳过文件夹批量遍历时生效。
    """
    # ① 处理模式：合成一份（图集）vs 每张独立 md（PDF图片）
    img_mode = _ask(
        "【图片】这批图片怎么处理？",
        {
            "A": ("合成一份笔记（推荐）", "例子：整个图集整理成一篇 md，普通图集用这个"),
            "B": ("每张独立 md（PDF图片）", "例子：PDF 里的图 → 每张同名一个 md，收进 images_notes/，便于和 full.md 融合"),
        },
        default_key="A")
    cfg["image_mode"] = "album" if img_mode == "A" else "separate"

    # ② GLM 模型 + 请求间隔（仅开启 GLM 时问）
    if cfg.get("glm") == "yes":
        glm_model = _ask(
            "【图片】让 AI 看懂图片，用哪个版本？",
            {
                "A": ("flashx 稳定版（推荐）", "例子：速度快、限流少，适合正式转"),
                "B": ("flash 免费版", "例子：免费但有频率限制，要配慢速间隔，转得慢"),
            },
            default_key="A")
        cfg["glm_model"] = "flashx" if glm_model == "A" else "flash"
        hint = "（免费版建议 ≥5，否则容易触发限流）" if cfg["glm_model"] == "flash" else ""
        delay_input = input(f"  每张图之间隔几秒？(GLM 请求间隔，防限流，默认 5){hint} [5]: ").strip()
        try:
            delay_val = float(delay_input) if delay_input else 5.0
        except ValueError:
            delay_val = 5.0
        cfg["glm_delay"] = delay_val if delay_val > 0 else 5.0  # 防负数/0 传入下游
    else:
        cfg.setdefault("glm_model", "flashx")
        cfg.setdefault("glm_delay", 5.0)

    # ③ 断点续传 vs 全部重转（仅每张独立模式）
    if cfg["image_mode"] == "separate":
        resume = _ask(
            "【图片】已有 md 的图片，跳过还是重新转？",
            {
                "A": ("跳过已生成（推荐）", "例子：上次中断的，这次接着转没转完的，不重来"),
                "B": ("全部重新转", "例子：彻底重来，已生成的也覆盖"),
            },
            default_key="A")
        cfg["resume"] = "yes" if resume == "A" else "no"
    else:
        cfg.setdefault("resume", "yes")

    # ④ 跳过哪些问题文件夹（批量遍历多个文件夹时生效）
    skip_input = input(
        "  跳过哪些问题文件夹？(批量遍历时跳过，逗号分隔可多填，可留空): ").strip()
    cfg["skip_folders"] = [
        s.strip() for s in skip_input.replace("，", ",").split(",") if s.strip()]


def _test_glm(api_url: str, api_key: str, model: str = "glm-4.6v-flashx") -> str:
    """发一张 1x1 透明 PNG 测试 GLM 连接。model 参数指定模型名。
    返回错误码：'ok' 成功 / 'key' Key无效(401/403) / 'model' 模型名错(400/404) / 'network' 网络错误。
    """
    import base64
    import json
    import urllib.error
    import urllib.request
    # 1x1 透明 PNG（最小可用）
    png_b64 = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
               "/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==")
    body = {
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{png_b64}"}},
            {"type": "text", "text": "测试，请回复 OK"},
        ]}],
    }
    req = urllib.request.Request(
        api_url, data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return "ok" if resp.status == 200 else "network"
    except urllib.error.HTTPError as e:
        # 401/403 → Key 无效；400/404 → 模型名错（含 1301 内容过滤）
        if e.code in (401, 403):
            return "key"
        if e.code in (400, 404):
            return "model"
        return "network"
    except Exception:
        return "network"


def run_wizard(media_type: str = "video") -> dict:
    """运行配置向导。

    media_type ∈ {video, image, audio}：按类型只问相关项
    （视频问抽帧 + GLM；图集问 GLM 与图片选项；音频只问产物目录与中间文件处理）。
    """
    cfg = load_config()
    print("\n" + "=" * 50)
    print("【转写开始前的设置向导】")
    print("开始前，我们先花一分钟确认几个设置。每项都有默认值，")
    print("直接按回车就用默认的，不用每个都改。")
    print("=" * 50)

    # 问题1：视频画面怎么截图？（固定+智能结合）—— 仅视频
    if media_type == "video":
        interval_choice = _ask(
            "【问题1】视频画面怎么截图？为了看懂幻灯片和公式要截图，越密越细但越慢。",
            {
                "A": ("每 1 秒截 1 张（最细）", "例子：1小时课≈3600张图，代码/公式多也不漏"),
                "B": ("每 2 秒截 1 张", "例子：1小时课≈1800张图，普通课够用"),
                "C": ("每 5 秒截 1 张", "例子：1小时课≈720张图，画面基本不动最快"),
            },
            default_key="A")
        cfg["interval"] = {"A": 1.0, "B": 2.0, "C": 5.0}[interval_choice]

        frame_mode = _ask(
            "  抽帧方式：固定间隔，还是画面变化才抽？",
            {
                "A": ("固定间隔（默认）", "例子：每 N 秒必抽 1 张，页内小改动也不漏，但帧数多"),
                "B": ("画面变化才抽（省帧）", "例子：同一页停 10 秒只抽 1 张，快很多；页内小改动可能漏"),
            },
            default_key="A")
        cfg["smart_frame"] = (frame_mode == "B")

    # 问题2：让 AI 看懂画面（GLM 关键帧）—— 视频/图集（文案按类型）
    if media_type in ("video", "image"):
        glm_question = (
            "【问题2】要不要让 AI【看懂】每张图？OCR 能读出图上文字，看懂是理解图的内容"
            "（如'这是编辑距离的表格'）。花一点云端费用（每次几厘钱）。"
            if media_type == "image"
            else "【问题2】要不要让 AI【看懂】画面？截图只能读出文字；看懂是理解图的意思"
                 "（如'这是编辑距离的表格'）。花一点云端费用（每次几厘钱）。"
        )
        glm_choice = _ask(glm_question,
            {
                "A": ("开启（推荐）", "例子：截图里的表格，AI能解释'这是算编辑距离的'，笔记更深入"),
                "B": ("关闭", "例子：只记录截图上的文字，不解释图，省钱但笔记浅一些"),
            },
            default_key="A")
        cfg["glm"] = "yes" if glm_choice == "A" else "no"
        if cfg["glm"] == "yes":
            _ask_glm_config()

    # 【图片专属】合成vs独立 + GLM模型 + 请求间隔 + 断点续传 + 跳过文件夹
    if media_type == "image":
        _ask_image_options(cfg)

    # 问题3：转写产物存哪里（默认/自定义都显示具体路径预览 → 确认；N 打回重选）
    _ask_storage_root(cfg)

    # 问题4：中间产物怎么处理
    clean_choice = _ask(
        "【问题4】转写过程会生成一堆中间文件（音频、转写文字、画面文字），"
        "转写完后这些怎么处理？",
        {
            "A": ("保留（推荐）", "例子：音频+文字全留着，方便复查/重洗，占空间"),
            "B": ("精简（只删音频）", "例子：只删最大的音频文件，省空间但仍能复查"),
            "C": ("全部清理", "例子：只留清洗后的 md，最省空间，以后不能复查"),
        },
        default_key="A")
    cfg["cleanup"] = {"A": "keep", "B": "slim", "C": "clean"}[clean_choice]

    save_config(cfg)
    _print_summary(cfg, media_type)
    return cfg


def _print_summary(cfg: dict, media_type: str = "video") -> None:
    """向导收尾确认清单（按类型显示相关项）。"""
    cleanup_txt = {"keep": "保留中间文件", "slim": "只删音频",
                   "clean": "全部清理"}[cfg.get("cleanup", "keep")]
    root_txt = cfg.get("notes_root") or _default_root()
    print("\n[OK] 设置确认完毕，开始转写！")
    print(f"   • 产物目录：{root_txt}")
    if media_type == "video":
        frame_txt = f"每 {cfg['interval']:g} 秒 1 张" + ("（画面变化才抽）" if cfg["smart_frame"] else "")
        glm_txt = "开（GLM 关键帧）" if cfg["glm"] == "yes" else "关"
        print(f"   • 画面：{frame_txt}")
        print(f"   • 看懂画面：{glm_txt}")
    elif media_type == "image":
        glm_txt = "开（GLM 逐张看懂）" if cfg["glm"] == "yes" else "关"
        mode_txt = "合成一份图集" if cfg.get("image_mode", "album") == "album" else "每张独立 md"
        print(f"   • 图片处理：{mode_txt}")
        print(f"   • 看懂每张图：{glm_txt}")
        if cfg["glm"] == "yes":
            model_txt = "flashx 稳定版" if cfg.get("glm_model", "flashx") == "flashx" else "flash 免费版"
            print(f"   • GLM 模型：{model_txt} · 间隔 {cfg.get('glm_delay', 5.0):g} 秒")
        if cfg.get("image_mode") == "separate":
            resume_txt = "断点续传（跳过已有）" if cfg.get("resume", "yes") == "yes" else "全部重转"
            print(f"   • 断点：{resume_txt}")
        if cfg.get("skip_folders"):
            print(f"   • 跳过：{', '.join(cfg['skip_folders'])}")
    print(f"   • 中间文件：{cleanup_txt}")
    input("\n按回车开始...")


if __name__ == "__main__":
    import json
    cfg = run_wizard()
    print(json.dumps(cfg, ensure_ascii=False, indent=2))
