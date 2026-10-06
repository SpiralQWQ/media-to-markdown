#!/usr/bin/env python3
"""core/audio.py — 音频域链路编排：ASR→json→clean→timeline→半成品 md。

音频只有声音（json 转写），无画面。复用 engines/asr（subprocess）+ clean/transcript + assemble/timeline。
"""
from __future__ import annotations

import os
import subprocess
import sys

from media_to_markdown.clean import transcript
from media_to_markdown.assemble import timeline

_PKG_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
_ENGINES_DIR = os.path.join(_PKG_DIR, "engines")
ASR_PY = os.environ.get("ASR_PY") or sys.executable


def _run_live(cmd, timeout=7200, label=""):
    """实时打印子进程输出，返回 CompletedProcess。
    空解释器/解释器不存在 → 返回失败 CP 不崩溃；读线程版整段超时。"""
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


def process_audio(audio: str, out_root: str = "") -> dict:
    """音频 → 半成品 md。返回 {tjson, clean_json, clean_md, chars}。"""
    if not os.path.isfile(audio):
        return {"error": f"音频不存在: {audio}"}
    out_root = out_root or os.path.join("output", "cache", "音频")
    os.makedirs(out_root, exist_ok=True)
    stem = os.path.splitext(os.path.basename(audio))[0]
    tjson = os.path.join(out_root, f"{stem}.json")

    # ① ASR 转写 → json（断点：已存在则复用）
    if not (os.path.exists(tjson) and os.path.getsize(tjson) > 0):
        _run_live([ASR_PY, os.path.join(_ENGINES_DIR, "asr.py"), audio, tjson], label="ASR")

    # ② 清洗（json 保结构）
    cjson = transcript.clean_transcript_json(tjson) if os.path.exists(tjson) else ""

    # ③ 组装：按时间排 → md
    if not cjson:
        return {"error": "转写 json 缺失，无法组装", "tjson": tjson}
    md = timeline.assemble_timeline(cjson, title=stem)
    clean_md = os.path.join(out_root, f"{stem}_clean.md")
    with open(clean_md, "w", encoding="utf-8") as f:
        f.write(md)
    return {"tjson": tjson, "clean_json": cjson, "clean_md": clean_md, "chars": len(md)}