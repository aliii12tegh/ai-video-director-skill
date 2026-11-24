#!/usr/bin/env python3
"""Transcribe a video with word-level timestamps and suggest silence-trimmed cuts."""

import argparse
import json
from pathlib import Path
from faster_whisper import WhisperModel


def merge_cuts(segments, padding: float, min_gap: float) -> list[dict]:
    """Merge speech segments that are closer than min_gap into clean cut ranges."""
    raw_cuts = []
    for seg in segments:
        start = max(0.0, round(seg["start"] - padding, 3))
        end = round(seg["end"] + padding, 3)
        if raw_cuts and start - raw_cuts[-1]["end"] <= min_gap:
            raw_cuts[-1]["end"] = max(raw_cuts[-1]["end"], end)
        else:
            raw_cuts.append({"start": start, "end": end})
    return raw_cuts


def main():
    parser = argparse.ArgumentParser(description="Transcribe video and detect speech cuts.")
    parser.add_argument("--input", required=True, help="Path to source video file")
    parser.add_argument("--output", required=True, help="Path to output transcript JSON")
    parser.add_argument("--model", default="base", help="Whisper model size (tiny, base, small, medium)")
    parser.add_argument("--device", default="auto", help="Device: auto, cpu, or cuda")
    parser.add_argument("--padding", type=float, default=0.12, help="Seconds of padding around speech")
    parser.add_argument("--min-gap", type=float, default=0.45, help="Minimum silence gap (s) to trigger a cut")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input video not found: {input_path}")

    model = WhisperModel(args.model, device=args.device, compute_type="int8")
    segments_iter, info = model.transcribe(
        str(input_path),
        vad_filter=True,
        word_timestamps=True,
    )

    segments_data = []
    for seg in segments_iter:
        words = [
            {
                "word": w.word.strip(),
                "start": round(w.start, 3),
                "end": round(w.end, 3),
            }
            for w in (seg.words or [])
        ]
        segments_data.append(
            {
                "start": round(seg.start, 3),
                "end": round(seg.end, 3),
                "text": seg.text.strip(),
                "words": words,
            }
        )

    output_data = {
        "source_video": str(input_path),
        "language": info.language,
        "duration": round(info.duration, 3),
        "suggested_cuts": merge_cuts(segments_data, args.padding, args.min_gap),
        "segments": segments_data,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved transcript ({len(segments_data)} segments) to {output_path}")


if __name__ == "__main__":
    main()
