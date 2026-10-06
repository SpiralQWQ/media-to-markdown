#!/usr/bin/env python3
"""core/{video,image,audio} 编排单元测试（mock 引擎/子进程，验证断点/失败/闭环）。

运行：python -m unittest tests.test_core
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
_SAMPLE = os.path.join(_ROOT, "tests", "sample")

from media_to_markdown.core.video import process_video, _run_live, _save_prog, _load_prog
from media_to_markdown.core.audio import process_audio
from media_to_markdown.core.image import process_image, process_images_to_mds


def _write(path, content):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


class TestVideo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="m2n_v_")
        self.video = os.path.join(self.tmp, "clip.mp4")
        _write(self.video, "fake video bytes")

    def test_missing_video(self):
        r = process_video(os.path.join(self.tmp, "nope.mp4"), out_root=self.tmp)
        self.assertIn("error", r)

    def test_resume_with_existing_products(self):
        """预置 json+visual → 断点跳过引擎 → 真实 clean+assemble → clean.md"""
        shutil.copy(os.path.join(_SAMPLE, "video_sample.json"),
                    os.path.join(self.tmp, "clip.json"))
        shutil.copy(os.path.join(_SAMPLE, "video_sample_visual.txt"),
                    os.path.join(self.tmp, "clip_visual.txt"))
        with mock.patch("media_to_markdown.core.video.ffmpeg.extract_audio", return_value=True):
            r = process_video(self.video, glm="no", out_root=self.tmp)
        self.assertIn("clean_md", r)
        self.assertTrue(os.path.isfile(r["clean_md"]))
        self.assertGreater(r["chars"], 0)

    def test_engine_failure_no_crash(self):
        """无产物 + 引擎失败 → 不崩溃，返回 dict"""
        cp = subprocess.CompletedProcess([], 0)
        with mock.patch("media_to_markdown.core.video.ffmpeg.extract_audio", return_value=True), \
             mock.patch("media_to_markdown.core.video._run_live", return_value=cp):
            r = process_video(self.video, glm="no", out_root=self.tmp)
        self.assertIsInstance(r, dict)

    # ---- v0.5.0 回移植（开源版同步）：实时进度/断点/引擎防呆 ----

    def test_progress_save_load_roundtrip(self):
        """进度文件写→读 roundtrip；坏文件/缺文件返回空集不崩。"""
        _save_prog(self.tmp, all_done=True)
        self.assertEqual(_load_prog(self.tmp), {"all_done"})
        self.assertEqual(_load_prog(os.path.join(self.tmp, "none")), set())
        _write(os.path.join(self.tmp, "_progress.json"), "{bad json")
        self.assertEqual(_load_prog(self.tmp), set())

    def test_all_done_resume_returns_existing_md(self):
        """all_done 断点 → 直接返回既有 clean_md，不再跑清洗/组装。"""
        clean_md = os.path.join(self.tmp, "clip_clean.md")
        _write(clean_md, "# done md")
        _save_prog(self.tmp, all_done=True)
        with mock.patch("media_to_markdown.core.video.ffmpeg.extract_audio", return_value=True):
            r = process_video(self.video, glm="no", out_root=self.tmp)
        self.assertEqual(r["chars"], len("# done md"))
        self.assertTrue(os.path.isfile(r["clean_md"]))

    def test_run_live_streams_timeout_and_engine_guard(self):
        """_run_live：流式捕获 stdout；沉默进程超时被杀；空解释器防呆。"""
        py = sys.executable
        r = _run_live([py, "-c", "print('hello'); print('world')"], label="T")
        self.assertEqual(r.returncode, 0)
        self.assertIn("hello", r.stdout)
        self.assertIn("world", r.stdout)
        # 沉默进程超时（开源版修的 bug：readline 版会永阻塞）
        r2 = _run_live([py, "-c", "import time; time.sleep(5)"], timeout=1, label="T")
        self.assertNotEqual(r2.returncode, 0)  # timeout killed (code varies by OS)
        # 空解释器防呆（ASR_PY 被清空时不崩）
        r3 = _run_live(["", "x"], label="T")
        self.assertEqual(r3.returncode, 1)
        self.assertIn("not configured", r3.stderr)



class TestAudio(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="m2n_a_")
        self.audio = os.path.join(self.tmp, "voice.wav")
        _write(self.audio, "fake wav")

    def test_missing_audio(self):
        r = process_audio(os.path.join(self.tmp, "nope.wav"), out_root=self.tmp)
        self.assertIn("error", r)

    def test_resume_with_existing_json(self):
        shutil.copy(os.path.join(_SAMPLE, "video_sample.json"),
                    os.path.join(self.tmp, "voice.json"))
        r = process_audio(self.audio, out_root=self.tmp)
        self.assertTrue(os.path.isfile(r["clean_md"]))
        self.assertGreater(r["chars"], 0)

    def test_engine_failure_no_crash(self):
        cp = subprocess.CompletedProcess([], 0)
        with mock.patch("media_to_markdown.core.audio._run_live", return_value=cp):
            r = process_audio(self.audio, out_root=self.tmp)
        self.assertIsInstance(r, dict)


class TestImage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="m2n_i_")

    def test_empty_images(self):
        r = process_image([], out_root=self.tmp)
        self.assertIn("error", r)

    def test_glm_no(self):
        with mock.patch("media_to_markdown.core.image.ocr.ocr_images_to_text",
                        return_value=["画面文字A"]):
            r = process_image(["a.png"], glm="no", out_root=self.tmp)
        self.assertTrue(os.path.isfile(r["clean_md"]))
        self.assertEqual(r["images"], 1)
        with open(r["clean_md"], encoding="utf-8") as f:
            md = f.read()
        self.assertIn("画面文字A", md)
        self.assertNotIn("GLM画面理解", md)

    def test_glm_yes_adds_block(self):
        with mock.patch("media_to_markdown.core.image.ocr.ocr_images_to_text",
                        return_value=["画面文字A"]), \
             mock.patch("media_to_markdown.core.image._glm_describe", return_value="描述A"):
            r = process_image(["a.png"], glm="yes", out_root=self.tmp)
        with open(r["clean_md"], encoding="utf-8") as f:
            md = f.read()
        # 清洗规范：GLM 标签行删除，描述内容保留
        self.assertNotIn("GLM画面理解", md)
        self.assertIn("描述A", md)

    def test_glm_failure_no_crash(self):
        def _boom(_img):
            raise RuntimeError("glm 挂了")
        with mock.patch("media_to_markdown.core.image.ocr.ocr_images_to_text",
                        return_value=["画面文字A"]), \
             mock.patch("media_to_markdown.core.image._glm_describe", side_effect=_boom):
            r = process_image(["a.png"], glm="yes", out_root=self.tmp)
        self.assertTrue(os.path.isfile(r["clean_md"]))


class TestImageMds(unittest.TestCase):
    """process_images_to_mds：每张独立 md / 断点 / 模型透传 / 限流间隔（Task-04）。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="m2n_mds_")
        self.dir = os.path.join(self.tmp, "imgs")
        os.makedirs(self.dir)
        for n in ["a.jpg", "b.png", "c.webp"]:
            _write(os.path.join(self.dir, n), "fake image bytes")
        self.out = os.path.join(self.tmp, "out")

    def test_missing_dir(self):
        r = process_images_to_mds(os.path.join(self.tmp, "nope"))
        self.assertIn("error", r)

    def test_no_images_in_dir(self):
        empty = os.path.join(self.tmp, "empty")
        os.makedirs(empty)
        r = process_images_to_mds(empty)
        self.assertIn("error", r)

    def test_basic_no_glm(self):
        with mock.patch("media_to_markdown.core.image.ocr.make_ocr", return_value=None), \
             mock.patch("media_to_markdown.core.image.ocr.ocr_image_to_text", return_value="画面文字A"):
            r = process_images_to_mds(self.dir, out_dir=self.out, glm="no")
        self.assertEqual(r["done"], 3)
        self.assertEqual(r["skipped"], 0)
        self.assertEqual(r["total"], 3)
        self.assertTrue(os.path.isfile(os.path.join(self.out, "a.md")))
        with open(os.path.join(self.out, "a.md"), encoding="utf-8") as f:
            md = f.read()
        self.assertIn("## 图片内容（OCR）", md)
        self.assertNotIn("## GLM 画面理解", md)

    def test_resume_skips_existing(self):
        _write(os.path.join(self.out, "a.md"), "done")
        with mock.patch("media_to_markdown.core.image.ocr.make_ocr", return_value=None), \
             mock.patch("media_to_markdown.core.image.ocr.ocr_image_to_text", return_value="画面文字A"):
            r = process_images_to_mds(self.dir, out_dir=self.out, glm="no")
        self.assertEqual(r["done"], 2)
        self.assertEqual(r["skipped"], 1)

    def test_resume_no_redoes(self):
        _write(os.path.join(self.out, "a.md"), "done")
        with mock.patch("media_to_markdown.core.image.ocr.make_ocr", return_value=None), \
             mock.patch("media_to_markdown.core.image.ocr.ocr_image_to_text", return_value="画面文字A"):
            r = process_images_to_mds(self.dir, out_dir=self.out, glm="no", resume="no")
        self.assertEqual(r["done"], 3)
        self.assertEqual(r["skipped"], 0)

    def test_duplicate_stem_not_overwritten(self):
        """同名不同扩展（a.jpg + a.png）→ 后一个跳过，不覆盖已生成 md。"""
        _write(os.path.join(self.dir, "a.png"), "dup")
        with mock.patch("media_to_markdown.core.image.ocr.make_ocr", return_value=None), \
             mock.patch("media_to_markdown.core.image.ocr.ocr_image_to_text", return_value="画面文字A"):
            r = process_images_to_mds(self.dir, out_dir=self.out, glm="no")
        self.assertEqual(r["done"], 3)     # a.jpg, b.png, c.webp
        self.assertEqual(r["skipped"], 1)  # a.png 重名跳过
        self.assertEqual(r["total"], 4)
        with open(os.path.join(self.out, "a.md"), encoding="utf-8") as f:
            self.assertIn("# a", f.read())

    def test_glm_model_forwarded_and_sleep(self):
        """模型透传到 _glm_describe_en；每张 GLM 成功后 sleep(delay) 真限流。"""
        with mock.patch("media_to_markdown.core.image.ocr.make_ocr", return_value=None), \
             mock.patch("media_to_markdown.core.image.ocr.ocr_image_to_text", return_value="画面文字A"), \
             mock.patch("media_to_markdown.core.image._glm_describe_en", return_value="描述A") as g, \
             mock.patch("time.sleep") as slp:
            r = process_images_to_mds(self.dir, out_dir=self.out,
                                      glm="yes", model="glm-4.6v-flash", delay=2)
        # 模型透传到 _glm_describe_en 第 3 个位置参数
        self.assertEqual(g.call_args[0][2], "glm-4.6v-flash")
        # 每张 GLM 成功后 sleep(delay) 限流
        self.assertIn(2.0, [c[0][0] for c in slp.call_args_list])
        self.assertEqual(r["done"], 3)
        with open(os.path.join(self.out, "a.md"), encoding="utf-8") as f:
            md = f.read()
        self.assertIn("## GLM 画面理解", md)
        self.assertIn("描述A", md)

    # ---- fixloop S2 边界穷举（v0.10.1）----

    def test_empty_ocr_uses_placeholder(self):
        """OCR 返回空 → 占位符（无文字），md 结构完整不空段。"""
        with mock.patch("media_to_markdown.core.image.ocr.make_ocr", return_value=None), \
             mock.patch("media_to_markdown.core.image.ocr.ocr_image_to_text", return_value=""):
            r = process_images_to_mds(self.dir, out_dir=self.out, glm="no")
        with open(os.path.join(self.out, "a.md"), encoding="utf-8") as f:
            md = f.read()
        self.assertIn("## 图片内容（OCR）", md)
        self.assertIn("（无文字）", md)

    def test_clean_applied_to_ocr(self):
        """T2：OCR 文本过 clean_plain_text（短行噪音删除；长行保留是防误删设计）。"""
        noisy = "正常内容\n点赞\n>>> \n好内容2"
        with mock.patch("media_to_markdown.core.image.ocr.make_ocr", return_value=None), \
             mock.patch("media_to_markdown.core.image.ocr.ocr_image_to_text", return_value=noisy):
            process_images_to_mds(self.dir, out_dir=self.out, glm="no")
        with open(os.path.join(self.out, "a.md"), encoding="utf-8") as f:
            md = f.read()
        self.assertIn("正常内容", md)
        self.assertIn("好内容2", md)
        self.assertNotIn("点赞", md)      # 短水印行被删
        self.assertNotIn(">>>", md)

    def test_long_line_not_cleaned(self):
        """长行内嵌界面词不删（防误删正文的有意设计）。"""
        long_line = "这是一个很长的正常描述行 包含了 System Settings 菜单词但属于正文内容不应删除" * 1
        with mock.patch("media_to_markdown.core.image.ocr.make_ocr", return_value=None), \
             mock.patch("media_to_markdown.core.image.ocr.ocr_image_to_text", return_value=long_line):
            process_images_to_mds(self.dir, out_dir=self.out, glm="no")
        with open(os.path.join(self.out, "a.md"), encoding="utf-8") as f:
            self.assertIn("System Settings", f.read())  # 长行保留

    def test_clean_to_empty_falls_back(self):
        """OCR 全是噪音 → 清洗后为空 → 占位符兜底（不产生空 OCR 段）。"""
        with mock.patch("media_to_markdown.core.image.ocr.make_ocr", return_value=None), \
             mock.patch("media_to_markdown.core.image.ocr.ocr_image_to_text", return_value=">>>"):
            process_images_to_mds(self.dir, out_dir=self.out, glm="no")
        with open(os.path.join(self.out, "a.md"), encoding="utf-8") as f:
            md = f.read()
        self.assertIn("（无文字）", md)

    def test_glm_retry_until_success(self):
        """GLM 失败→重试直到成功（铁律：绝不跳过）。flaky 全局计数：
        第 1 张试 3 次成功，第 2/3 张首试即成（mock 状态延续）→ 共 5 次调用。"""
        calls = {"n": 0}
        def flaky(*a, **kw):
            calls["n"] += 1
            return "描述" if calls["n"] >= 3 else ""
        with mock.patch("media_to_markdown.core.image.ocr.make_ocr", return_value=None), \
             mock.patch("media_to_markdown.core.image.ocr.ocr_image_to_text", return_value="文"), \
             mock.patch("media_to_markdown.core.image._glm_describe_en", side_effect=flaky), \
             mock.patch("time.sleep"):
            r = process_images_to_mds(self.dir, out_dir=self.out, glm="yes")
        self.assertEqual(r["done"], 3)   # 3 张全部成功，无一跳过
        self.assertEqual(calls["n"], 5)  # 3+1+1 次调用
        with open(os.path.join(self.out, "a.md"), encoding="utf-8") as f:
            self.assertIn("## GLM 画面理解", f.read())


if __name__ == "__main__":
    unittest.main(verbosity=2)
