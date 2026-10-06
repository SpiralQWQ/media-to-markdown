# -*- coding: utf-8 -*-
"""Robustness regression tests for the issues found in the 1.0.0 pre-release audit.

Each test locks one behaviour that used to be wrong (or crash) before the fix.
"""
import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

from media_to_markdown.clean import clean_segment
from media_to_markdown.clean.transcript import clean_transcript_json
from media_to_markdown.assemble.interleave import assemble_interleaved
from media_to_markdown.engines.asr import _normalize_english_case
from media_to_markdown.core.image import process_images_to_mds


class TestCleanSegmentUnicode(unittest.TestCase):
    """clean_segment used to empty any line without an ASCII alnum or a CJK ideograph."""

    def test_keeps_other_scripts(self):
        for s in ["Привет мир", "안녕하세요", "café münchen", "ＡＢＣ１２３", "مرحبا"]:
            self.assertEqual(clean_segment(s), s, "被误删: %r" % s)

    def test_still_drops_punctuation_only(self):
        for s in ["。。。", ",,,", "   ", "★☆", "", None]:
            self.assertEqual(clean_segment(s), "", "应清空: %r" % s)


class TestTranscriptNullCollections(unittest.TestCase):
    """A transcript json with "segments": null used to raise TypeError on len(None)."""

    def test_null_segments_and_sentences(self):
        d = tempfile.mkdtemp(prefix="m2m_null_")
        try:
            p = os.path.join(d, "t.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump({"text": "x", "segments": None, "sentences": None}, f)
            out = clean_transcript_json(p)
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["segments"], [])
            self.assertEqual(data["sentences"], [])
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestInterleaveLongVideo(unittest.TestCase):
    """Frames past the 99-minute mark were silently dropped by a 2-digit regex."""

    def test_frame_beyond_100_minutes_is_kept(self):
        d = tempfile.mkdtemp(prefix="m2m_long_")
        try:
            cj = os.path.join(d, "c.json")
            with open(cj, "w", encoding="utf-8") as f:
                json.dump({"sentences": [{"text": "开场", "start_ms": 0, "end_ms": 1000}]}, f)
            vf = os.path.join(d, "v.txt")
            with open(vf, "w", encoding="utf-8") as f:
                f.write("[100:05]\n后半段画面\n\n[00:00]\n开场画面")
            md = assemble_interleaved(cj, vf, title="长视频")
            self.assertIn("后半段画面", md, "≥100 分钟的画面帧被丢弃")
            self.assertIn("开场画面", md)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_non_numeric_timestamp_does_not_crash(self):
        d = tempfile.mkdtemp(prefix="m2m_dirty_")
        try:
            cj = os.path.join(d, "c.json")
            with open(cj, "w", encoding="utf-8") as f:
                json.dump({"sentences": [{"text": "脏数据", "start_ms": "abc"}]}, f)
            md = assemble_interleaved(cj, "", title="t")
            self.assertIn("脏数据", md)
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestEnglishCaseBoundary(unittest.TestCase):
    """The case normaliser replaced its target inside longer English words."""

    def test_does_not_touch_inside_a_longer_word(self):
        # 大小写变体嵌在更长的英文词里：旧实现会把 "MyPOWERSHELLish" 改成 "MyPowerShellish"
        corr = {"x": "PowerShell"}
        self.assertEqual(_normalize_english_case("MyPOWERSHELLish thing", corr),
                         "MyPOWERSHELLish thing")

    def test_still_normalises_next_to_chinese(self):
        corr = {"x": "PowerShell"}
        self.assertEqual(_normalize_english_case("用Powershell写脚本", corr),
                         "用PowerShell写脚本")


class TestGlmAttemptCap(unittest.TestCase):
    """GLM retried forever when the key was missing, hanging the whole batch."""

    def test_gives_up_and_writes_ocr_only(self):
        d = tempfile.mkdtemp(prefix="m2m_glm_")
        try:
            img = os.path.join(d, "a.png")
            with open(img, "wb") as f:
                f.write(b"\x89PNG\r\n\x1a\n")
            out = os.path.join(d, "out")
            with mock.patch("media_to_markdown.core.image.ocr.make_ocr", return_value=None), \
                 mock.patch("media_to_markdown.core.image.ocr.ocr_image_to_text", return_value="hello"), \
                 mock.patch("media_to_markdown.core.image._glm_describe_en", return_value="") as m:
                r = process_images_to_mds(d, out_dir=out, glm="yes", delay=0.0, retry_delay=0.0)
            self.assertEqual(r.get("done"), 1)
            self.assertEqual(m.call_count, 3, "GLM 重试次数应有上限")
            with open(os.path.join(out, "a.md"), encoding="utf-8") as f:
                self.assertIn("hello", f.read())
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestCliExitCode(unittest.TestCase):
    """The CLI exited 0 even when every input failed."""

    def test_version_returns_zero(self):
        from media_to_markdown import cli
        self.assertEqual(cli.main(["--version"]), 0)

    def test_all_inputs_failing_returns_nonzero(self):
        from media_to_markdown import cli
        rc = cli.main([os.path.join(tempfile.gettempdir(), "no_such_file_9f3a.mp4")])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
