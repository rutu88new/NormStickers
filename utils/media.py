import os
import tempfile
from pathlib import Path
from PIL import Image, ImageSequence
import imageio.v2 as imageio
import subprocess

MAX_SIZE = 512

def _resize_to_box(img):
    w, h = img.size
    scale = min(MAX_SIZE / max(w, h), 1.0) if max(w, h) > MAX_SIZE else 1.0
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    return img.resize(new_size, Image.LANCZOS)

def gif_first_frame_to_png(gif_path, out_path):
    im = Image.open(gif_path)
    im = im.convert("RGBA")
    frame0 = Image.new("RGBA", im.size)
    frame0.paste(im, (0, 0), im)
    frame0 = _resize_to_box(frame0)
    frame0.save(out_path, "PNG")

def webp_to_png(src_path, out_path):
    im = Image.open(src_path).convert("RGBA")
    im = _resize_to_box(im)
    im.save(out_path, "PNG")

def image_to_png(src_path, out_path):
    im = Image.open(src_path).convert("RGBA")
    im = _resize_to_box(im)
    im.save(out_path, "PNG")

def make_black_bg_preview(src_path, out_mp4_path, seconds=2):
    # Build a short mp4 preview (black 512x512 background), overlaying a resized RGBA PNG.
    # Requires ffmpeg in PATH.
    tmp_png = None
    try:
        tmp_png = Path(tempfile.mkstemp(suffix=".png")[1])
        if src_path.lower().endswith((".gif",)):
            gif_first_frame_to_png(src_path, tmp_png)
        elif src_path.lower().endswith((".webp", ".png")):
            if src_path.lower().endswith(".webp"):
                webp_to_png(src_path, tmp_png)
            else:
                image_to_png(src_path, tmp_png)
        else:
            image_to_png(src_path, tmp_png)

        cmd = [
            "ffmpeg",
            "-y",
            "-f", "lavfi", "-i", f"color=c=black:s={MAX_SIZE}x{MAX_SIZE}:d={seconds}",
            "-loop", "1", "-i", str(tmp_png),
            "-filter_complex", "[1]scale=w=min(iw,512):h=-1[fg];[0][fg]overlay=(W-w)/2:(H-h)/2",
            "-t", str(seconds),
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(out_mp4_path)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    finally:
        if tmp_png and Path(tmp_png).exists():
            os.remove(tmp_png)

def best_guess_to_png(src_path, out_path):
    ext = Path(src_path).suffix.lower()
    if ext == ".gif":
        gif_first_frame_to_png(src_path, out_path)
    elif ext == ".webp":
        webp_to_png(src_path, out_path)
    else:
        image_to_png(src_path, out_path)
