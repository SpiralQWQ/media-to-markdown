#!/usr/bin/env python3
"""media_to_markdown.cli.py 冒烟测试（Task-04：图片文件夹 / PDF 图片模式 / 传参）。

覆盖验收点：
  1. 传图片文件列表 → process_image（合成一份）
  2. 传图片文件夹（默认）→ process_images_to_mds（每张独立，收 images_notes/）
  3. --wizard + cfg album → 文件夹内图片合成一份
  4. cfg 传参透传（glm / delay / model / resume）
  5. 目录无图片 / 路径不存在 → 不崩溃

运行：python -m unittest tests.test_cli
"""
import os
import sys
import tempfile
import unittest
from unittest import mock

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
from media_to_markdown import cli
_OK_MDS = {"done": 2, "skipped": 0, "total": 2, "out": "x"}
_OK_ALBUM = {"clean_md": "x", "chars": 10, "images": 2}


class TestCliImage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="cli_img_")
        self.dir = os.path.join(self.tmp, "pdf_images")
        os.makedirs(self.dir)
        for n in ["a.jpg", "b.png"]:
            with open(os.path.join(self.dir, n), "wb") as f:
                f.write(b"x")
        self.img1 = os.path.join(self.dir, "a.jpg")

    def test_file_list_uses_process_image(self):
        """传图片文件 → 合成一份（现有行为不变）。"""
        with mock.patch("media_to_markdown.core.image.process_image", return_value=_OK_ALBUM) as m, \
             mock.patch("media_to_markdown.core.image.process_images_to_mds") as m2:
            cli.main([self.img1])
        m.assert_called_once()
        m2.assert_not_called()
        self.assertEqual(m.call_args[0][0], [self.img1])

    def test_folder_default_separate(self):
        """传图片文件夹（无向导）→ 每张独立 md，glm=no，model 空走环境默认。"""
        with mock.patch("media_to_markdown.core.image.process_images_to_mds", return_value=_OK_MDS) as m, \
             mock.patch("media_to_markdown.core.image.process_image") as m2, \
             mock.patch("media_to_markdown.cli._wizard_cfg", return_value={}):
            cli.main([self.dir])
        m.assert_called_once()
        m2.assert_not_called()
        args, kw = m.call_args
        self.assertEqual(args[0], self.dir)
        self.assertEqual(kw.get("glm"), "no")
        self.assertEqual(kw.get("model"), "")
        self.assertEqual(kw.get("resume"), "yes")

    def test_wizard_cfg_params_forwarded(self):
        """向导选 flash+间隔8+断点重转 → 参数透传到 process_images_to_mds。"""
        cfg = {"glm": "yes", "glm_model": "flash", "glm_delay": 8.0, "resume": "no"}
        with mock.patch("media_to_markdown.core.image.process_images_to_mds", return_value=_OK_MDS) as m, \
             mock.patch("media_to_markdown.cli._wizard_cfg", return_value=cfg):
            cli.main(["--wizard", self.dir])
        _, kw = m.call_args
        self.assertEqual(kw["glm"], "yes")
        self.assertEqual(kw["delay"], 8.0)
        self.assertEqual(kw["model"], "glm-4.6v-flash")
        self.assertEqual(kw["resume"], "no")

    def test_unknown_glm_model_falls_back_empty(self):
        """cfg glm_model 未知值 → model 回退空串（环境默认），不传 None。"""
        cfg = {"image_mode": "separate", "glm_model": "weird-model"}
        with mock.patch("media_to_markdown.core.image.process_images_to_mds", return_value=_OK_MDS) as m, \
             mock.patch("media_to_markdown.cli._wizard_cfg", return_value=cfg):
            cli.main(["--wizard", self.dir])
        _, kw = m.call_args
        self.assertEqual(kw["model"], "")

    def test_wizard_album_folder_uses_process_image(self):
        """向导选合成一份 + 传文件夹 → 目录内图片合成一份。"""
        cfg = {"image_mode": "album", "glm": "no"}
        with mock.patch("media_to_markdown.core.image.process_image", return_value=_OK_ALBUM) as m, \
             mock.patch("media_to_markdown.core.image.process_images_to_mds") as m2, \
             mock.patch("media_to_markdown.cli._wizard_cfg", return_value=cfg):
            cli.main(["--wizard", self.dir])
        m.assert_called_once()
        m2.assert_not_called()
        self.assertEqual(len(m.call_args[0][0]), 2)  # 目录内 2 张图

    def test_dir_no_images_no_crash(self):
        empty = os.path.join(self.tmp, "empty")
        os.makedirs(empty)
        with mock.patch("media_to_markdown.core.image.process_image") as m, \
             mock.patch("media_to_markdown.core.image.process_images_to_mds") as m2:
            cli.main([empty])
        m.assert_not_called()
        m2.assert_not_called()

    def test_missing_path_no_crash(self):
        with mock.patch("media_to_markdown.core.image.process_image") as m, \
             mock.patch("media_to_markdown.core.image.process_images_to_mds") as m2:
            cli.main([os.path.join(self.tmp, "nope")])
        m.assert_not_called()
        m2.assert_not_called()


class TestCliVideoAudio(unittest.TestCase):
    """cli 视频/音频/三模态路由冒烟（Task-07 验收）。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="cli_va_")
        self.video = os.path.join(self.tmp, "clip.mp4")
        self.audio = os.path.join(self.tmp, "voice.wav")
        self.img = os.path.join(self.tmp, "pic.jpg")
        for p in [self.video, self.audio, self.img]:
            open(p, "wb").write(b"x")

    def test_video_routes_to_process_video(self):
        with mock.patch("media_to_markdown.core.video.process_video",
                        return_value={"clean_md": "x", "chars": 1}) as m:
            cli.main([self.video])
        m.assert_called_once()
        self.assertEqual(m.call_args[1]["glm"], "no")

    def test_audio_routes_to_process_audio(self):
        with mock.patch("media_to_markdown.core.audio.process_audio",
                        return_value={"clean_md": "x", "chars": 1}) as m:
            cli.main([self.audio])
        m.assert_called_once()

    def test_trimodal_routes(self):
        """一次传视频+音频+图片 → 三个分支各触发一次。"""
        with mock.patch("media_to_markdown.core.video.process_video",
                        return_value={"clean_md": "x", "chars": 1}) as vm, \
             mock.patch("media_to_markdown.core.audio.process_audio",
                        return_value={"clean_md": "x", "chars": 1}) as am, \
             mock.patch("media_to_markdown.core.image.process_image",
                        return_value={"clean_md": "x", "chars": 1, "images": 1}) as im:
            cli.main([self.video, self.audio, self.img])
        vm.assert_called_once()
        am.assert_called_once()
        im.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
