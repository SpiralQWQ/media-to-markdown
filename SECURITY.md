# Security Policy / 安全策略

## Supported Versions / 支持的版本

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅ actively maintained |
| < 1.0   | ❌ pre-release, not supported |

## Reporting a Vulnerability / 报告漏洞

If you find a security issue, **please do not open a public issue first**. Instead:

1. Open a private report via **GitHub Security Advisories** → *New advisory* on this
   repository (or email the maintainer privately if you have a known contact).
2. Include: affected version, OS, a minimal repro, and the impact you observed.
3. We'll acknowledge within **7 days** and aim to ship a fix in the next release.

We're a small project — thank you for handling it discreetly and giving us time to fix it.

> 发现安全问题请**先走 GitHub 私密安全通告**，不要直接公开提 issue。附上：影响版本、系统、最小复现、影响面。7 天内确认，随下个版本修复。

## Security Notes / 安全说明

- **Secrets never belong in the repo.** `GLM_API_KEY` is a personal credential —
  keep it in `.env` (git-ignored) or an environment variable. If you accidentally
  commit one, rotate it immediately. `ASR_PY` / `OCR_PY` are interpreter *paths*,
  not secrets.
- **`.env` is git-ignored** — copy `configs/.env.example` locally, never commit the
  real file.
- **Local files only.** This tool downloads nothing; it reads media you already
  have on disk. Processing or republishing material you have no right to use is
  still a copyright problem — see the disclaimer in the README.
- **LLM egress.** With `--glm yes`, sampled frames are sent to the configured GLM
  endpoint. Do not point it at material you have no right to send to a third party.
- **External engines.** ffmpeg, FunASR and RapidOCR are invoked as separate
  processes. Install them from their official sources and keep them updated.
