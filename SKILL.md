---
name: ai-video-director
description: Speech-driven AI video editing skill (v3) built to run natively inside Gemini, Claude, or local terminals with zero pip installs required. Automatically trims silences using FFmpeg, analyzes spoken cues to insert synced image or text overlays, and supports optional local background replacement.
---

# AI Video Director Skill (v3 — Sandbox & Cloud Ready)

## Overview

This skill turns raw talking-head footage into tight, engaging videos directly from **what the speaker says**. In **v3**, the default pipeline requires **zero Python package installations**—it uses only the Python standard library + `FFmpeg`, making it ready to run directly inside Gemini, Claude, or any sandboxed agent environment.

## Core Workflow (Zero-Dependency Mode — Default)

### Step 1: Detect Speech & Trim Silences
Run `scripts/auto_cut_ffmpeg.py` to automatically detect silence gaps and generate clean `suggested_cuts`:

```bash
python3 scripts/auto_cut_ffmpeg.py --input raw_video.mp4 --output work/cuts.json --noise -30dB --min-silence 0.5
```

### Step 2: Analyze Speech & Build `work/edit_plan.json`
Use your native multimodal understanding of the video (or user-provided transcript) to:
1. Review `suggested_cuts` from `work/cuts.json` and remove any false starts or retakes.
2. Identify key spoken visual cues (products, technical terms, benefits, steps) and map them to `overlays` (`image` or `text`) synced to the **post-cut timeline**.

Write `work/edit_plan.json`:
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
      "asset_path": "assets/overlay.png",
      "start": 3.5,
      "end": 6.0,
      "position": "top_right",
      "scale_width": 320
    },
    {
      "type": "text",
      "text": "Key Takeaway",
      "start": 8.5,
      "end": 11.0,
      "position": "bottom_center"
    }
  ]
}
```

### Step 3: Render Final Video
Run `scripts/render_video.py` to apply cuts, composite overlays, normalize audio (`-14 LUFS`), and export the final MP4:

```bash
python3 scripts/render_video.py --plan work/edit_plan.json --output final_video.mp4
```

## Optional Local-Only Enhancements
When running on a local machine with `requirements.txt` installed:
- **Word-level transcription:** Use `scripts/transcribe_and_cut.py` (`faster-whisper`) instead of Step 1.
- **Background swap:** Run `scripts/swap_background.py` (`rembg` + `u2net_human_seg`) before Step 3 and point `source_video` to `work/swapped.mp4`.

## Guardrails
- **Sandbox first:** Always default to `auto_cut_ffmpeg.py` + `render_video.py` inside chat sandboxes so the skill never fails on missing pip packages.
- **Non-destructive:** Never overwrite `raw_video.mp4`.
- **Graceful fallback:** If an `image` overlay file is missing, skip it or fall back to a clean `text` callout.
