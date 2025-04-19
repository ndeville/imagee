#!/usr/bin/env python3
from PIL import Image, ImageOps
import os
from datetime import datetime

def _prepare_format_and_path(input_path, output_path=None, output_format=None):
    """Helper function to handle format and path preparation"""
    if output_format is None:
        output_format = os.path.splitext(input_path)[1].lower().replace('.', '')
    
    # Standardize format names
    if output_format.lower() in ['jpg', 'jpeg']:
        output_format = 'JPEG'
    elif output_format.lower() == 'png':
        output_format = 'PNG'
    
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
    
    img.save(output_path, format=output_format, **save_kwargs)
    return output_path

def process_image_exact(input_path, width, height, output_path=None, 
                       exact_mode_focus='center', output_format=None, quality=85):
    """Process image with exact dimensions"""
    img = Image.open(input_path)
    output_format, output_path = _prepare_format_and_path(input_path, output_path, output_format)
    
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
    
    return _save_image(img, output_path, output_format, quality)

def process_image_max(input_path, max_width=None, max_height=None, 
                     output_path=None, output_format=None, quality=85):
    """Process image with maximum dimension constraints"""
    img = Image.open(input_path)
    output_format, output_path = _prepare_format_and_path(input_path, output_path, output_format)
    
    # Apply max dimension resize
    if max_width and max_height:
        img = ImageOps.contain(img, (max_width, max_height), Image.LANCZOS)
    elif max_width:
        w_percent = max_width / float(img.width)
        h_size = int(float(img.height) * w_percent)
        img = img.resize((max_width, h_size), Image.LANCZOS)
    elif max_height:
        h_percent = max_height / float(img.height)
        w_size = int(float(img.width) * h_percent)
        img = img.resize((w_size, max_height), Image.LANCZOS)
    
    return _save_image(img, output_path, output_format, quality)

def process_image_box(input_path, width, height, output_path=None, 
                     output_format=None, quality=85):
    """Process image to fit within a box while maintaining aspect ratio"""
    img = Image.open(input_path)
    output_format, output_path = _prepare_format_and_path(input_path, output_path, output_format)
    
    # Resize to fit box
    img = ImageOps.contain(img, (width, height), Image.LANCZOS)
    
    return _save_image(img, output_path, output_format, quality)

def process_image_default(input_path, output_path=None, output_format=None, quality=85):
    """Process image without resizing"""
    img = Image.open(input_path)
    output_format, output_path = _prepare_format_and_path(input_path, output_path, output_format)
    
    return _save_image(img, output_path, output_format, quality)

def create_output_filename(input_path, mode, output_format, target_width=None, target_height=None):
    """Create standardized output filename based on input path and processing mode"""
    base = os.path.splitext(input_path)[0]
    resolution_suffix = ""
    if target_width and target_height:
        resolution_suffix = f"{target_width}x{target_height}"
    return f"{base}_{resolution_suffix}.{output_format.lower()}"

def main():
    # Configuration
    # input_path = "/Users/nic/demo/pharma/drug-launch.png"
    input_path = input("\nEnter the path to the image > ")
    output_format = 'jpg'
    resize_mode = 'exact'  # Options: 'exact', 'max', 'box', 'default'
    exact_mode_focus = '45%'  # Options: 'center', 'top', 'bottom', '10%'
    width = 1584
    height = 396
    quality = 85
    
    # Create output filename
    mode_suffix = f'{resize_mode}_{exact_mode_focus}' if resize_mode == 'exact' else resize_mode
    output_path = create_output_filename(input_path, mode_suffix, output_format, 
                                       target_width=width, target_height=height)
    
    # Process based on mode
    if resize_mode == 'exact':
        output_path = process_image_exact(
            input_path, width, height,
            output_path=output_path,
            exact_mode_focus=exact_mode_focus,
            output_format=output_format,
            quality=quality
        )
    elif resize_mode == 'max':
        output_path = process_image_max(
            input_path,
            max_width=width,
            max_height=height,
            output_path=output_path,
            output_format=output_format,
            quality=quality
        )
    elif resize_mode == 'box':
        output_path = process_image_box(
            input_path, width, height,
            output_path=output_path,
            output_format=output_format,
            quality=quality
        )
    else:
        output_path = process_image_default(
            input_path,
            output_path=output_path,
            output_format=output_format,
            quality=quality
        )
    
    print(f"\n\n✅ Image saved to:\t\t{output_path}\n")

    # Print dimensions of the processed image
    try:
        from PIL import Image
        with Image.open(output_path) as img:
            width, height = img.size
            file_size = os.path.getsize(output_path)
            file_size_kb = file_size / 1024
            file_size_mb = file_size_kb / 1024
            
            if file_size_mb >= 1:
                size_str = f"{file_size_mb:.2f} MB"
            else:
                size_str = f"{file_size_kb:.2f} KB"
                
            print(f"ℹ️  Output image dimensions:\t{width}x{height}")
            print(f"ℹ️  Output file size:\t\t{size_str}\n\n")
    except Exception as e:
        print(f"Could not read dimensions of output image: {e}")

if __name__ == '__main__':
    main()
