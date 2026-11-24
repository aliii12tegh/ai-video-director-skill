---
name: ai-video-director
description: Speech-driven AI video editing skill (v1) that turns raw talking-head footage into tight, engaging videos. Automatically transcribes speech with word-level timestamps, trims silences and retakes, and composites synced image or text-callout overlays using FFmpeg.
---

# AI Video Director Skill (v1)

## Overview

This skill lets an AI agent edit raw talking-head videos directly from **what the speaker says**. It extracts word-level timestamps using `faster-whisper`, removes dead air and retakes, identifies spoken visual cues (products, technical terms, key points), and renders the final cut with synced image or text overlays via `FFmpeg`.

## Prerequisites

- Python 3.10+
- `ffmpeg` available in `PATH`
- Python packages from `requirements.txt` (`pip install -r requirements.txt`)

## Workflow

### Step 1: Transcribe & Detect Speech Segments
Run `scripts/transcribe_and_cut.py` on the raw footage to produce word-level timestamps and silence-trimmed cut ranges:

```bash
python scripts/transcribe_and_cut.py --input raw_video.mp4 --output work/transcript.json --model base
```

### Step 2: Build `work/edit_plan.json`
Inspect `work/transcript.json` and refine:
1. **`cuts`**: Start from `suggested_cuts` and drop any false starts, filler sentences, or retakes.
2. **`overlays`**: Map spoken keywords (e.g., *"this water bottle"*, *"3 key benefits"*) to either an `image` overlay (path to a local PNG/JPG) or a `text` callout synced to the post-cut timeline.

Schema example:
```json
{
  "source_video": "raw_video.mp4",
  "cuts": [
    { "start": 0.4, "end": 8.2 },
    { "start": 10.1, "end": 22.5 }
  ],
  "overlays": [
    {
      "type": "image",
      "asset_path": "assets/bottle.png",
      "start": 3.5,
      "end": 6.0,
      "position": "top_right",
      "scale_width": 320
    },
    {
      "type": "text",
      "text": "3 Key Benefits",
      "start": 8.5,
      "end": 11.0,
      "position": "bottom_center"
    }
  ]
}
```

### Step 3: Render Final Video
Execute `scripts/render_video.py` to cut, concatenate, apply overlays, and normalize audio to `-14 LUFS`:

```bash
python scripts/render_video.py --plan work/edit_plan.json --output final_video.mp4
```

## Guardrails
- **Non-destructive:** Never overwrite `source_video`.
- **Graceful fallback:** If an `image` overlay asset is missing on disk, skip or replace it with a `text` callout rather than failing the render.
- **Sync accuracy:** Keep overlay timestamps aligned within `±0.2s` of the spoken trigger phrase on the post-cut timeline.
