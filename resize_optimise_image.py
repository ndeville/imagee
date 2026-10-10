#!/usr/bin/env python3
import sys
from PIL import Image, ImageOps
import os
from datetime import datetime
import pillow_avif  # Add AVIF support
import pillow_heif  # Add HEIF/HEIC support

# Register HEIF/HEIC with PIL
pillow_heif.register_heif_opener()

from pync import Notifier

def _prepare_format_and_path(input_path, output_path=None, output_format=None):
    """Helper function to handle format and path preparation"""
    if output_format is None:
        output_format = os.path.splitext(input_path)[1].lower().replace('.', '')
    
    # Standardize format names
    if output_format.lower() in ['jpg', 'jpeg']:
        output_format = 'JPEG'
    elif output_format.lower() == 'png':
        output_format = 'PNG'
    elif output_format.lower() == 'avif':
        output_format = 'AVIF'
    elif output_format.lower() in ['heic', 'heif']:
        output_format = 'JPEG'  # Default to JPEG for output if input is HEIC/HEIF
    
    # Create output path if not provided
    if output_path is None:
        timestamp = datetime.now().strftime('%y%m%d-%H%M%S')
        filename = os.path.basename(input_path)
        name, _ = os.path.splitext(filename)
        output_path = f"{name}_{timestamp}_optimized.{output_format.lower()}"
    
    return output_format, output_path

def _save_image(img, output_path, output_format, quality=85):
    """Helper function to save the image with optimization"""
    save_kwargs = {'optimize': True}
    
    # Convert RGBA to RGB if saving as JPEG
    if output_format == 'JPEG' and img.mode == 'RGBA':
        img = img.convert('RGB')
    
    if output_format == 'JPEG':
        save_kwargs['quality'] = quality
    elif output_format == 'AVIF':
        save_kwargs['quality'] = quality
        save_kwargs['speed'] = 6  # Faster encoding, lower compression
    
    img.save(output_path, format=output_format, **save_kwargs)
    return output_path

def process_image_exact(input_path, width, height, output_path=None, 
                       exact_mode_focus='center', output_format=None, quality=85):
    """Process image with exact dimensions"""
    img = Image.open(input_path)
    save_format, _ = _prepare_format_and_path(input_path, None, output_format)
    
    # Resize to exact dimensions with focus point
    if exact_mode_focus == 'center':
        img = ImageOps.fit(img, (width, height), Image.LANCZOS, centering=(0.5, 0.5))
    elif exact_mode_focus == 'top':
        img = ImageOps.fit(img, (width, height), Image.LANCZOS, centering=(0.5, 0.0))
    elif exact_mode_focus == 'bottom':
        img = ImageOps.fit(img, (width, height), Image.LANCZOS, centering=(0.5, 1.0))
    elif isinstance(exact_mode_focus, str) and exact_mode_focus.endswith('%'):
        # Handle percentage value for vertical centering
        try:
            percentage = float(exact_mode_focus.rstrip('%')) / 100
            # Ensure percentage is between 0 and 1
            percentage = max(0, min(1, percentage))
            img = ImageOps.fit(img, (width, height), Image.LANCZOS, centering=(0.5, percentage))
        except ValueError:
            # If percentage conversion fails, default to center
            img = ImageOps.fit(img, (width, height), Image.LANCZOS, centering=(0.5, 0.5))
    else:
        # Default to center if invalid focus point is provided
        img = ImageOps.fit(img, (width, height), Image.LANCZOS, centering=(0.5, 0.5))
    
    # Build output path in same folder with final size suffix if not provided
    if output_path is None:
        output_path = create_output_filename(
            input_path,
            mode="exact",
            output_format=output_format or save_format,
            target_width=img.width,
            target_height=img.height,
        )

    return _save_image(img, output_path, save_format, quality)

def process_image_max(input_path, max_width=None, max_height=None, 
                     output_path=None, output_format=None, quality=85):
    """Process image with maximum dimension constraints without upscaling.

    Only resizes when the input image exceeds the given max_width and/or
    max_height. If the image already fits within the boundaries, its size is
    preserved (format/quality optimization may still occur).
    """
    img = Image.open(input_path)
    save_format, _ = _prepare_format_and_path(input_path, None, output_format)
    
    # Apply max dimension resize (no upscaling)
    if max_width and max_height:
        if img.width > max_width or img.height > max_height:
            img = ImageOps.contain(img, (max_width, max_height), Image.LANCZOS)
    elif max_width:
        if img.width > max_width:
            w_percent = max_width / float(img.width)
            h_size = int(float(img.height) * w_percent)
            img = img.resize((max_width, h_size), Image.LANCZOS)
    elif max_height:
        if img.height > max_height:
            h_percent = max_height / float(img.height)
            w_size = int(float(img.width) * h_percent)
            img = img.resize((w_size, max_height), Image.LANCZOS)
    
    # Build output path in same folder with final size suffix if not provided
    if output_path is None:
        output_path = create_output_filename(
            input_path,
            mode="max",
            output_format=output_format or save_format,
            target_width=img.width,
            target_height=img.height,
        )

    return _save_image(img, output_path, save_format, quality)

def process_image_box(input_path, width, height, output_path=None, 
                     output_format=None, quality=85):
    """Process image to fit within a box while maintaining aspect ratio"""
    img = Image.open(input_path)
    save_format, _ = _prepare_format_and_path(input_path, None, output_format)
    
    # Resize to fit box
    img = ImageOps.contain(img, (width, height), Image.LANCZOS)
    
    # Build output path in same folder with final size suffix if not provided
    if output_path is None:
        output_path = create_output_filename(
            input_path,
            mode="box",
            output_format=output_format or save_format,
            target_width=img.width,
            target_height=img.height,
        )

    return _save_image(img, output_path, save_format, quality)

def process_image_default(input_path, output_path=None, output_format=None, quality=85):
    """Process image without resizing"""
    img = Image.open(input_path)
    save_format, _ = _prepare_format_and_path(input_path, None, output_format)

    # Build output path in same folder with final size suffix if not provided
    if output_path is None:
        output_path = create_output_filename(
            input_path,
            mode="default",
            output_format=output_format or save_format,
            target_width=img.width,
            target_height=img.height,
        )

    return _save_image(img, output_path, save_format, quality)

def create_output_filename(input_path, mode, output_format, target_width=None, target_height=None):
    """Create standardized output filename based on input path and processing mode"""
    base = os.path.splitext(input_path)[0]
    resolution_suffix = ""
    if target_width and target_height:
        resolution_suffix = f"_{target_width}x{target_height}"

    # Determine extension preference (prefer .jpg over .jpeg)
    ext = (output_format or os.path.splitext(input_path)[1].lstrip('.')).lower()
    if ext in ("jpeg", "jpg"):
        ext = "jpg"

    return f"{base}{resolution_suffix}.{ext}"

def copy_from_clipboard() -> str:
    import subprocess
    result = subprocess.run("pbpaste", universal_newlines=True, stdout=subprocess.PIPE)
    return result.stdout.strip()

def main():

    # Configuration

    # input_path = "/Users/nic/demo/pharma/drug-launch.png"
    
    # A path argument (Filee action) wins; the clipboard stays the fallback (Alfred).
    input_path = sys.argv[1] if len(sys.argv) > 1 else copy_from_clipboard()

    valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
    if input_path.startswith("/") and input_path.lower().endswith(valid_extensions):
        original_ext = os.path.splitext(input_path)[1].lower()
        pass
    else:
        print(f"❌ Input path is not a valid path: {input_path}")
        Notifier.notify(
            title='FAIL - people table',
            message=f'🔴🔴🔴 ERROR\nInput path is not a valid path: {input_path}',
        )

    output_format = 'png' if original_ext == '.png' else 'jpg'
    resize_mode = 'max'  # Options: 'exact', 'max', 'box', 'default'
    exact_mode_focus = '0%'  # Options: 'center', 'top', 'bottom', '10%'
    width = 1920
    height = 1080
    quality = 85
    
    # Determine desired output formats (if input is .png, save both .png and .jpg)
    original_ext = os.path.splitext(input_path)[1].lower()
    desired_formats = ['png', 'jpg'] if original_ext == '.png' else [output_format]

    # Let the processors determine the output path based on final size
    outputs = []
    
    # Process based on mode for each desired format
    for fmt in desired_formats:
        output_path = None
        if resize_mode == 'exact':
            output_path = process_image_exact(
                input_path, width, height,
                output_path=output_path,
                exact_mode_focus=exact_mode_focus,
                output_format=fmt,
                quality=quality
            )
        elif resize_mode == 'max':
            output_path = process_image_max(
                input_path,
                max_width=width,
                max_height=height,
                output_path=output_path,
                output_format=fmt,
                quality=quality
            )
        elif resize_mode == 'box':
            output_path = process_image_box(
                input_path, width, height,
                output_path=output_path,
                output_format=fmt,
                quality=quality
            )
        else:
            output_path = process_image_default(
                input_path,
                output_path=output_path,
                output_format=fmt,
                quality=quality
            )
        outputs.append(output_path)

    for p in outputs:
        print(f"\n\n✅ Image saved to:\t\t{p}")
    print()

    # Print dimensions of the processed image
    try:
        from PIL import Image
        notification_lines = []
        for p in outputs:
            with Image.open(p) as img:
                width, height = img.size
                file_size = os.path.getsize(p)
                file_size_kb = file_size / 1024
                file_size_mb = file_size_kb / 1024
                
                if file_size_mb >= 1:
                    size_str = f"{file_size_mb:.2f} MB"
                else:
                    size_str = f"{file_size_kb:.2f} KB"
                
                print(f"ℹ️  Output image dimensions:\t{width}x{height} ({os.path.basename(p)})")
                print(f"ℹ️  Output file size:\t\t{size_str}\n")
                notification_lines.append(f"{os.path.basename(p)} — {width}x{height}, {size_str}")

        Notifier.notify(
            title='SUCCESS',
            message='\n'.join(["✅ Outputs:"] + notification_lines),
        )
    except Exception as e:
        print(f"Could not read dimensions of output image: {e}")

if __name__ == '__main__':
    main()
