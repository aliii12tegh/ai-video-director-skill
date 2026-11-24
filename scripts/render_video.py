#!/usr/bin/env python3
"""Render final edited video from an edit_plan.json using FFmpeg."""

import argparse
import json
import subprocess
from pathlib import Path

POSITION_MAP = {
    "top_left": ("40", "40"),
    "top_right": ("W-w-40", "40"),
    "center": ("(W-w)/2", "(H-h)/2"),
    "bottom_left": ("40", "H-h-80"),
    "bottom_right": ("W-w-40", "H-h-80"),
    "bottom_center": ("(W-w)/2", "H-h-120"),
}


def escape_drawtext(text: str) -> str:
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def run_ffmpeg(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\n{result.stderr}")


def main():
    parser = argparse.ArgumentParser(description="Render edited video from edit_plan.json")
    parser.add_argument("--plan", required=True, help="Path to edit_plan.json")
    parser.add_argument("--output", required=True, help="Path to final MP4 output")
    args = parser.parse_args()

    plan_path = Path(args.plan)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))

    source = Path(plan["source_video"])
    if not source.exists():
        raise FileNotFoundError(f"Source video not found: {source}")

    cuts = plan.get("cuts", [])
    if not cuts:
        raise ValueError("edit_plan.json must contain at least one entry in 'cuts'.")

    overlays = plan.get("overlays", [])
    inputs = ["-i", str(source)]
    filter_parts = []

    # 1. Trim and concatenate cuts
    concat_inputs = []
    for idx, cut in enumerate(cuts):
        s, e = cut["start"], cut["end"]
        filter_parts.append(f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[v{idx}]")
        filter_parts.append(f"[0:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS[a{idx}]")
        concat_inputs.append(f"[v{idx}][a{idx}]")

    filter_parts.append(
        f"{''.join(concat_inputs)}concat=n={len(cuts)}:v=1:a=1[vbase][abase]"
    )

    current_v = "[vbase]"
    next_input_idx = 1

    # 2. Apply image and text overlays
    for idx, ov in enumerate(overlays):
        ov_type = ov.get("type", "text")
        start, end = ov["start"], ov["end"]
        pos = ov.get("position", "top_right")
        out_v = f"[vov{idx}]"

        if ov_type == "image":
            asset = Path(ov.get("asset_path", ""))
            if not asset.exists():
                print(f"[warn] Missing image asset '{asset}', skipping overlay #{idx}")
                continue
            inputs.extend(["-i", str(asset)])
            scale_w = int(ov.get("scale_width", 320))
            x_expr, y_expr = POSITION_MAP.get(pos, POSITION_MAP["top_right"])
            filter_parts.append(f"[{next_input_idx}:v]scale={scale_w}:-1[img{idx}]")
            filter_parts.append(
                f"{current_v}[img{idx}]overlay=x={x_expr}:y={y_expr}:enable='between(t,{start},{end})'{out_v}"
            )
            next_input_idx += 1
            current_v = out_v

        elif ov_type == "text":
            text = escape_drawtext(ov.get("text", ""))
            if not text:
                continue
            x_expr = "(w-text_w)/2"
            y_expr = "h-text_h-100" if "bottom" in pos else "80"
            filter_parts.append(
                f"{current_v}drawtext=text='{text}':fontcolor=white:fontsize=42:"
                f"box=1:boxcolor=black@0.65:boxborderw=16:"
                f"x={x_expr}:y={y_expr}:enable='between(t,{start},{end})'{out_v}"
            )
            current_v = out_v

    # 3. Normalize audio loudness (-14 LUFS)
    filter_parts.append("[abase]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex",
        ";".join(filter_parts),
        "-map",
        current_v,
        "-map",
        "[aout]",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "20",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        str(output_path),
    ]

    print(f"Rendering {output_path} ...")
    run_ffmpeg(cmd)
    print(f"Done! Saved final video to {output_path}")


if __name__ == "__main__":
    main()
