# Contributing to media-to-markdown

First off, thank you for considering a contribution — this project grew out of a
real study-material pipeline and every outside perspective makes it better.

## The one thing to understand before you start

The pipeline is **one-way and layered**:

```
cli  →  core  →  { engines, clean, assemble }
```

`core/` orchestrates; `engines/` wrap external tools (ffmpeg / ASR / OCR / GLM);
`clean/` and `assemble/` are pure text transforms. Nothing imports upward, and the
engines know nothing about the pipeline. That is what makes any single stage
replaceable — please keep it that way.

## How to set up

```bash
git clone https://github.com/SpiralQWQ/media-to-markdown.git
cd media-to-markdown
pip install -e ".[dev]"        # package + test deps (ASR extra not needed)
python -m pytest tests -q      # should be all green before you touch anything
```

The ASR extra (`pip install -e ".[asr]"`) pulls FunASR + PyTorch. The test suite
runs without it — the ASR engine is imported lazily, so CI installs the light set.

## How to contribute

1. **Open an issue first** for anything beyond a typo fix. A minimal repro — a
   small input file, the exact command, and the wrong output — is ideal.
2. **Fork & branch** — `feat/<short-name>` or `fix/<short-name>`.
3. **Add tests** — mirror the package structure under `tests/`. Fixtures live in
   `tests/sample/` and must be **synthetic**: no third-party screenshots, media,
   or book text.
4. **Check the entry point** — `python -m media_to_markdown --version` must run.
5. **Update the docs** — user-facing changes go into both READMEs; notable
   changes append to `CHANGELOG.md` and `CHANGELOG_zh.md`.

## Commit style

Conventional-ish, one line, imperative: `fix: ...`, `feat: ...`, `docs: ...`,
`test: ...`, `chore: ...`.

## Code style

- Python 3.10+ — CI runs 3.10, 3.11 and 3.12, so avoid syntax that is newer than
  that. (Notably: a nested f-string that reuses its outer quote character only
  works on 3.12+.)
- No hardcoded keys, absolute paths, or model names — environment variables or
  `configs/.env.example` only.
- Chinese comments are fine; keep user-facing strings consistent with the
  surrounding code.

## License

By contributing, you agree that your contributions are licensed under AGPL-3.0,
same as the project.
