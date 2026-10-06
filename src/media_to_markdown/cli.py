#!/usr/bin/env python3
"""cli.py — 薄入口：按输入类型路由到 core 各模态域（视频/图片/音频）。

只做「判断路径类型 → 调 core」；本身不含业务逻辑，保持入口薄、防呆完整。
用法（包安装后）:
  python -m media_to_markdown "<视频.mp4>" [--glm yes|no]   # 视频 → 半成品 md
  python -m media_to_markdown "<图片.jpg> [图2...]"         # 图集 → 一份 md（逐张 OCR，可 --glm）
  python -m media_to_markdown "<音频.wav>"                  # 音频 → md（ASR 转写）
  python -m media_to_markdown --version
"""
from __future__ import annotations

import os
import sys

from media_to_markdown import __version__
from media_to_markdown.core import base


def _classify(path: str):
    if not path:
        return None
    low = path.lower()
    if low.endswith(base.VIDEO_EXTS):
        return "video"
    if low.endswith(base.IMAGE_EXTS):
        return "image"
    if low.endswith(base.AUDIO_EXTS):
        return "audio"
    return None


# 向导 glm_model 选择键 → GLM 完整模型名（图片逐张理解用）
_GLM_MODEL_NAMES = {"flashx": "glm-4.6v-flashx", "flash": "glm-4.6v-flash"}


def _out_root(cfg: dict, name: str) -> str:
    """按向导的产物根目录拼出该项的输出目录。

    未设根目录时返回空串，由 core 使用自己的默认（当前工作目录下的 output/cache）。
    """
    root = (cfg or {}).get("notes_root") or ""
    if not root:
        return ""
    return os.path.join(root, "output", "cache", name)


def _apply_cleanup(policy: str, clean_md: str) -> None:
    """按向导选择处理中间文件。

    keep  不动；slim  只删音频（体积最大）；clean 只留清洗后的产物（md + clean json）。
    """
    if policy not in ("slim", "clean") or not clean_md:
        return
    folder = os.path.dirname(os.path.abspath(clean_md))
    if not os.path.isdir(folder):
        return
    for fn in os.listdir(folder):
        path = os.path.join(folder, fn)
        if not os.path.isfile(path):
            continue
        if policy == "slim":
            if fn.lower().endswith(".wav"):
                os.remove(path)
        elif not (fn.endswith("_clean.md") or fn.endswith("_clean.json")):
            os.remove(path)


def _wizard_cfg(kind: str) -> dict:
    """按媒体类型弹对应向导（run_wizard(media_type=kind)），返回配置。失败返回 {}。"""
    try:
        import importlib.util as u
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs", "wizard.py")
        spec = u.spec_from_file_location("_w", p)
        w = u.module_from_spec(spec)
        spec.loader.exec_module(w)
        return w.run_wizard(media_type=kind)
    except Exception as e:
        print(f"[WARN] 向导未完成，用默认: {type(e).__name__}: {e}")
        return {}


def main(argv=None):
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        sys.exit('用法: python -m media_to_markdown "<视频/图片/音频路径>" [--glm yes|no]')

    glm = "no"
    wizard_flag = False
    paths = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--glm" and i + 1 < len(args):
            glm = args[i + 1]
            i += 2
            continue
        if a == "--wizard":
            wizard_flag = True
            i += 1
            continue
        if a in ("--version", "-V"):
            print(f"media-to-markdown {__version__}")
            return 0
        if a.startswith("--"):
            i += 1
            continue
        paths.append(a)
        i += 1

    if not paths:
        sys.exit('用法: 缺少输入路径')

    # 分类收集：视频/音频各为独立 md；图片文件=一份图集，图片文件夹=每张独立 md
    videos, images, audios, image_dirs = [], [], [], []
    ok_count = fail_count = 0
    for p in paths:
        if not os.path.exists(p):
            print(f"错误: 路径不存在: {p}")
            fail_count += 1
            continue
        if os.path.isdir(p):
            try:
                names = os.listdir(p)
            except OSError as e:
                print(f"错误: 无法读取目录 {p}: {e}")
                fail_count += 1
                continue
            if any(f.lower().endswith(base.IMAGE_EXTS) for f in names):
                image_dirs.append(p)   # 图片文件夹 → 每张独立 md
            else:
                print(f"错误: 目录内没有图片: {p}")
                fail_count += 1
            continue
        kind = _classify(p)
        if kind is None:
            print(f"错误: 不支持的扩展名: {p}")
            fail_count += 1
            continue
        if kind == "video":
            videos.append(p)
        elif kind == "image":
            images.append(p)
        elif kind == "audio":
            audios.append(p)

    v_total = len(videos)
    for idx, p in enumerate(videos, 1):
        try:
            print(f"\n[{idx}/{v_total}] 开始处理视频: {os.path.basename(p)}")
            cfg = _wizard_cfg("video") if wizard_flag else {}
            g = cfg.get("glm", glm) if cfg else glm
            from media_to_markdown.core import video
            stem = os.path.splitext(os.path.basename(p))[0]
            r = video.process_video(p, glm=g, out_root=_out_root(cfg, stem),
                                    interval=float(cfg.get("interval", 1.0) or 1.0),
                                    smart_frame=bool(cfg.get("smart_frame", False)))
            if "error" in r:
                print(f"[{idx}/{v_total}] 错误: {r['error']}")
                fail_count += 1
            else:
                print(f"[{idx}/{v_total}] 视频完成: {r.get('clean_md')} ({r.get('chars')} 字符)")
                _apply_cleanup(cfg.get("cleanup", "keep"), r.get("clean_md", ""))
                ok_count += 1
        except Exception as e:
            print(f"[{idx}/{v_total}] 处理失败 {p}: {type(e).__name__}: {e}")
            fail_count += 1

    a_total = len(audios)
    for idx, p in enumerate(audios, 1):
        try:
            print(f"\n[{idx}/{a_total}] 开始处理音频: {os.path.basename(p)}")
            cfg = _wizard_cfg("audio") if wizard_flag else {}
            from media_to_markdown.core import audio
            r = audio.process_audio(p, out_root=_out_root(cfg, "音频"))
            if "error" in r:
                print(f"[{idx}/{a_total}] 错误: {r['error']}")
                fail_count += 1
            else:
                print(f"[{idx}/{a_total}] 音频完成: {r.get('clean_md')} ({r.get('chars')} 字符)")
                _apply_cleanup(cfg.get("cleanup", "keep"), r.get("clean_md", ""))
                ok_count += 1
        except Exception as e:
            print(f"[{idx}/{a_total}] 处理失败 {p}: {type(e).__name__}: {e}")
            fail_count += 1

    if images:
        try:
            cfg = _wizard_cfg("image") if wizard_flag else {}
            g = cfg.get("glm", glm) if cfg else glm
            from media_to_markdown.core import image
            r = image.process_image(images, glm=g, out_root=_out_root(cfg, "图片"))   # 多图合成一份图集 md
            if "error" in r:
                print(f"错误: {r['error']}")
                fail_count += 1
            else:
                print(f"图集完成: {r.get('clean_md')} ({r.get('chars')} 字符, {r.get('images')} 张)")
                _apply_cleanup(cfg.get("cleanup", "keep"), r.get("clean_md", ""))
                ok_count += 1
        except Exception as e:
            print(f"图集处理失败: {type(e).__name__}: {e}")
            fail_count += 1

    # 图片文件夹：向导选 album 则合成一份，否则每张独立 md
    for idx, d in enumerate(image_dirs, 1):
        try:
            print(f"\n[{idx}/{len(image_dirs)}] 图片文件夹: {os.path.basename(d)}")
            cfg = _wizard_cfg("image") if wizard_flag else {}
            g = cfg.get("glm", glm) if cfg else glm
            from media_to_markdown.core import image
            if cfg and cfg.get("image_mode") == "album":
                # 向导选了合成一份 → 目录内图片合成一份图集 md
                files = [os.path.join(d, f) for f in sorted(os.listdir(d))
                         if f.lower().endswith(base.IMAGE_EXTS)]
                r = image.process_image(files, glm=g, out_root=_out_root(cfg, os.path.basename(d)))
                if "error" in r:
                    print(f"[{idx}/{len(image_dirs)}] 错误: {r['error']}")
                    fail_count += 1
                else:
                    print(f"[{idx}/{len(image_dirs)}] 图集完成: {r.get('clean_md')} ({r.get('chars')} 字符, {r.get('images')} 张)")
                    _apply_cleanup(cfg.get("cleanup", "keep"), r.get("clean_md", ""))
                    ok_count += 1
            else:
                # 每张独立 md（默认）：收进源同级 images_notes/
                model = (_GLM_MODEL_NAMES.get(cfg.get("glm_model", "")) or "") if cfg else ""
                delay = float(cfg.get("glm_delay", 5.0)) if cfg else 5.0
                resume = cfg.get("resume", "yes") if cfg else "yes"
                # 每张图独立成 md；未设根目录时用引擎默认（源目录同级 images_notes/）
                r = image.process_images_to_mds(
                    d, out_dir=_out_root(cfg, os.path.join("images_notes", os.path.basename(d))),
                    glm=g, delay=delay, model=model, resume=resume)
                if "error" in r:
                    print(f"[{idx}/{len(image_dirs)}] 错误: {r['error']}")
                    fail_count += 1
                else:
                    print(f"[{idx}/{len(image_dirs)}] 完成: 新增 {r['done']} / 跳过 {r['skipped']} / 共 {r['total']} 张 → {r['out']}")
                    ok_count += 1
        except Exception as e:
            print(f"[{idx}/{len(image_dirs)}] 图片文件夹处理失败 {d}: {type(e).__name__}: {e}")
            fail_count += 1

    # 退出码：有任何一项失败就返回非 0，脚本/CI 才能感知
    if fail_count:
        print(f"\n完成：成功 {ok_count} 项，失败 {fail_count} 项。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())