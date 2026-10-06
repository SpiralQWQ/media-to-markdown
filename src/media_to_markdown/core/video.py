#!/usr/bin/env python3
"""core/video.py — 视频域链路编排：extract(音频+画面)→clean→assemble→半成品 md。

组装顺序（单向依赖 core→{engines,clean,assemble}）：
  视频 → ffmpeg 提音频 → ASR→json
       → OCR(+坐标排序)→ visual.txt
       → 清洗(transcript + visual)
       → assemble.interleave → 半成品 md
返回产物路径 dict；引擎已有产物时跳过（断点），仅 clean+assemble 也可用。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

from media_to_markdown.clean import transcript
from media_to_markdown.clean import visual
from media_to_markdown.assemble import interleave
from media_to_markdown.engines import ffmpeg

_PKG_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
_ENGINES_DIR = os.path.join(_PKG_DIR, "engines")

# 引擎解释器：默认当前解释器；用 ASR_PY / OCR_PY 指定独立虚拟环境
ASR_PY = os.environ.get("ASR_PY") or sys.executable
OCR_PY = os.environ.get("OCR_PY") or sys.executable


def _run_live(cmd, timeout=3600, label=""):
    """实时打印子进程输出，返回 CompletedProcess。
    空解释器/解释器不存在（如 ASR_PY 被环境变量清空）→ 返回失败 CP 不崩溃；
    读线程版：timeout 约束整段运行（沉默进程也会被终止，readline 不会永阻塞）。"""
    if not cmd or not cmd[0] or not os.path.isfile(cmd[0]):
        print(f"  [{label}] 引擎未配置，跳过: {cmd[0] if cmd else cmd}")
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="engine not configured")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace")
    out_lines = []
    import threading

    def _pump():
        for line in proc.stdout:
            text = line.rstrip()
            out_lines.append(text)
            if text:
                print(f"  [{label}] {text}")

    reader = threading.Thread(target=_pump, daemon=True)
    reader.start()
    timed_out = False
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        proc.wait()
    reader.join(timeout=5)  # 排空剩余输出（daemon 线程不会卡住主线程）
    if timed_out:
        print(f"  [{label}] 超时终止")
    return subprocess.CompletedProcess(proc.args, proc.returncode,
                                       stdout="\n".join(out_lines), stderr="")


def _prog_path(out_root: str) -> str:
    return os.path.join(out_root, "_progress.json")


def _save_prog(out_root: str, **kw):
    """写进度文件，记录已完成的步骤。"""
    p = _prog_path(out_root)
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"steps": list(kw.keys())}, f, ensure_ascii=False)
    except OSError:
        pass  # 进度文件写失败不阻塞


def _load_prog(out_root: str) -> set:
    """读进度文件，返回已完成的步骤名集合。"""
    p = _prog_path(out_root)
    try:
        with open(p, "r", encoding="utf-8") as f:
            return set(json.load(f).get("steps", []))
    except (OSError, json.JSONDecodeError):
        return set()


def process_video(video: str, glm: str = "no", out_root: str = "",
                  interval: float = 1.0, smart_frame: bool = False) -> dict:
    """视频 → 半成品 md。返回 {tjson, vtxt, clean_json, clean_md, chars}。

    interval / smart_frame 直接透传给 OCR 引擎（固定间隔 / 画面变化才抽）。
    """
    if not os.path.isfile(video):
        return {"error": f"视频不存在: {video}"}
    stem = os.path.splitext(os.path.basename(video))[0]
    out_root = out_root or os.path.join("output", "cache", stem)
    os.makedirs(out_root, exist_ok=True)

    tjson = os.path.join(out_root, f"{stem}.json")
    vtxt = os.path.join(out_root, f"{stem}_visual.txt")

    # ① 提音频 → wav（缺则生成）
    wav = os.path.join(out_root, f"{stem}.wav")
    if not (os.path.exists(wav) and os.path.getsize(wav) > 0):
        ffmpeg.extract_audio(video, wav)

    # ② ASR 转写 → json（断点跳过）
    if os.path.exists(tjson) and os.path.getsize(tjson) > 0:
        pass
    else:
        _run_live([ASR_PY, os.path.join(_ENGINES_DIR, "asr.py"), wav, tjson], timeout=7200, label="ASR")

    # ③ 画面 OCR → visual（断点跳过）
    if not (os.path.exists(vtxt) and os.path.getsize(vtxt) > 0):
        _run_live([OCR_PY, os.path.join(_ENGINES_DIR, "ocr.py"), video,
              "--mode", "scene" if smart_frame else "fixed",
              "--interval", f"{interval:g}", "--glm", glm, "--out", vtxt],
              timeout=14400, label="OCR")

    # ④ 清洗（json 保结构 + 画面逐帧）— 检查是否已全部完成
    done = _load_prog(out_root)
    if "all_done" in done:
        clean_md = os.path.join(out_root, f"{stem}_clean.md")
        if os.path.isfile(clean_md):
            with open(clean_md, encoding="utf-8") as f:
                md = f.read()
            cjson = os.path.join(out_root, f"{stem}_clean.json")
            cvisual = os.path.join(out_root, f"{stem}_visual_clean.txt")
            return {"tjson": tjson, "vtxt": vtxt, "clean_json": cjson,
                    "clean_visual": cvisual, "clean_md": clean_md, "chars": len(md)}
    cjson = transcript.clean_transcript_json(tjson) if os.path.exists(tjson) else ""
    cvisual = visual.clean_visual_timeline(vtxt) if os.path.exists(vtxt) else ""

    # ⑤ 组装：时间交错 → 半成品 md
    if not cjson and not cvisual:
        return {"error": "转写 json 与画面 txt 均缺失，无法组装", "tjson": tjson, "vtxt": vtxt}
    md = interleave.assemble_interleaved(cjson, cvisual, title=stem)
    clean_md = os.path.join(out_root, f"{stem}_clean.md")
    with open(clean_md, "w", encoding="utf-8") as f:
        f.write(md)
    _save_prog(out_root, all_done=True)

    return {"tjson": tjson, "vtxt": vtxt, "clean_json": cjson,
            "clean_visual": cvisual, "clean_md": clean_md, "chars": len(md)}