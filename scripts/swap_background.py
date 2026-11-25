#!/usr/bin/env python3
"""High-quality video background replacement using rembg (u2net_human_seg) + OpenCV + FFmpeg."""

import argparse
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import new_session, remove


def prepare_background(bg_path: Path, width: int, height: int, blur_radius: int) -> np.ndarray:
    """Load, center-crop/resize to match video dimensions, and optionally blur the background."""
    bg = cv2.imread(str(bg_path))
    if bg is None:
        raise FileNotFoundError(f"Could not read background image: {bg_path}")

    bg_h, bg_w = bg.shape[:2]
    target_ratio = width / height
    bg_ratio = bg_w / bg_h

    if bg_ratio > target_ratio:
        new_w = int(bg_h * target_ratio)
        offset = (bg_w - new_w) // 2
        bg = bg[:, offset : offset + new_w]
    else:
        new_h = int(bg_w / target_ratio)
        offset = (bg_h - new_h) // 2
        bg = bg[offset : offset + new_h, :]

    bg = cv2.resize(bg, (width, height), interpolation=cv2.INTER_LANCZOS4)

    if blur_radius > 0:
        k = blur_radius if blur_radius % 2 == 1 else blur_radius + 1
        bg = cv2.GaussianBlur(bg, (k, k), 0)

    return bg.astype(np.float32)


def main():
    parser = argparse.ArgumentParser(description="High-quality AI background swap for talking-head videos.")
    parser.add_argument("--input", required=True, help="Path to source video")
    parser.add_argument("--background", required=True, help="Path to studio/office background image")
    parser.add_argument("--output", required=True, help="Path to output MP4 with replaced background")
    parser.add_argument("--model", default="u2net_human_seg", help="rembg model (default: u2net_human_seg)")
    parser.add_argument("--blur", type=int, default=7, help="Background Gaussian blur for natural depth (0 to disable)")
    parser.add_argument("--no-alpha-matting", action="store_true", help="Disable alpha matting for faster processing")
    args = parser.parse_args()

    input_path = Path(args.input)
    bg_path = Path(args.background)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input video not found: {input_path}")

    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    bg_float = prepare_background(bg_path, width, height, args.blur)
    session = new_session(args.model)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        silent_video = Path(tmpdir) / "silent_swapped.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(silent_video), fourcc, fps, (width, height))

        frame_idx = 0
        print(f"Processing {total_frames} frames ({width}x{height} @ {fps:.2f}fps) using {args.model}...")

        while True:
            ret, frame_bgr = cap.read()
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)

            # Extract high-quality alpha matte for the speaker
            mask = remove(
                pil_img,
                session=session,
                only_mask=True,
                alpha_matting=not args.no_alpha_matting,
                alpha_matting_foreground_threshold=240,
                alpha_matting_background_threshold=15,
                alpha_matting_erode_size=8,
            )

            alpha = np.array(mask, dtype=np.float32) / 255.0
            # Light feathering to eliminate harsh edges
            alpha = cv2.GaussianBlur(alpha, (3, 3), 0)
            alpha_3ch = alpha[:, :, np.newaxis]

            fg_float = frame_bgr.astype(np.float32)
            composited = (fg_float * alpha_3ch + bg_float * (1.0 - alpha_3ch)).astype(np.uint8)
            writer.write(composited)

            frame_idx += 1
            if frame_idx % 30 == 0 or frame_idx == total_frames:
                print(f"  Frame {frame_idx}/{total_frames}")

        cap.release()
        writer.release()

        # Re-encode to H.264 and mux original audio back using FFmpeg
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(silent_video),
            "-i",
            str(input_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0?",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "19",
            "-c:a",
            "copy",
            "-shortest",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg audio mux failed:\n{result.stderr}")

    print(f"Done! Saved background-swapped video to {output_path}")


if __name__ == "__main__":
    main()
