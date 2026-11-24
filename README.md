# AI Video Director Skill

An open-source, speech-driven AI Agent Skill that turns raw talking-head footage into clean, tight videos using `faster-whisper` and `FFmpeg`.

## What v1 Does

- **Word-Level Transcription:** Extracts exact timestamps for every spoken word locally with `faster-whisper`.
- **Automatic Silence & Retake Cutting:** Removes dead air and pauses based on speech activity.
- **Synced Visual Overlays:** Inserts PNG/JPG graphics or styled text callouts at the exact moment a keyword is spoken.
- **Broadcast Audio Loudness:** Normalizes final audio to `-14 LUFS`.

## Quick Start

### 1. Prerequisites
- Python 3.10+
- [FFmpeg](https://ffmpeg.org/download.html) installed in your system `PATH`

### 2. Install
```bash
git clone [https://github.com/aliii12tegh/ai-video-director-skill.git](https://github.com/aliii12tegh/ai-video-director-skill.git)
cd ai-video-director-skill
pip install -r requirements.txt
