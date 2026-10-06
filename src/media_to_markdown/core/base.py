#!/usr/bin/env python3
"""core/base.py — 视频/图片/音频链路的公共骨架（被各模态 core 复用）。

只做「编排」：定义提取→清洗→组装的模板、统一路径解析、引擎解释器默认值。
具体引擎实现来自 engines/，清洗来自 clean/，组装来自 assemble/——本模块不直接含引擎逻辑。
"""
from __future__ import annotations

import os
import sys

# 引擎解释器：默认用当前解释器——把 FunASR / RapidOCR 装进同一环境即可开箱即用。
# 若把两个引擎放在各自的虚拟环境里，用环境变量 ASR_PY / OCR_PY 指向对应的 python 可执行文件。
ASR_PY = os.environ.get("ASR_PY") or sys.executable
OCR_PY = os.environ.get("OCR_PY") or sys.executable

VIDEO_EXTS = (".mp4", ".webm", ".mkv", ".mov", ".flv", ".avi")
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp")
AUDIO_EXTS = (".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".wma")


def write_text(path: str, text: str) -> None:
    """UTF-8 写文本（父目录自动建）。"""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def human_size(nbytes: int) -> str:
    mb = nbytes / 1048576
    return f"{mb:.1f}M" if mb >= 1 else f"{int(nbytes / 1024)}K"