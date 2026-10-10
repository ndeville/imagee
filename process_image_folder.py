import sys
import os
import subprocess
import shutil
from PIL import Image, ImageOps
from resize_optimise_image import process_image_max, copy_from_clipboard

def process_image_folder():
    """Process all images and .mp4 videos in a given folder"""
    
    # Get folder path from clipboard
    # A path argument (Filee action) wins; the clipboard stays the fallback (Alfred).
    folder_path = (sys.argv[1] if len(sys.argv) > 1 else copy_from_clipboard()).strip()
    
    # Validate folder path
    if not os.path.isdir(folder_path):
        print(f"❌ Invalid folder path: {folder_path}")
        return
    
    # Configuration
    max_width = 1000
    max_height = 1000
    quality = 85
    
    # Valid media extensions
    valid_extensions = ('.png', '.jpg', '.jpeg')  # images
    video_extensions = ('.mp4', '.m4v', '.mov')  # videos
    
    # Create output subfolder
    output_folder = os.path.join(folder_path, "optimised")
    os.makedirs(output_folder, exist_ok=True)
    
    # Find all media files
    image_files = []
    video_files = []
    for filename in os.listdir(folder_path):
        lower = filename.lower()
        if lower.endswith(valid_extensions):
            image_files.append(filename)
        elif lower.endswith(video_extensions):
            video_files.append(filename)
    
    if not image_files and not video_files:
        print(f"❌ No image or video files found in: {folder_path}")
        return
    
    print(f"📁 Processing {len(image_files)} images and {len(video_files)} videos from: {folder_path}")
    print(f"📁 Output folder: {output_folder}")
    
    processed_files = []
    
    # Process each image
    for filename in image_files:
        input_path = os.path.join(folder_path, filename)
        
        # Determine output format(s)
        original_ext = os.path.splitext(filename)[1].lower()
        output_format = 'png' if original_ext == '.png' else 'jpg'
        
        # Create output filename
        base_name = os.path.splitext(filename)[0]
        output_filename = f"{base_name}.{output_format}"
        output_path = os.path.join(output_folder, output_filename)
        
        try:
            # Process the image
            result_path = process_image_max(
                input_path,
                max_width=max_width,
                max_height=max_height,
                output_path=output_path,
                output_format=output_format,
                quality=quality
            )
            processed_files.append(result_path)
            print(f"✅ Processed: {filename} -> {output_filename}")
            
        except Exception as e:
            print(f"❌ Error processing {filename}: {str(e)}")
    
    # Before processing videos, ensure ffmpeg is available
    ffmpeg_exe = shutil.which("ffmpeg") if video_files else None
    if video_files and not ffmpeg_exe:
        print("❌ ffmpeg not found on PATH. Install it (e.g., `brew install ffmpeg`) and re-run.")
    
    # Process each video using ffmpeg
    for filename in video_files:
        input_path = os.path.join(folder_path, filename)
        output_filename = filename  # Keep the same name as original
        output_path = os.path.join(output_folder, output_filename)
        
        # Skip video processing if ffmpeg is unavailable
        if not ffmpeg_exe:
            continue
        
        # ffmpeg command as specified
        cmd = [
            ffmpeg_exe,
            "-y",  # overwrite without prompt
            "-i", input_path,
            "-vcodec", "libx264",
            "-crf", "28",
            "-preset", "veryfast",
            "-acodec", "aac",
            "-b:a", "128k",
            output_path,
        ]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "ffmpeg failed")
            processed_files.append(output_path)
            print(f"✅ Processed video: {filename} -> {output_filename}")
        except Exception as e:
            print(f"❌ Error processing video {filename}: {str(e)}")
    
    print(f"\n🎉 Successfully processed {len(processed_files)} files")
    print(f"📁 Output folder: {output_folder}")

if __name__ == "__main__":
    process_image_folder()
