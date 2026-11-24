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
