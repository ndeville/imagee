#!/usr/bin/env python3
"""
Make an image that drops into a 16:9 PowerPoint slide at EXACTLY 33.87 cm × 19.05 cm
(= 13.333 in × 7.5 in). On macOS PowerPoint, the reliable mapping is 72 DPI.

Therefore, we must output: 960 × 540 px at 72 DPI.

Usage:
1) Copy an absolute image path (e.g., via Finder: ⌘⌥C).
2) Run this script; it reads the path from the clipboard and writes a new file
   next to the original with suffix _ppt_960x540.jpg (or .png if source has alpha).
3) Insert into PowerPoint via Insert → Picture (not paste) for best consistency.
"""

import os
import sys
from datetime import datetime
from PIL import Image, ImageOps

# Optional decoders (ignore if missing)
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass
try:
    import pillow_avif  # registers on import
except Exception:
    pass

# ---- Constants for the exact PPT physical size on macOS ----
SLIDE_WIDTH_CM  = 33.87
SLIDE_HEIGHT_CM = 19.05
BASE_DPI        = 72                # macOS PowerPoint layout base
TARGET_W_PX     = 960                # 13.333 in × 72 dpi
TARGET_H_PX     = 540                # 7.5 in × 72 dpi
# BASE_DPI        = 96                
# TARGET_W_PX     = 1280                
# TARGET_H_PX     = 720               

VALID_EXTS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.avif', '.heic', '.heif')


def copy_from_clipboard() -> str:
    import subprocess
    out = subprocess.run(["pbpaste"], text=True, stdout=subprocess.PIPE).stdout.strip()
    return out


def has_alpha(pil_image: Image.Image) -> bool:
    if pil_image.mode in ("RGBA", "LA"):
        return True
    if pil_image.mode == "P":  # palette: may have transparency
        return "transparency" in pil_image.info
    return False


def output_path_for(src_path: str, ext: str) -> str:
    base, _ = os.path.splitext(src_path)
    # stamp = datetime.now().strftime('%y%m%d-%H%M%S')
    ext = ext.lower()
    if ext in ("jpeg", "jpg"):
        ext = "jpg"
    # return f"{base}_ppt_960x540_{stamp}.{ext}"
    return f"{base}_ppt.{ext}"


def save_with_dpi(img: Image.Image, dest: str, format_hint: str):
    fmt = "PNG" if dest.lower().endswith(".png") else "JPEG"
    params = {"optimize": True, "dpi": (BASE_DPI, BASE_DPI)}

    if fmt == "JPEG":
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
        params.update({"quality": 90, "progressive": True})
    else:
        # PNG: 'dpi' writes a pHYs chunk via Pillow; many apps honor it.
        pass

    img.save(dest, format=fmt, **params)
    return dest


def main():
    # 1) Read absolute path from clipboard
    # A path argument (Filee action) wins; the clipboard stays the fallback (Alfred).
    src = sys.argv[1] if len(sys.argv) > 1 else copy_from_clipboard()
    if not (src and src.startswith("/") and src.lower().endswith(VALID_EXTS)):
        print(f"❌ Invalid image path from clipboard: {src!r}")
        sys.exit(1)

    # 2) Open, resize/crop to EXACT 960×540
    with Image.open(src) as im:
        out_is_png = has_alpha(im)  # keep transparency if present
        target = ImageOps.fit(im, (TARGET_W_PX, TARGET_H_PX), Image.LANCZOS, centering=(0.5, 0.5))

        # 3) Decide extension: PNG if alpha, else JPG to maximize DPI honor in Office
        dest_ext = "png" if out_is_png else "jpg"
        dest = output_path_for(src, dest_ext)

        # 4) Save at 72 DPI
        save_with_dpi(target, dest, dest_ext)

    # 5) Report
    with Image.open(dest) as test:
        w, h = test.size
        dpi = test.info.get("dpi", ("?", "?"))
    print(f"✅ Wrote: {dest}")
    print(f"   Pixels: {w}×{h} | DPI tag: {dpi} | Expected PPT size: 33.87 cm × 19.05 cm (macOS)")

if __name__ == "__main__":
    main()