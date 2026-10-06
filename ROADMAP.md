# Roadmap

Direction for `media-to-markdown`. Nothing here is a commitment — priorities move
with real usage. Open an issue to push something up the list.

## Near term

- **Subtitle-track preference** — when a video ships an embedded subtitle track,
  use it and drop frame OCR to a low rate instead of OCR'ing every frame.
- **Optional GPU for ASR** — the ASR engine is CPU-only today; a machine with CUDA
  still transcribes on the CPU.

## Mid term

- **Non-Chinese cleaning rules** — the noise and watermark rules are tuned for
  Chinese ASR/OCR output; English material is untuned.
- **Pluggable output layout** — let the caller decide where artifacts land instead
  of the `<root>/output/cache/<name>/` convention.

## Exploring

- **Speaker separation** — label who said what in multi-speaker recordings.
