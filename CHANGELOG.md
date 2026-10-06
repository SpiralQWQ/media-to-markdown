# Changelog

<p align="center"><kbd>🇺🇸 English</kbd> · <kbd><a href="CHANGELOG_zh.md">简体中文</a></kbd></p>

All notable changes to this project are documented here, following
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
[Semantic Versioning](https://semver.org/).

Versions below 1.0.0 record this tool's life as a personal working script. They are
kept for history and have been rewritten from the original working log — internal
process notes were dropped, the changes themselves are unchanged.

## [1.0.0] - 2026-10-06

_First public release: packaged, cleaned of anything machine-specific, and open to contributors._

### Added

- Installable packaging: the `src/media_to_markdown/` layout, `pip install -e .`, a
  `python -m media_to_markdown` entry point and a `media-to-markdown` console script.
- `pyproject.toml` with the speech engine as an optional extra (`.[asr]`), so someone who
  only needs OCR does not have to install PyTorch.
- Continuous integration: the test suite runs on Linux, Windows and macOS across Python
  3.10, 3.11 and 3.12, plus a syntax gate and an entry-point smoke test.
- Community files: `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, issue and
  pull-request templates, and `ROADMAP.md`.
- A `Configuration` section in the README documenting every environment variable, and a
  roadmap section.
- The wizard can choose **scene-aware sampling** — sample a frame only when the picture
  changes — an engine feature that was previously unreachable from the CLI.

### Changed

- The wizard no longer asks questions whose answers nothing reads. Course naming, note
  naming, note style, speaker count, batch mode and cache placement were left over from
  the "generate study notes" stage this tool no longer performs, and have been removed.
  In their place, the settings that do matter — frame interval, sampling strategy, output
  folder and intermediate-file policy — are now actually applied by the pipeline.
- A saved wizard configuration now drops keys that no longer exist instead of carrying
  them forward forever.
- The key written by the interactive wizard now lands in the same `.env` the GLM engine
  reads. Previously the wizard saved it under `configs/.config/` while the engine looked
  in `engines/.config/`, so a key the wizard had just verified was never found.
- `ASR_PY` / `OCR_PY` default to the current interpreter instead of a hardcoded path on
  the author's machine.
- The wizard reports the current working directory as the default output root, matching
  where the pipeline actually writes.
- All test fixtures are synthetic; the repository ships no third-party media.

### Fixed

- `clean/visual.py` no longer treats 知识点 ("knowledge point") as a watermark. It is one
  of the most common words in study material, and the filter was deleting real content.
- Segment cleaning no longer empties every line that lacks an ASCII letter/digit or a
  Chinese/Japanese ideograph — Cyrillic, Hangul, Arabic and full-width Latin text used to
  vanish silently.
- The GLM retry loop gives up after three attempts and writes the image OCR-only, instead
  of retrying forever and hanging the whole batch when the key is missing.
- Frames past the 99-minute mark are no longer dropped when interleaving a long video.
- A transcript whose `segments` / `sentences` is explicitly `null` no longer crashes
  cleaning, and a non-numeric timestamp no longer aborts assembly.
- English case normalisation no longer rewrites a target word inside a longer one
  (`MyPOWERSHELLish` stays intact) while still normalising next to Chinese text.
- The CLI returns a non-zero exit code when any input fails, so scripts and CI can tell.
- A missing `ffmpeg` now raises an error that says how to install it, instead of a bare
  `FileNotFoundError`.
- The frame-cap warning is only printed when frames were actually truncated; it used to
  fire on long videos that were sampled in full.
- Removed dead code: an unused `numpy` import, an unused `re` import, a dead
  Chinese/non-Chinese branch in transcript deduplication, and two functions with no callers.

### Removed

- The PDF-image helpers (`batch_images.py`, `embed_image_notes.py`, `fix_md_image_refs.py`)
  and the `legacy/` script folder were not carried into this release. They were built for
  one private note pipeline and depended on a separate project, so they could not run
  stand-alone.

### Security

- No credentials or machine-specific absolute paths remain anywhere in the source tree.
- The published test fixtures contain no third-party screenshots, media or book text.

## [0.10.1] - 2026-08-29
_Image output format aligned, cleaning wired in, embed script moved home._

### Changed

- **Image output format aligned**: `process_images_to_mds` now emits `## 图片内容（OCR）` + `## GLM 画面理解`, matching the format of previously converted images so old and new output merge seamlessly.
- **Cleaning wired into image transcription**: `process_images_to_mds` now runs `clean_plain_text` (drops UI noise lines and labels, normalizes punctuation), so transcribed output is cleaned in one pass.
- **Embed script moved home**: `embed_image_notes.py` (embeds each image's note at its position in full.md, producing an AI-friendly self-contained document) moved into `src/scripts/`; `main` now accepts argv arguments; 4 unit tests added (embed / missing-note retention / volume-recursive note lookup / dry-run).

### Fixed

- `embed_image_notes.py` entry point never propagated the exit code (a wrong path always exited 0) → now `sys.exit(main())`; a wrong path exits with code 2 as verified.
- Edge cases locked down with tests: empty note files, notes without a GLM section, repeated references to the same image, Chinese filename stems, custom directory names (`--images-dir` / `--notes-dir`).

## [0.10.0] - 2026-08-23
_PDF image mode, batch conversion, and image-reference rewriting._

### Added

- **PDF image mode**: `core/image.py` `process_images_to_mds()` — writes one standalone md per image into `images_notes/` next to the source folder; supports resume (skips existing output) + retries on GLM failure until it succeeds.
- **Image wizard asks more questions**: `configs/wizard.py` asks upfront whether to merge into one file or keep one md per image, whether to use the stable flashx or the free flash GLM tier, the request delay, resume vs. from scratch, and which folders to skip; the configuration is saved and reused.
- **CLI image folder**: `python -m media_to_markdown <image folder>` writes one md per image; `--wizard` can request a merged single file; glm / delay / model / resume are all forwarded.
- **Batch traversal**: `src/scripts/batch_images.py` — `--root` recursively scans folders containing images and converts them one by one, `--skip` excludes paths, resume is built in, wizard configuration acts as the fallback and CLI flags override it.
- **Reference rewriting**: `src/scripts/fix_md_image_refs.py` — rewrites image references in full.md into `images_notes/*.md` links, leaving references without a matching md untouched.

### Changed

- `process_images_to_mds` now rate-limits for real: `sleep(delay)` between two GLM requests (prevents 429 on the free tier); model selection (flashx / flash) is overridable via environment variables; `resume="no"` reconverts everything.

## [0.9.5] - 2026-08-22

_Live progress output and batch error recovery._

### Added

- **Progress feedback**: live printing of ASR/OCR subprocess output with [ASR]/[OCR] tags
- **Batch numbering**: video/audio loops show [1/N] indices, clear visibility when processing multiple files
- **Error recovery**: `_progress.json` records all completion states; cleaning + assembly skip completed steps on resume

### Changed

- 76 tests all green

## [0.9.4] - 2026-08-22

_Source tree reorganized per directory contract, root 13 → 5._

### Changed

- Root directory cleanup: 13 → 5 (src/ output/ docs/ tests/ + entry point)
- Source code consolidated into src/ (assemble/clean/configs/core/engines/scripts)
- Artifacts isolated into output/ (cache/temp/validation)
- Path references in cli.py and all modules and tests updated accordingly
- 76 tests all green, cli smoke test normal

## [0.9.3] - 2026-08-21

_Stability fixes: timeline ordering and empty-source guards._

### Fixed

- Audio timeline now sorted by time
- core/video | audio engines guard against empty sources on failure (returns error instead of crashing)
- cli._classify null-value guard
- core/image GLM exceptions caught by outer try with graceful degradation

### Changed

- Added 76 unit tests (tests/, including sample fixtures), all passing

## [0.9.2] - 2026-08-19
_The wizard is now media-type aware and only asks relevant questions._

### Added

- **Media-type-aware wizard**: `run_wizard(media_type=…)` asks only what applies to the type — video asks everything (visuals / GLM / speakers / course), album asks only GLM (understand each image), audio asks only about speakers; the prompt text and closing summary both fit the type.
- **CLI `--wizard`**: pops the wizard matching the media type and forwards glm; without `--wizard` the previous default / `--glm` behavior is kept for compatibility.
- Boundary cases (invalid / over-long / empty input) do not crash; output is reachable for all three media types; cli and batch paths produce identical results.

## [0.9.1] - 2026-08-19
_Image output aligned with video; album images merged into one file._

### Changed

- **Image pipeline aligned with video**: each image now emits `【图片N】+ [画面文字 OCR] + [GLM 画面理解]` (same engine, OCR coordinate ordering + GLM), with no timeline — image numbers are used instead.
- **CLI album batching**: `python -m media_to_markdown 图1 图2 图3` merges the album into one md (`【图片1】…【图片N】`) instead of one file per image; video and audio still produce independent files.
- Multi-image merge verified with a real run.

## [0.9.0] - 2026-08-19
_Image and audio pipelines added alongside video._

### Added

- **Image pipeline**: `core/image.py` + `assemble/album.py` — image / album → OCR (mandatory, coordinate ordering) + optional GLM → cleaning → image-order draft md.
- **Audio pipeline**: `core/audio.py` + `assemble/timeline.py` — audio → ASR → json → cleaning → time-ordered md.
- `engines/ocr.py` exposes image OCR (`ocr_image_to_text` / `ocr_images_to_text`), sharing coordinate ordering with video frames.
- `cli.py` routes all three media types (video / image / audio); the six input guards are kept.

### Changed

- Artifacts synchronized: video = time-interleaved, image = image-ordered, audio = time-ordered; draft md is cleaned but not reorganized; json is always the audio transcript, txt is always visuals / images.
- Image and audio output now defaults to a transcription cache directory (image / audio) instead of polluting the root.
- Cross-path consistency sampling passed; verified with real images and audio.

### Security

- ASR / OCR interpreters come from environment variables + package defaults; GLM can be downgraded optionally; `.env.example` contains no secrets.

## [0.8.0] - 2026-08-19

_Directory restructuring: thin entry point, business domains, and layering._

### Changed

- Flat scripts → directory contract: `cli.py` (thin entry router) → `core` (business domains: base/video) → `engines` (asr/ocr/glm_vision/ffmpeg) + `clean` (transcript/visual/plain) + `assemble` (interleave) + `configs` (wizard/.env.example).
- Old `scripts/` and legacy main flow archived to `scripts/_legacy/`; docs to `docs/`; old tasks/logs to `temp/_legacy_tasks/`.
- Transcription engine → `engines/asr.py`; frame/image OCR (with coordinate sorting) → `engines/ocr.py`; cleaning built in with zero dependencies (no longer depends on text-cleaning-engine).
- End-to-end testing on real data (audio 107 / images 179) with zero regressions.

### Added

- `core`/`engines`/`clean`/`assemble` domains have zero external dependencies, one-way dependency core → {engines,clean,assemble,configs}.
- `cli.py` three-mode detection (video wired; image/audio are phase-2 stubs) + six types of input guards.

### Security

- ASR/OCR interpreters use environment variables + package defaults; .env.example is example only, no hardcoded keys.

## [0.7.1] - 2026-08-11

_Patch C follow-up: review hint now lists specific segments._

### Changed

- `course_video_to_notes.py` review_hint: from "count only" to **listing specific segments**
  - Each segment includes `[MM:SS]` timestamp + first 60 chars of text
  - Max 10 segments listed; if more, shows "remaining N segments omitted" (prevents overly long prompts)
  - Read-only on review/confidence fields, no value changes
  - Example:
    ```
    ⚠️ 3 low-confidence segments pending review; mark [review] at corresponding knowledge points in notes (keep original text, only flag as uncertain):
      [00:03] w s l concatenation residue
      [01:05] another uncertain segment with longer content truncated for display
    ```
- 4-scenario tests (3 segments / 12-segment truncation / no review / read-only fields) passed; full script syntax + wizard regression 31 PASS + patch integration without breakage.

## [0.7.0] - 2026-08-11

_Five transcription capability patches driven by a 195-repository survey._

### Added

- **Patch A · VAD silence pre-filtering** (silero-vad): trim pure silence head/tail before transcription with silero-vad, reducing hallucinated words + saving ASR compute; guard logic (speech ratio / head-tail silence thresholds) prevents deleting lecture pauses
- **Patch B · Hotword post-processing correction layer** (asr-hotword approach): three-layer correction — exact replacement (corrections.json) + Chinese homophone sliding window (pinyin ≥95% to correct) + English proper noun case normalization; prevents false corrections (no correction if character count differs)
- **Patch C · Low-confidence segment review flagging** (transcript-critic approach): segments with confidence<0.5 flagged `review:true`, note generation prompts "N transcription segments pending review, mark [review] at corresponding locations"
- **Patch D · Deep learning denoiser isolation**: denoiser conflicts with FunASR's omegaconf, breaking transcription → moved to independent environment (`DENOISE_PY` env var), safe skip if not configured
- **Patch E · ct-punc punctuation**: confirmed integrated (SenseVoice `punc_model="ct-punc"`), verified punctuation works in real-world testing
- New dependencies: silero-vad 6.2.1 / pypinyin 0.55 / onnxruntime 1.28 (rapidfuzz already present)

### Fixed

- **Bug · silero sample index vs millisecond unit mismatch**: VAD detection start/end are sample counts, mistakenly used as milliseconds for ratio → fixed `/sr` to seconds (prevents incorrect trimming)
- **Bug · English fuzz false positives**: whole-word fuzz ineffective for English and I→AI false positive → changed to Chinese homophone sliding window (same character count + pinyin ≥95%) + English case normalization
- **Bug · omegaconf conflict breaking transcription**: denoiser depends on omegaconf 1.x conflicting with FunASR (requires ≥2.0), installation breaks core transcription → isolated as DENOISE_PY independent environment

### Changed

- Wizard regression 31 PASS / full patch integration 7 PASS / denoiser safety 3 PASS / full script syntax passed.

## [0.6.6] - 2026-08-10
_Real-time progress bars and stage timing overview._

### Added

- Real-time progress display: new `run_stream()` passes subprocess stdout directly to the terminal while capturing stderr for error diagnosis, so transcription and OCR progress is no longer swallowed.
- Progress bars for transcription, OCR, and GLM stages: replaced line-by-line output with a single-line refresh showing percentage, current/total count, and estimated remaining time.
- Stage timing summary: each stage prints its elapsed time on completion, and the final stage shows the total runtime.

### Changed

- `course_video_to_notes.py`: added `run_stream()` and `_fmt_dur()`; transcription and OCR now use `run_stream()`; `process()` tracks timing for all three stages.
- `scripts/transcribe_funasr.py`: added `_progress_bar()`; transcription loop uses progress bar; stdout reconfigured.
- `scripts/video_frames_ocr.py`: added `_progress_bar()`; OCR and GLM loops use progress bar; stdout reconfigured.
- Wizard regression: 31 tests pass.

## [0.6.5] - 2026-08-10
_Course name rules added to the wizard, question order rearranged._

### Added

- Question 6 course name rules: three options stored in config, applied to all subsequent videos. Previously the course name was auto-inferred by `detect_parts()` with no user choice.
  - A. Auto-detect (default): inferred from path/filename, falls back to the containing folder name.
  - B. Fixed course name: all videos grouped under one course; enter the name, preview the path, and confirm.
  - C. Source folder name: use the video's containing folder name as the course.
  - Each option shows a specific path preview after selection; press N to reselect.
- Config persistence: DEFAULT_CONFIG adds `course_rule` (auto/fixed/folder) and `course_fixed`, passed via environment variables.
- Main script application: `process()` overrides the course after `detect_parts` based on the rule.
- Naming preview linkage: the course name in the naming preview follows the course name rule.
- Closing checklist linkage: `_print_summary` shows the course name source.

### Changed

- Question order rearrangement: the three note-structure questions (storage root, course name, naming) are now consecutive, with the two intermediate-artifact questions moved to the end.
- `wizard.py`: added `_ask_course_rule()`; `_preview_naming()` adds `course_txt` parameter; `_ask_naming()` follows the course name rule; run_wizard swaps questions 6/7 with 8/9.
- `course_video_to_notes.py`: main() passes `COURSE_RULE`/`COURSE_FIXED` environment variables; `process()` applies the rule.

## [0.6.4] - 2026-08-10
_Path preview and confirmation for storage root and naming questions._

### Fixed

- Question 5 default location not transparent: selecting "use default directory" now shows the specific absolute path preview before continuing.
- Question 8 naming has no path feedback: after selecting a naming rule, the full final path is now displayed for confirmation (e.g. `course/lecture/NN_XX_X_section.md` or `prefix_section.md`).
- Question 8 empty prefix: submitting an empty custom prefix now shows a prompt and returns to reselection.

### Changed

- Added `_default_root()`: automatically derives the default root directory (same logic as the main script's project root, going up 3 levels).
- Added `_ask_storage_root()` / `_ask_naming()`: unified "preview, confirm, N to reselect" interaction.
- `_preview_storage()` enhanced: outputs a storage structure preview with specific absolute paths.
- Added `_preview_naming()`: shows an example of the final note file path based on the naming rule.
- Main script naming wiring (`NOMENCLATURE` environment variable) unchanged, no regression.

## [0.6.3] - 2026-08-10
_Note naming rules enhanced._

### Added

- Question 8 custom naming: new option C "custom prefix" generates `prefix_section.md`.
- Naming config wiring: the wizard's naming config (default/simple/custom) is passed to the main script via environment variables; `process()` prompts to name notes according to the selected rule.

## [0.6.2] - 2026-08-10

_GLM error classification, subtitle-to-JSON extraction, and a cleaning hook placeholder._

### Added

- GLM error classification: test failures now distinguish 401/403 (invalid key), 400/404 (wrong model name), and network errors (retry), each with a clear message instead of a generic "model name incorrect" warning.
- Subtitle track extraction to JSON: `extract_subtitle_to_json()` detects embedded subtitle tracks, extracts them via ffmpeg, and parses them into a JSON structure matching ASR output (confidence 0.99), skipping audio transcription for better accuracy and lower cost.
- Cleaning hook placeholder: `clean_transcript_hook()` is reserved for future integration with a cleaning tool to remove noise from JSON output. Currently returns False and does not affect existing workflows.

### Changed

- Transcription output is now unified as JSON (with timestamps and confidence), regardless of whether the source is audio ASR or video subtitles.
- SRT files are now export-only review artifacts, generated from JSON.
- The cleaning target is JSON (the data source), not SRT (the display format).

## [0.6.1] - 2026-08-10

_Interaction experience fixes._

### Fixed

- Duplicate "default" label: the option text "开启（默认，推荐）" conflicted with the auto-marked default; changed to "开启（推荐）".
- Storage confirmation N not returning to re-fill: selecting N fell back to default directly; now returns to the re-fill path (re-enter after N, Enter to fall back to default).
- GLM test failure not returning: failures exited immediately; now loops for retry (re-enter key/model or exit).
- Cache path misalignment: after confirming a custom root, the cache still landed in the default location; verified that the `global` override in main() correctly follows the selection (after confirming with Y, cache is stored under the custom root).

## [0.6.0] - 2026-08-10

_GLM configuration enhancements, course classification, storage preview, and failure handling._

### Added

- GLM configuration display with three choices: when already configured, shows provider/model/endpoint; A use current / B change provider/model / C change model only.
- Provider switching: preset Zhipu/Alibaba/Baidu/OpenAI plus custom endpoint, with key, model name, and connection test required before saving.
- Model-only switching: preserves provider/endpoint/key, prompts for a new model name with a test gate (no change on failure).
- Multi-provider persistence: `.env` now includes `GLM_MODEL` and `GLM_PROVIDER` fields; `glm_vision.py` reads custom provider/model from `.env`.
- Course classification with 4 options: when `detect_parts` fails to identify, offers A parent directory name / B custom / C system recommendation / D uncategorized course, with full path preview and confirmation.
- `detect_parts` parent directory fallback: no longer defaults to a hardcoded course name; uses the video's parent directory name as the course.
- Storage root path preview: after input, displays the full notes/video/cache structure with confirmation (Y/N/invalid re-fill).
- GLM failure handling: content-sensitive errors (400) do not retry and offer per-frame choices (skip/stop/retry); network errors retry 3 times then offer choices; no longer exits via `sys.exit`, preserving processed items and marking unprocessed ones while the flow continues.
- Real-time progress: transcription shows "segment N/total + time + %"; OCR shows "frame N/total + %".

### Fixed

- Missing `import re` in wizard: `ask_course_classification` used `re` without importing it; added the import.
- `detect_parts` course fallback regression: after changing the default to empty, the sample course path could not be resolved; enhanced directory name recognition with parent directory fallback as a safety net.
- Duplicate "default" label: option text mixed "（默认）" with the auto-marked default; unified to use the auto-marked default, with text showing only "（推荐）".

## [0.5.0] - 2026-08-10

_Dynamic path resolution and storage configuration wizard._

### Added

- Dynamic path derivation: BASE is the script's directory, project root is its parent, and cache/notes directories are derived relatively; the script automatically follows migrations or drive changes without hardcoded absolute paths.
- Custom root directory: the `NOTES_ROOT` environment variable overrides the default root; only the outermost path needs to be specified, and the inner structure (`NoteBooks/`, `_转写缓存/`, `课程/第XX讲_标题/`) is automatically fixed.
- Wizard storage questions 5-8: four new prompts — storage root (default/custom), intermediate artifact cleanup (keep/trim/full clean), cache location (standalone/with notes), and naming rules (default/section name only).
- Storage configuration persistence: save/load now includes storage fields, with backward compatibility for older configs (missing fields are auto-filled with defaults).

### Fixed

- Missing `global` in main(): overriding project root/cache/notes directories in main() created local variables that did not affect the globals used by process(); added `global` declaration so custom root directories take effect.
- Lecture number parsing failure on real paths: directory names like `第02讲_标题` (with underscores) did not match `isdigit()`, causing the lecture number to fall back to 00; now backfills from the filename via regex (`2-1` → lecture `02`).
- `OCR_INTERVAL` read timing: the value was fixed at module load time (0.5), so the wizard setting of 1.0 in main() had no effect; process() now reads the environment variable at call time.

## [0.4.0] - 2026-08-10

_Workflow capability upgrade — a systematic overhaul of the transcription workflow based on a survey of 200 transcription repositories._

### Added

- **Preemptive hotword injection**: FunASR upgraded 1.4.0 → 1.4.1; target words in `corrections.json` are now applied as model-level `hotword=` decoding bias, improving recognition at the source rather than correcting after the fact
- **Confidence field**: transcription JSON segments/sentences now carry a `confidence` field (heuristic: fragmentation / concatenation / repetition / length); low-confidence segments can be flagged for manual review
- **SRT subtitle export**: .srt files are exported automatically after transcription, enabling review, clipping, and playback
- **Note spec patch**: `note_style_spec.md` gains importance rules, [unclear] rules, three-part sectioning, and layered chapter generation (outline first, then write in layers)
- **Enhanced spoken-language normalization**: graded cleanup of repeated words — meaningless fillers are removed while emphatic repetition is preserved
- **Adaptive frame budget**: the frame extraction cap now scales with video duration (100 min → 12000 frames) instead of a fixed 6000-frame cutoff for long videos
- **GLM retry on failure**: keyframe GLM calls retry automatically up to 3 times; if still failing, the run stops and waits for handling — never silently skipped
- **Dependency precheck**: new `--precheck` flag at entry checks ffmpeg / ffprobe / rapidocr and reports errors with locations when missing
- **Denoise toggle + auto-detection**: ffmpeg energy analysis auto-detects noise level (DENOISE=auto/on/off); noisy material triggers an automatic warning
- **Audio rebuild cache**: audio rebuild now uses a video fingerprint (size + timestamp) cache; previously repaired videos are reused directly without re-repair
- **Transcription config wizard**: new `wizard.py` interactive wizard (deep-read / fast + frame extraction + GLM multi-provider config + speakers); batch mode remembers settings; `--no-wizard` skips it
- **Subtitle auto-detection**: new `detect_subtitle_track()` probes embedded subtitle tracks; when subtitles exist they take priority and OCR drops to 5s intervals for charts only
- **Batch parallelism**: new `--parallel N` for multi-process parallel transcription (off by default; deep-read mode uses serial)

### Fixed

- **Confidence misjudgment**: isolated single-letter regex misjudged normal articles (the "a" in "is a") → now requires two consecutive isolated single letters
- **GBK decode crash**: ffmpeg volumedetect output contained non-UTF-8 bytes → added `encoding="utf-8", errors="replace"`
- **Noise threshold misjudgment**: clean lecture audio (mean=-23.6) was misjudged as noisy → threshold -28 → -18, dynamic range 42
- **Wizard emoji crash**: checkmark/cross symbols triggered UnicodeEncodeError in GBK terminals → switched to ASCII characters + stdout reconfigure
- **English concatenation residue**: SenseVoice syllable-level splits ("O kay" → "Okay") → added `_SENSEVOICE_SPLITS` dictionary (50+ words) and `merge_sensevoice_splits()`, without breaking normal articles (e.g. "a few")
- **OCR scene integration**: with `OCR_INTERVAL=scene`, the smart_frame branch passed `scene` as a fixed interval to `--interval`, causing an error → refactored OCR parameter logic (scene / fixed / subtitle combinations now route correctly)

## [0.3.0] - 2026-08-09

_A full repair pass over the transcription workflow following a complete self-check._

### Added

- **Automatic audio rebuild**: when a corrupted AAC stream is detected, the tool automatically probes decodable segments at 60s intervals and concatenates a complete audio track. In testing, a corrupted video was rebuilt to 218s in 1 second (more complete than the 205s manual splice)
- **Unified naming**: course directory = `01-sample-course`, cache lecture = `lecture-03`, note lecture = `lecture-03_Minimum Edit Distance`, section = `source_data_3-1_title` (lecture-section without zero-padding)

### Fixed

- **Audio corruption misjudgment**: the audio duration check returned True when a corrupted wav could not be read (misjudged as consistent), skipping audio rebuild → now returns False when the wav is unreadable (ad≤0), triggering automatic rebuild
- **Concatenation reliability**: audio rebuild used `-c copy` (no re-encoding) for segment splicing, which can fail on segments with abnormal headers → now re-encodes when splicing (`-ar 16000 -ac 1` unified parameters)
- **Unclear OCR truncation message**: `MAX_FRAMES=6000` gave a vague message when truncating long videos → now states clearly "approximately XX minutes of video truncated, increase MAX_FRAMES"
- **Lecture title mapping**: script lecture name without title vs note directory name with title caused videos to be copied into the wrong directory layer → added `LECTURE_TITLES` mapping and `lecture_note_name()`: cache uses the short form, notes use the full title
- **Resume misjudgment**: JSON generated from corrupted audio (low coverage) was misjudged as complete → now validates JSON coverage (≥70% required); insufficient coverage triggers re-transcription
- **Extension-less videos skipped**: files without a .mp4 suffix were filtered out by `endswith` → now uses ffprobe format detection

## [0.2.1] - 2026-08-09

_CPU thread-limit optimization._

### Changed

- **OCR thread control**: `RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1)` uses the official config parameters. Result: threads 95 → 3-4, single frame 33% faster (3.03s → 2.02s), CPU usage down 96%. Key point: environment variables (OMP/ORT_*) have no effect on onnxruntime; the official parameters must be used (confirmed by reviewing the GitHub source)

## [0.2.0] - 2026-08-09

_Directory layout rules established._

### Added

- **Directory structure**:

  ```
  notes/course/lecture_XX_title/        ← notes flat at top level + source-data subfolder (videos only)
  transcription_cache/course/lecture_XX/source_data_XX_X/   ← intermediate products (wav + json + visual.txt)
  ```

- **Quality-check rules**: after each transcription, check ① audio vs video duration consistency ② transcription quality ③ frame OCR/GLM ④ note format
- **Lecture title mapping table**: a mapping table was built for the sample course (23 lectures)

## [0.1.0] - 2026-08-08

_Initial pipeline setup._

### Added

- **Main script**: created `course_video_to_notes.py` (local version, online video download removed, reads local mp4 directly)
- **Reused existing engines**: `transcribe_funasr.py` (SenseVoice auto Chinese/English) / `video_frames_ocr.py` (OCR + GLM) / `glm_vision.py`
- **Default config**: OCR at 2 fps (OCR_INTERVAL=0.5) · GLM on keyframes only · Chinese notes · Feynman 6/4/3 · keep transcription appendix
- **Duration check**: warns when audio duration < 80% of video
- **--job batch**: pass a video list via JSON file to avoid command-line quoting issues

## [0.0.x] - 2026-08-08

_Pitfall fixes from the first lecture run._

### Fixed

- **Missing audio**: AAC stream corrupted (330-563s undecodable); manually spliced segments 0-330 + 600-771 and re-transcribed
- **ffmpeg AAC error**: returned non-zero but wav succeeded → now checks whether the wav was generated instead of the return code
- **GBK crash**: `run()` read subprocess output as UTF-8 (the original default GBK crashed on Chinese)
- **Resume**: skip when json/visual exist (judged by file existence, not by counter)

Known limitations:

- `MAX_FRAMES=6000` corresponds to 2 fps × 50 minutes; long videos will have frames truncated (WARN shown, adjustable)
- Audio rebuild re-runs on every corruption (overwriting rebuild.wav); acceptable in resume scenarios but not optimal
- The lecture title mapping currently covers only the sample course; other courses need to be added
