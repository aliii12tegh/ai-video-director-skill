---
name: ai-video-director
description: Speech-driven AI video editing skill (v2) that turns raw talking-head footage into studio-grade videos. Automatically trims silences and retakes, replaces plain room backgrounds with custom studio/office scenes using high-quality human matting, and composites synced image or text overlays via FFmpeg.
---

# AI Video Director Skill (v2)

## Overview

This skill lets an AI agent edit raw talking-head videos directly from **what the speaker says**. It extracts word-level timestamps using `faster-whisper`, removes dead air and retakes, optionally swaps plain backgrounds into realistic studio or office environments using `rembg` (`u2net_human_seg` + alpha matting), and renders the final cut with synced visual overlays via `FFmpeg`.

## Prerequisites

- Python 3.10+
- `ffmpeg` available in `PATH`
- Dependencies from `requirements.txt` (`pip install -r requirements.txt`)

## Workflow

### Step 1: Transcribe & Detect Speech Segments
Run `scripts/transcribe_and_cut.py` on the raw footage to produce word-level timestamps and silence-trimmed cut ranges:

```bash
python scripts/transcribe_and_cut.py --input raw_video.mp4 --output work/transcript.json --model base
```

### Step 2: Optional Background Replacement (v2)
If the user requests a new background (e.g., studio desk, modern office, workshop), run `scripts/swap_background.py` before rendering cuts, and point `source_video` in `edit_plan.json` to `work/swapped.mp4`:

```bash
python scripts/swap_background.py --input raw_video.mp4 --background assets/studio_bg.jpg --output work/swapped.mp4 --blur 7
```

### Step 3: Build `work/edit_plan.json`
Inspect `work/transcript.json` and refine:
1. **`source_video`**: Set to `work/swapped.mp4` if background swap was run, otherwise `raw_video.mp4`.
2. **`cuts`**: Start from `suggested_cuts` and drop any false starts, filler sentences, or retakes.
3. **`overlays`**: Map spoken keywords (e.g., *"this water bottle"*, *"3 key benefits"*) to either an `image` overlay or a `text` callout synced to the post-cut timeline.

### Step 4: Render Final Video
Execute `scripts/render_video.py` to cut, concatenate, apply overlays, and normalize audio to `-14 LUFS`:

```bash
python scripts/render_video.py --plan work/edit_plan.json --output final_video.mp4
```

## Guardrails
- **Non-destructive:** Never overwrite the original `raw_video.mp4`.
- **Graceful fallback:** If background replacement or an image overlay asset fails, fall back cleanly to the original footage or a text callout rather than aborting.
- **Sync accuracy:** Keep overlay timestamps aligned within `±0.2s` of the spoken trigger phrase on the post-cut timeline.
