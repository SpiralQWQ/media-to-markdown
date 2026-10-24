#!/usr/bin/env python3
"""clean — 清洗层（纯文本，零外部依赖，被 core 单向调用）。

模块内只含纯文本清洗原语，不含任何引擎/IO 业务，保证可独立单测、可复用。
公共原语（标点规范化、段落清洗）放在本包 __init__，供 transcript/visual/plain 引用。
"""
from __future__ import annotations

import re

# 标点乱码规范化（ASR/OCR 转写常见）：,,→, / ..→. / ??→? / 中文标点压缩
_PUNCT_PAIRS = [
    (re.compile(r",{2,}"), ","),
    (re.compile(r"\.{2,}"), "."),
    (re.compile(r"\?{2,}"), "?"),
    (re.compile(r",\."), "."),
    (re.compile(r"\.,"), "."),
    (re.compile(r"。，"), "。"),
    (re.compile(r"，。"), "。"),
    (re.compile(r"。{2,}"), "。"),
    (re.compile(r"，{2,}"), "，"),
]

# 句首孤立标点：ASR 在「。」后断句，紧跟着的「，」就落到了下一句的开头。
# _PUNCT_PAIRS 全是两两配对，没有一条针对"串首"，而 .strip() 去的是空白不是标点，
# 于是句首那个逗号原样活下来，一路流进 markdown 时间轴。
# 只匹配串首连续的一段；句中与句尾的标点不归这里管。
_LEADING_PUNCT = re.compile(r"^[，。、；：？！,.;:?!…—]+")


def norm_punct(text: str) -> str:
    """标点乱码规范化。"""
    for rx, repl in _PUNCT_PAIRS:
        text = rx.sub(repl, text)
    return text.strip()


def strip_leading_punct(text: str) -> str:
    """去掉句首的孤立标点（上一句结尾被 ASR 断句切到了下一句开头）。"""
    return _LEADING_PUNCT.sub("", text, count=1)


def clean_segment(text) -> str:
    """单段/单句清洗：标点规范化 + 去句首孤立标点 + 空白规整 + 纯标点/纯空白段清空（返回空串）。"""
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    t = strip_leading_punct(norm_punct(text))
    t = re.sub(r"[ \t　]+", " ", t)
    t = t.strip()
    if not any(ch.isalnum() for ch in t):  # 纯标点/纯空白 → 清空（isalnum 走 Unicode，非中英文字符不再被误删）
        return ""
    return t