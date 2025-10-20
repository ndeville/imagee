from pathlib import Path
import re
import xml.etree.ElementTree as ET

try:
    import cairosvg
except ImportError as e:
    raise ImportError(
        "This function requires the 'cairosvg' package.\n"
        "Install it with: pip install cairosvg"
    ) from e


def _parse_length_to_px(value: str, dpi: float = 96.0) -> float:
    """
    Convert an SVG length string (e.g., '10cm', '100px', '2in', '12mm', '72pt', '6pc')
    to pixels at the given DPI. If unitless, treat as pixels per SVG spec.
    """
    if value is None:
        return None
    s = value.strip().lower()
    m = re.fullmatch(r"([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)([a-z%]*)", s)
    if not m:
        return None
    num, unit = float(m.group(1)), m.group(2)
    if unit in ("", "px"):
        return num
    if unit == "in":
        return num * dpi
    if unit == "cm":
        return num * (dpi / 2.54)
    if unit == "mm":
        return num * (dpi / 25.4)
    if unit == "pt":  # 1 pt = 1/72 in
        return num * (dpi / 72.0)
    if unit == "pc":  # 1 pc = 12 pt
        return num * (dpi / 6.0)
    # Percent and unknown units aren't well-defined here
    return None


def _intrinsic_svg_size_px(svg_path: Path, dpi: float = 96.0) -> tuple[float, float]:
    """
    Determine the intrinsic width/height of an SVG in pixels.
    Follows: https://www.w3.org/TR/SVG11/coords.html#ViewportSpace
    """
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Handle namespaces safely
    width_attr = root.get("width")
    height_attr = root.get("height")
    viewBox_attr = root.get("viewBox")

    w_px = _parse_length_to_px(width_attr, dpi) if width_attr else None
    h_px = _parse_length_to_px(height_attr, dpi) if height_attr else None

    # If both width/height are present and valid -> use them
    if w_px and h_px:
        return float(w_px), float(h_px)

    # Else, if viewBox exists, use its aspect ratio with whichever dimension is available
    if viewBox_attr:
        try:
            _, _, vb_w, vb_h = map(float, viewBox_attr.strip().replace(",", " ").split())
            if vb_w > 0 and vb_h > 0:
                if w_px and not h_px:
                    return float(w_px), float(w_px * (vb_h / vb_w))
                if h_px and not w_px:
                    return float(h_px * (vb_w / vb_h)), float(h_px)
                if not w_px and not h_px:
                    # No explicit size: use viewBox in px at 1:1
                    return float(vb_w), float(vb_h)
        except Exception:
            pass

    # Fallback: if we have one dimension, mirror it (square); else default 300x150 like browsers often do
    if w_px and not h_px:
        return float(w_px), float(w_px)
    if h_px and not w_px:
        return float(h_px), float(h_px)
    return 300.0, 150.0


def svg_to_png_max_5cm_by_2cm(svg_path: str, dpi: float = 96.0) -> str:
    """
    Convert an SVG to PNG at 96 dpi, preserving aspect ratio, scaled to fit
    within a max width of 5 cm and max height of 2 cm.

    - Input: path to .svg
    - Output: path to generated .png (same directory, same basename)
    """
    svg_path = Path(svg_path).expanduser().resolve()
    if not svg_path.exists():
        raise FileNotFoundError(f"SVG not found: {svg_path}")

    # Max box (in pixels @ 96 dpi)
    max_w_px = 5.0 * (dpi / 2.54)   # 5 cm
    max_h_px = 2.0 * (dpi / 2.54)   # 2 cm

    orig_w_px, orig_h_px = _intrinsic_svg_size_px(svg_path, dpi=dpi)

    # Scale to fit within max box, preserving aspect ratio
    scale = min(max_w_px / orig_w_px, max_h_px / orig_h_px)
    out_w = max(1, int(round(orig_w_px * scale)))
    out_h = max(1, int(round(orig_h_px * scale)))

    out_path = svg_path.with_suffix(".png")

    # Render with CairoSVG
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(out_path),
        output_width=out_w,
        output_height=out_h,
        dpi=dpi,
    )

    return str(out_path)

svg_to_png_max_5cm_by_2cm("/Users/nic/tmp/logos/ppt/media/image3.svg")