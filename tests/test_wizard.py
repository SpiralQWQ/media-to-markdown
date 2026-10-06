#!/usr/bin/env python3
"""configs/wizard.py 向导单元测试。

覆盖验收点：
  1. 图片模式默认（album）配置落盘正确
  2. 合成一份 vs 每张独立选择
  3. GLM 模型 flashx / flash 选择 + 请求间隔（含非法输入回退）
  4. GLM 关闭时不再问模型/间隔
  5. 独立模式断点续传选择
  6. 跳过文件夹解析（中英文逗号）
  7. summary 收尾联动
  8. 旧配置向后兼容：已知键保留，已移除的键被丢弃
  9. 向导设置 → CLI 的接线（产物目录、中间文件清理）

运行：python -m pytest tests/test_wizard.py
"""
import io
import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

from media_to_markdown.configs import wizard as W

# 隔离环境：配置读写导到临时目录，绝不碰真实 wizard.json / .env
_TMP = tempfile.mkdtemp(prefix="wizimg_")
W.CONFIG_DIR = _TMP
W.CONFIG_FILE = os.path.join(_TMP, "wizard.json")


def _run(seq, *args, **kwargs):
    """按输入序列跑 run_wizard；mock input/sys.stdout/_ask_glm_config。"""
    it = iter(seq)
    buf = io.StringIO()

    def fake_input(prompt=""):
        if prompt:
            buf.write(prompt + "\n")
        try:
            return next(it)
        except StopIteration:
            raise EOFError

    with mock.patch("builtins.input", side_effect=fake_input), \
         mock.patch("sys.stdout", buf), \
         mock.patch.object(W, "_ask_glm_config", lambda: None):
        ret = W.run_wizard(*args, **kwargs)
    return buf.getvalue(), ret


# 通用尾部（与媒体类型无关）：存储根目录(选择 + 确认) + 中间文件处理 + 收尾回车
_TAIL = ["", "", "", ""]


class TestImageWizard(unittest.TestCase):
    def setUp(self):
        # 隔离：每个用例从纯默认配置开始，避免前例 save_config 污染
        if os.path.exists(W.CONFIG_FILE):
            os.remove(W.CONFIG_FILE)

    def test_defaults_album(self):
        """全默认：glm=yes · 模式A(album) · 模型A(flashx) · 间隔5 · 跳过空。

        输入：glm 模式 模型 间隔 跳过 + 尾部4 = 9
        """
        seq = [""] * 5 + _TAIL
        out, cfg = _run(seq, media_type="image")
        self.assertEqual(cfg["image_mode"], "album")
        self.assertEqual(cfg["glm"], "yes")
        self.assertEqual(cfg["glm_model"], "flashx")
        self.assertEqual(cfg["glm_delay"], 5.0)
        self.assertEqual(cfg["resume"], "yes")
        self.assertEqual(cfg["skip_folders"], [])
        self.assertIn("合成一份图集", out)

    def test_separate_resume_no(self):
        """每张独立 + 断点重转 + 跳过文件夹。

        输入：glm 模式B 模型 间隔 resumeB 跳过 + 尾部4 = 10
        """
        seq = ["", "B", "", "5", "B", "Python开发技术详解"] + _TAIL
        out, cfg = _run(seq, media_type="image")
        self.assertEqual(cfg["image_mode"], "separate")
        self.assertEqual(cfg["resume"], "no")
        self.assertEqual(cfg["skip_folders"], ["Python开发技术详解"])
        self.assertIn("每张独立 md", out)
        self.assertIn("全部重转", out)

    def test_flash_delay10(self):
        """GLM 免费版 flash + 间隔 10 秒。"""
        seq = ["", "", "B", "10", ""] + _TAIL
        out, cfg = _run(seq, media_type="image")
        self.assertEqual(cfg["glm_model"], "flash")
        self.assertEqual(cfg["glm_delay"], 10.0)
        self.assertIn("flash 免费版", out)
        self.assertIn("间隔 10 秒", out)

    def test_glm_off_keeps_defaults(self):
        """GLM 关闭：不再问模型/间隔，保留默认值。

        输入：glm(B=关) 模式 跳过 + 尾部4 = 7
        """
        seq = ["B", "", ""] + _TAIL
        out, cfg = _run(seq, media_type="image")
        self.assertEqual(cfg["glm"], "no")
        self.assertEqual(cfg["glm_model"], "flashx")
        self.assertEqual(cfg["glm_delay"], 5.0)
        self.assertNotIn("flash 免费版", out)
        self.assertNotIn("间隔", out)

    def test_skip_cn_comma(self):
        """跳过文件夹支持中英文逗号混用。"""
        seq = ["", "", "", "", "A目录，B目录, C目录"] + _TAIL
        out, cfg = _run(seq, media_type="image")
        self.assertEqual(cfg["skip_folders"], ["A目录", "B目录", "C目录"])

    def test_invalid_delay_falls_back(self):
        """间隔输入非法或负数 → 回退默认 5.0。"""
        seq = ["", "", "", "abc", ""] + _TAIL
        out, cfg = _run(seq, media_type="image")
        self.assertEqual(cfg["glm_delay"], 5.0)
        # 负数同样回退，防 time.sleep 异常
        seq2 = ["", "", "", "-3", ""] + _TAIL
        out2, cfg2 = _run(seq2, media_type="image")
        self.assertEqual(cfg2["glm_delay"], 5.0)

    def test_cleanup_and_root_choices_recorded(self):
        """中间文件与产物目录的选择要落进配置（这两个现在真的会被 CLI 消费）。"""
        root = tempfile.gettempdir()   # 真实可写目录，才能通过路径校验
        seq = ["", "", "", "", "", "B", root, "", "C", ""]
        out, cfg = _run(seq, media_type="image")
        self.assertEqual(cfg["cleanup"], "clean")
        self.assertEqual(cfg["notes_root"], root)


class TestBackwardCompat(unittest.TestCase):
    def setUp(self):
        if os.path.exists(W.CONFIG_FILE):
            os.remove(W.CONFIG_FILE)

    def test_removed_keys_are_dropped_known_keys_kept(self):
        """旧配置：仍存在的键保留，已删除的键不再残留。"""
        old = {"glm": "no", "interval": 2.0, "mode": "single", "note_style": "new",
               "naming": "custom", "speaker": "multi", "cache_place": "with_notes"}
        with open(W.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(old, f)
        cfg = W.load_config()
        self.assertEqual(cfg["glm"], "no")
        self.assertEqual(cfg["interval"], 2.0)
        for gone in ("mode", "note_style", "naming", "speaker", "cache_place"):
            self.assertNotIn(gone, cfg, "已删除的配置键 %s 不该残留" % gone)

    def test_defaults_are_filled(self):
        cfg = W.load_config()
        for key in ("image_mode", "glm_model", "glm_delay", "resume", "skip_folders"):
            self.assertIn(key, cfg)


class TestCliWiring(unittest.TestCase):
    """向导的产物目录 / 中间文件清理设置确实被 CLI 消费。"""

    def test_out_root_empty_when_no_root_configured(self):
        from media_to_markdown import cli
        self.assertEqual(cli._out_root({}, "x"), "")
        self.assertEqual(cli._out_root({"notes_root": ""}, "x"), "")

    def test_out_root_follows_configured_root(self):
        from media_to_markdown import cli
        got = cli._out_root({"notes_root": os.path.join("D:", "videos")}, "x")
        self.assertEqual(got, os.path.join("D:", "videos", "output", "cache", "x"))

    def test_cleanup_slim_removes_only_wav(self):
        from media_to_markdown import cli
        d = tempfile.mkdtemp(prefix="m2m_cl_")
        try:
            for n in ("a.wav", "a.json", "a_clean.md", "a_clean.json"):
                open(os.path.join(d, n), "w").close()
            cli._apply_cleanup("slim", os.path.join(d, "a_clean.md"))
            left = sorted(os.listdir(d))
            self.assertNotIn("a.wav", left)
            self.assertIn("a.json", left)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_cleanup_clean_keeps_only_clean_outputs(self):
        from media_to_markdown import cli
        d = tempfile.mkdtemp(prefix="m2m_cl_")
        try:
            for n in ("a.wav", "a.json", "a_clean.md", "a_clean.json", "a_visual.txt"):
                open(os.path.join(d, n), "w").close()
            cli._apply_cleanup("clean", os.path.join(d, "a_clean.md"))
            self.assertEqual(sorted(os.listdir(d)), ["a_clean.json", "a_clean.md"])
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_cleanup_keep_leaves_everything(self):
        from media_to_markdown import cli
        d = tempfile.mkdtemp(prefix="m2m_cl_")
        try:
            for n in ("a.wav", "a.json", "a_clean.md"):
                open(os.path.join(d, n), "w").close()
            cli._apply_cleanup("keep", os.path.join(d, "a_clean.md"))
            self.assertEqual(len(os.listdir(d)), 3)
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
