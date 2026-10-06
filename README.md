# media-to-markdown

<p align="center">
  <kbd>English</kbd> · <kbd><a href="README_zh.md">简体中文</a></kbd>
</p>

<p align="center">
  <a href="https://github.com/SpiralQWQ/media-to-markdown/releases"><img src="https://img.shields.io/github/v/tag/SpiralQWQ/media-to-markdown?label=version" alt="version"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-3776AB" alt="Python 3.10+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-AGPL%203.0%20%7C%20Commercial-blue" alt="license"></a>
  <a href="https://github.com/SpiralQWQ/media-to-markdown/stargazers"><img src="https://img.shields.io/github/stars/SpiralQWQ/media-to-markdown?style=social" alt="stars"></a>
</p>

**Local video / image album / audio → cleaned, time-aligned Markdown.**

`media-to-markdown` turns **local media files** into a single "semi-finished"
Markdown document: speech transcripts and on-screen text interleaved by
timestamp, image albums merged in reading order, audio rendered as timestamped
lines. It cleans as it goes — watermarks, channel tags, OCR debris — but it does
**not** summarize, rewrite, or write teaching notes. That is the next stage, and
deliberately a different project.

## Table of Contents

- [What It Does](#what-it-does)
- [Why](#why)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Output Layout](#output-layout)
- [Architecture](#architecture)
- [File Tree](#file-tree)
- [Testing](#testing)
- [Roadmap](#roadmap)
- [FAQ](#faq)
- [Legal / Disclaimer](#legal--disclaimer)
- [License](#license)
- [💛 Support / Tip](#-support--tip)

## What It Does

| Modality | Input | Pipeline | Output |
|---|---|---|---|
| 🎬 Video | `.mp4 .webm .mkv .mov .flv .avi` | extract audio → ASR transcript, sample frames → OCR (+ optional GLM scene description) → clean → interleave by time | `🎤 speech` and `🖼 on-screen text` aligned on a shared timeline |
| 🖼️ Image album | `.jpg .jpeg .png .webp .gif .bmp` (files or a folder) | per-image OCR (reading order by coordinates) → clean → merge | `【图1】…【图N】` in one document, or one document per image |
| 🎧 Audio | `.mp3 .wav .m4a .flac .ogg .aac .wma` | ASR transcript → clean → timeline | `[MM:SS] 🎤 sentence` |

Everything lands in `output/cache/<name>/` as `<name>_clean.md`, next to the
intermediate artifacts so a re-run can resume instead of re-transcribing.

## Why

Raw ASR and OCR output is not usable as input to anything downstream:

- transcripts lose the visual context that made the video make sense;
- frame OCR is a pile of fragments with no temporal anchor;
- both carry watermarks, channel names, page numbers and OCR noise.

Fixing that is mechanical work, so it belongs in code rather than in a prompt.
`media-to-markdown` produces one deterministic, timestamped, cleaned Markdown file
— a stable contract for whatever consumes it next.

## Installation

```bash
git clone https://github.com/SpiralQWQ/media-to-markdown.git
cd media-to-markdown
pip install -e .            # OCR + cleaning (video frame OCR, image albums)
pip install -e ".[asr]"     # add if you also need speech transcription (FunASR + PyTorch, heavy)
```

**ffmpeg** is required as a system binary (audio extraction, frame sampling) and
must be on `PATH`:

- Windows: `winget install Gyan.FFmpeg`
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

**Engine interpreters.** By default the ASR and OCR engines run under the *same*
interpreter as the package, so `pip install -e .` is all you need. If you
prefer to keep FunASR and RapidOCR in separate virtual environments, point
`ASR_PY` / `OCR_PY` at their `python` executables (see `src/media_to_markdown/configs/.env.example`).

**GLM (optional, paid).** Passing `--glm yes` asks `glm-4.6v-flashx` to describe
what is on screen in each sampled frame — useful for slides and diagrams, and
entirely optional. Set `GLM_API_KEY` in a `.env` file at the project root; without
a key, `--glm` falls back to OCR-only.

## Configuration

Everything is optional — with no configuration at all, OCR runs locally and GLM
stays off.

| Variable | Default | What it does |
|---|---|---|
| `ASR_PY` | current interpreter | Interpreter that runs the FunASR engine — set it only if FunASR lives in another virtualenv |
| `OCR_PY` | current interpreter | Interpreter that runs the RapidOCR engine |
| `GLM_API_KEY` | *(unset)* | Zhipu GLM key; needed only for `--glm yes` |
| `GLM_API_URL` | `https://open.bigmodel.cn/api/paas/v4/chat/completions` | GLM endpoint |
| `GLM_MODEL` | `glm-4.6v-flashx` | GLM vision model |

Put them in a `.env` file **in the directory you run from** (it is git-ignored), or
export them as ordinary environment variables. `src/media_to_markdown/configs/.env.example`
is the template. The interactive wizard (`--wizard`) writes the same `.env` the
engines read.

## Usage

```bash
# Video: transcript + on-screen text, interleaved by timestamp
python -m media_to_markdown lecture.mp4 --glm no

# Video with scene understanding (needs GLM_API_KEY)
python -m media_to_markdown lecture.mp4 --glm yes

# Image album: several images merge into one document
python -m media_to_markdown page1.png page2.png page3.jpg

# Whole folder of images (one document per image by default)
python -m media_to_markdown ./slides/

# Audio
python -m media_to_markdown interview.wav

# Interactive wizard: framing interval, GLM, output folder, intermediate-file cleanup, …
python -m media_to_markdown lecture.mp4 --wizard
```

Progress is printed live per stage (`[ASR]`, `[OCR]`), and finished stages are
skipped on re-run.

## Output Layout

```
output/cache/<name>/
├── <name>_clean.md          # ← the deliverable
├── <name>_clean.json        # cleaned transcript, structure preserved
├── <name>.json              # raw ASR output (segments with ms timestamps)
├── <name>_visual.txt        # frame OCR, one block per sampled frame
└── <name>_visual_clean.txt  # cleaned frame OCR, each block anchored by [MM:SS]
```

## Architecture

```
cli.py                     thin entry point: classify input → route to a modality
└── src/
    ├── core/              orchestration per modality (video / image / audio)
    ├── engines/           external engines (asr / ocr / glm_vision / ffmpeg)
    ├── clean/             cleaning rules (transcript / visual / plain)
    ├── assemble/          output assembly (interleave / album / timeline)
    └── configs/           interactive wizard + config
```

One-way dependency only: `cli → core → {engines, clean, assemble}`. Engines know
nothing about the pipeline; the pipeline knows nothing about ffmpeg or FunASR
internals. That is what makes a stage replaceable — swap the ASR engine and only
`engines/asr.py` changes.

## File Tree

```
media-to-markdown/
├── cli.py
├── requirements.txt
├── src/
│   ├── core/                video.py · image.py · audio.py · base.py
│   ├── engines/             asr.py · ocr.py · glm_vision.py · ffmpeg.py
│   ├── clean/               transcript.py · visual.py · plain.py
│   ├── assemble/            interleave.py · album.py · timeline.py
│   └── configs/             wizard.py · .env.example
├── tests/                   108 tests
│   ├── sample/              synthetic fixtures (no third-party content)
│   └── test_*.py
└── assets/                  donation QR codes
```

## Testing

```bash
python -m pytest tests -q
# 108 passed
```

All fixtures under `tests/sample/` are synthetic and reproducible — no
third-party screenshots or media are shipped in this repository.

## Roadmap

See [`ROADMAP.md`](ROADMAP.md). Near term: prefer an embedded subtitle track when a
video has one, and an opt-in GPU path for ASR.

## FAQ

**Does it download videos from links (Douyin / YouTube / Bilibili)?**
No. This project only reads **local files**. If you want a link-to-notes pipeline,
that is a different project.

**Does it write the study notes?**
No. It stops at cleaned, time-aligned Markdown. Turning that into teaching notes
is a separate stage with its own project.

**Is the transcription Chinese-only?**
The cleaning rules are tuned for Chinese ASR output (Chinese punctuation, filler
words, channel watermarks), and the note-oriented wording is Chinese. The engines
themselves are multilingual, but non-Chinese output has not been tuned or tested.

**Do I have to use GLM?**
No. OCR runs locally and free (RapidOCR). GLM only adds one-line descriptions of
what is visible on screen, and only when you pass `--glm yes`.

**A run died halfway — does it start over?**
No. Engine artifacts are reused: if `<name>.json` / `<name>_visual.txt` already
exist, that stage is skipped and the pipeline resumes from cleaning.

## Legal / Disclaimer

This tool is intended for content you have the right to process — your own
recordings, material you licensed, or material that is lawfully accessible to you.
Transcribing and redistributing someone else's video, course, or book may infringe
their rights. You are responsible for how you use it, and for complying with the
terms of any platform or service involved. The authors provide this software
as-is, without warranty, and take no responsibility for misuse.

## License

[AGPL-3.0](LICENSE) for the open-source version. Commercial licensing is available
— see [COMMERCIAL.md](COMMERCIAL.md).

## 💛 Support / Tip

If this project saves you some time, you're welcome to buy me a coffee ☕.
Donation is entirely optional — the project stays free and open source.

<p align="center">
  <img src="assets/donate_wechat.jpg" alt="WeChat Pay" width="200">
  <img src="assets/donate_alipay.jpg" alt="Alipay" width="200">
</p>
