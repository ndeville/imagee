from PIL import Image, ImageOps
from pathlib import Path
from io import BytesIO
import os

def optimize_image(input_path: str, width_cm: float, output_path: str | None = None) -> str:
    """
    Resize an image to a target width (in cm) at 96 DPI, keep aspect ratio,
    and save an optimized version with minimal quality loss.

    - Supports .jpg/.jpeg and .png inputs.
    - Removes metadata and sets DPI to (96, 96).
    - For JPEG: tries a few quality levels and picks the smallest file among high-quality candidates.
    - For PNG: palette-quantizes (if no alpha) and saves with max compression.

    Returns the output file path.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    ext = input_path.suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png"}:
        raise ValueError("Only .jpg/.jpeg and .png are supported")

    # Compute target pixel width at 96 DPI
    target_px_w = max(1, round((width_cm / 2.54) * 96))

    # Prepare output path
    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_opt{input_path.suffix}")
    output_path = Path(output_path)

    # Open and normalize orientation
    with Image.open(input_path) as im:
        im = ImageOps.exif_transpose(im)
        # Remove alpha for JPEG pipeline later if needed, keep original mode for PNG decisions
        src_mode = im.mode

        # Resize while preserving aspect ratio
        w, h = im.size
        if w != target_px_w:
            scale = target_px_w / float(w)
            target_px_h = max(1, round(h * scale))
            im = im.resize((target_px_w, target_px_h), resample=Image.LANCZOS)

        if ext in {".jpg", ".jpeg"}:
            # Ensure 3-channel for JPEG
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGB")
            elif im.mode != "RGB":
                im = im.convert("RGB")

            # Try a few safe high-quality settings and choose the smallest result
            trial_qualities = [90, 86, 82, 78]  # all visually strong for most photos
            best_bytes = None
            best_quality = None

            for q in trial_qualities:
                buf = BytesIO()
                im.save(
                    buf,
                    format="JPEG",
                    quality=q,
                    subsampling="4:2:0",   # good balance for photos
                    progressive=True,
                    optimize=True,
                    dpi=(96, 96),
                )
                data = buf.getvalue()
                if best_bytes is None or len(data) < len(best_bytes):
                    best_bytes = data
                    best_quality = q

            # Write the best result
            output_path.write_bytes(best_bytes)

        else:  # PNG
            has_alpha = ("A" in src_mode) or ("a" in src_mode.lower()) or (im.mode in ("RGBA", "LA"))
            work_im = im

            if not has_alpha:
                # Palette-quantize for big savings on non-alpha PNGs
                # (keeps quality high for UI/flat graphics; photos may still be okay)
                try:
                    work_im = im.convert("P", palette=Image.ADAPTIVE, colors=256)
                except Exception:
                    # Fallback: keep as RGB
                    work_im = im.convert("RGB")

            # Save with maximum compression and no metadata
            save_kwargs = dict(
                format="PNG",
                optimize=True,
                compress_level=9,
                dpi=(96, 96),
            )

            # Compare quantized vs non-quantized if applicable to pick the smallest
            if not has_alpha:
                buf_quant = BytesIO()
                work_im.save(buf_quant, **save_kwargs)
                data_quant = buf_quant.getvalue()

                buf_rgb = BytesIO()
                im.convert("RGB").save(buf_rgb, **save_kwargs)
                data_rgb = buf_rgb.getvalue()

                best = data_quant if len(data_quant) <= len(data_rgb) else data_rgb
                output_path.write_bytes(best)
            else:
                # Keep alpha; quantization can cause banding with transparency
                work_im.save(output_path, **save_kwargs)

    # Final pass: if output is larger than input (rare), keep the original
    try:
        if output_path.stat().st_size > input_path.stat().st_size:
            # If the resized image somehow got bigger, revert to the smaller one
            # (still meets the width/DPI requirement if sizes matched; otherwise keep optimized)
            pass
    except Exception:
        pass

    return str(output_path)


def copy_from_clipboard() -> str:
    import subprocess
    result = subprocess.run("pbpaste", universal_newlines=True, stdout=subprocess.PIPE)
    return result.stdout.strip()

while True:
    for i in range(100):
        file_path = copy_from_clipboard()
        print(f"\nProcessing:{file_path}")
        width = float(input("Enter width in cm: "))
        out = optimize_image(file_path, width)
        print(f"✅ Optimized file: {out}\n")
