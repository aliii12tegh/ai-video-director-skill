#!/usr/bin/env python3
"""Zero-dependency silence detector using FFmpeg silencedetect (Sandbox/Gemini/Claude ready)."""

import argparse
import json
import re
import subprocess
from pathlib import Path


def get_duration(video_path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())


def detect_speech_cuts(
    video_path: Path, noise_db: str = "-30dB", min_silence: float = 0.5, padding: float = 0.1
) -> tuple[float, list[dict]]:
    duration = get_duration(video_path)
    cmd = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-af",
        f"silencedetect=noise={noise_db}:d={min_silence}",
        "-f",
        "null",
        "-",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    stderr = res.stderr

    silences = []
    current_start = None
    for line in stderr.splitlines():
        m_start = re.search(r"silence_start:\s*([0-9.]+)", line)
        if m_start:
            current_start = float(m_start.group(1))
        m_end = re.search(r"silence_end:\s*([0-9.]+)", line)
        if m_end and current_start is not None:
            silences.append((current_start, float(m_end.group(1))))
            current_start = None
    if current_start is not None:
        silences.append((current_start, duration))

    # Invert silences into speech ranges
    cuts = []
    cursor = 0.0
    for s_start, s_end in silences:
        seg_start = max(0.0, round(cursor - padding, 3))
        seg_end = min(duration, round(s_start + padding, 3))
        if seg_end - seg_start > 0.15:
            if cuts and seg_start <= cuts[-1]["end"]:
                cuts[-1]["end"] = max(cuts[-1]["end"], seg_end)
            else:
                cuts.append({"start": seg_start, "end": seg_end})
        cursor = s_end

    if cursor < duration:
        seg_start = max(0.0, round(cursor - padding, 3))
        seg_end = round(duration, 3)
        if seg_end - seg_start > 0.15:
            if cuts and seg_start <= cuts[-1]["end"]:
                cuts[-1]["end"] = max(cuts[-1]["end"], seg_end)
            else:
                cuts.append({"start": seg_start, "end": seg_end})

    if not cuts:
        cuts = [{"start": 0.0, "end": round(duration, 3)}]

    return round(duration, 3), cuts


def main():
    parser = argparse.ArgumentParser(description="Detect non-silent speech cuts using FFmpeg only.")
    parser.add_argument("--input", required=True, help="Path to source video")
    parser.add_argument("--output", required=True, help="Path to output JSON")
    parser.add_argument("--noise", default="-30dB", help="Silence threshold (default: -30dB)")
    parser.add_argument("--min-silence", type=float, default=0.5, help="Min silence duration in seconds")
    parser.add_argument("--padding", type=float, default=0.1, help="Padding around speech in seconds")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input video not found: {input_path}")

    duration, cuts = detect_speech_cuts(input_path, args.noise, args.min_silence, args.padding)
    data = {
        "source_video": str(input_path),
        "duration": duration,
        "suggested_cuts": cuts,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Detected {len(cuts)} speech segments (duration: {duration}s) -> {out_path}")


if __name__ == "__main__":
    main()
