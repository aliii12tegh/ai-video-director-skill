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
```

### 3. Run
```bash
# Step 1: Transcribe and detect cuts
python scripts/transcribe_and_cut.py --input raw_video.mp4 --output work/transcript.json

# Step 2: Create or generate work/edit_plan.json (see examples/sample_edit_plan.json)

# Step 3: Render final video
python scripts/render_video.py --plan work/edit_plan.json --output final_video.mp4
```

## Roadmap

- **v1 (Current):** Local speech-driven silence cutting, JSON edit plans, and FFmpeg image/text overlays.
- **v2 (Planned):** Automated background matting & studio/office scene replacement (`rembg` / Robust Video Matting).
- **v3 (Planned):** Modular Video-to-Video (V2V) export for outfit changes and headwear overlays via ComfyUI / API backends.

## License

MIT License — see [LICENSE](LICENSE) for details.
