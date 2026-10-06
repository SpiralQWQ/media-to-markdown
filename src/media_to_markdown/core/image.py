#!/usr/bin/env python3
"""core/image.py — 图片/图集域链路编排（对齐视频画面那套 OCR+GLM，仅无时间线）。

每张图都输出「【图片N】 + [画面文字 OCR] + [GLM画面理解]」两块（glm=yes 才有 GLM 块），
与视频帧的「帧标记 + OCR + GLM」同引擎、同质量；区别仅是无 [MM:SS] 时间戳（用图片编号代替）。
组装：assemble/album.py 图序罗列（无时间轴，不能交错）。
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

from media_to_markdown.clean import plain
from media_to_markdown.assemble import album
from media_to_markdown.engines import ocr

_ENGINES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "engines")


def _glm_describe(image: str) -> str:
    """子进程调 engines/glm_vision.py 看懂单图；失败返回空串（不阻塞）。"""
    prompt = "请描述这张图片的内容（主体/场景/图表/界面/文字信息），用于辅助制作学习笔记。简洁。"
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(_ENGINES_DIR, "glm_vision.py"),
             "--image", image, "--prompt", prompt],
            capture_output=True, timeout=180)
        return (r.stdout or "").decode("utf-8", errors="replace").strip()
    except Exception:
        return ""


def process_image(images: list, out_root: str = "", glm: str = "no") -> dict:
    """图片/图集 → 半成品 md（图序，对齐视频那套 OCR+GLM）。返回 {txt, clean_md, chars, images}。"""
    if not images:
        return {"error": "无图片输入"}
    out_root = out_root or os.path.join("output", "cache", "图片")
    os.makedirs(out_root, exist_ok=True)
    stem = os.path.splitext(os.path.basename(images[0]))[0]

    # ① OCR（必做，坐标排序）→ 每图文字
    texts = ocr.ocr_images_to_text(images)

    # ② 每图块：视频式「OCR 块 + GLM 块」，用【图片N】代替帧时间戳
    blocks = []
    for n, (p, t) in enumerate(zip(images, texts), 1):
        block = f"【图片{n}】"
        if t.strip():
            block += f"\n[画面文字 OCR]\n{t.strip()}"
        if glm == "yes":           # GLM 询问用户开/关（同视频：glm=yes 才看懂画面）
            try:
                d = _glm_describe(p)
            except Exception:
                d = ""
            if d:
                block += f"\n[GLM画面理解]\n{d}"
        blocks.append(block)
    txt = "\n\n".join(b for b in blocks if b)

    # ③ 清洗（与视频同规：去水印/标签独立行，保留图片序号与内容）
    cleaned = plain.clean_plain_text(txt)

    # ④ 组装 → 图序 md
    md = album.assemble_album(cleaned, title=stem)
    txt_path = os.path.join(out_root, f"{stem}_ocr.txt")
    clean_md = os.path.join(out_root, f"{stem}_clean.md")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(txt)
    with open(clean_md, "w", encoding="utf-8") as f:
        f.write(md)
    return {"txt": txt_path, "clean_md": clean_md, "chars": len(md), "images": len(images)}


_IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")

# GLM 单图最多尝试次数：失败到上限就退回纯 OCR，绝不无限重试卡死整批
_GLM_MAX_ATTEMPTS = 3


def _glm_describe_en(image: str, prompt: str, model: str = "") -> str:
    """Subprocess GLM vision; empty on failure (caller retries).
    model 非空时用其覆盖 GLM_MODEL（向导选 flashx/flash 时生效）。"""
    try:
        env = dict(os.environ)
        if model:
            env["GLM_MODEL"] = model
        r = subprocess.run(
            [sys.executable, os.path.join(_ENGINES_DIR, "glm_vision.py"),
             "--image", image, "--prompt", prompt],
            capture_output=True, timeout=300, env=env)
        return (r.stdout or "").decode("utf-8", errors="replace").strip()
    except Exception:
        return ""


def process_images_to_mds(images_dir: str, out_dir: str = "",
                          glm: str = "yes", delay: float = 5.0,
                          retry_delay: float = 30.0,
                          model: str = "", resume: str = "yes") -> dict:
    """Image folder -> one independent md per image (for PDF-derived images).

    Each image: OCR + optional GLM; md name = original name (.md).
    Output collected into <out_dir>/ (default: sibling images_notes/).
    Resume: existing md skipped (resume='no' -> redo all, keep raw md too).
    GLM retried up to _GLM_MAX_ATTEMPTS times per image, spaced by delay seconds;
    after that the image is written OCR-only rather than blocking the batch.
    model: GLM model override (e.g. 'glm-4.6v-flash' for free tier).
    Returns {done, skipped, total, out}.
    """
    if not os.path.isdir(images_dir):
        return {"error": f"images dir not found: {images_dir}"}
    imgs = sorted(f for f in os.listdir(images_dir) if f.lower().endswith(_IMG_EXTS))
    if not imgs:
        return {"error": f"no images in: {images_dir}"}
    out_dir = out_dir or os.path.join(os.path.dirname(os.path.abspath(images_dir)), "images_notes")
    os.makedirs(out_dir, exist_ok=True)

    ocr_engine = ocr.make_ocr()
    prompt = ("Describe this image (subject/scene/chart/UI/code/text) concisely "
              "in Chinese, to help make study notes.")
    done = skipped = 0
    seen_stems = set()
    for fn in imgs:
        stem = os.path.splitext(fn)[0]
        md_path = os.path.join(out_dir, f"{stem}.md")
        if stem in seen_stems:
            print(f"[warn] duplicate stem {fn} -> {stem}.md, skip to avoid overwrite")
            skipped += 1
            continue
        seen_stems.add(stem)
        if resume != "no" and os.path.exists(md_path) and os.path.getsize(md_path) > 0:
            skipped += 1
            continue  # resume: already done
        img_path = os.path.join(images_dir, fn)
        text = ocr.ocr_image_to_text(img_path, ocr_engine).strip()
        text = plain.clean_plain_text(text)  # 清洗（去水印/标签/标点规整）
        parts = [f"# {stem}", "", "## 图片内容（OCR）", "", text or "（无文字）"]
        if glm == "yes":
            desc = ""
            for attempt in range(1, _GLM_MAX_ATTEMPTS + 1):
                print(f"[glm] {fn} (attempt {attempt}/{_GLM_MAX_ATTEMPTS}, delay {delay}s)")
                desc = _glm_describe_en(img_path, prompt, model)
                if desc:
                    break
                if attempt < _GLM_MAX_ATTEMPTS:
                    print(f"[glm] {fn} not ready, wait {retry_delay}s and retry")
                    time.sleep(retry_delay)
            if desc:
                parts += ["", "## GLM 画面理解", "", desc]
            else:
                print(f"[glm] {fn} failed after {_GLM_MAX_ATTEMPTS} attempts -> writing OCR-only")
            if delay > 0:
                time.sleep(delay)  # 限流：两次 GLM 请求间隔（免费版防 429）
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(parts))
        done += 1
    return {"done": done, "skipped": skipped, "total": len(imgs), "out": out_dir}