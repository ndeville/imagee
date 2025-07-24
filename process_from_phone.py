"""
Script triggered with Hazel, monitoring a Dropbox folder where images are uploaded. 
Images are resized to a max canvas size (eg 1000x1000), optimised in size, and stripped from metadata - made available in a dedicated output folder. 
"""

from datetime import datetime
import os
print("----------")
ts_file = f"{datetime.now().strftime('%y%m%d-%H%M%S')}"

import time
start_time = time.time()

from dotenv import load_dotenv
load_dotenv()
INPUT_FOLDER = os.getenv("INPUT_FOLDER")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER")
PATH_INDEXEE = os.getenv("PATH_INDEXEE")

import sys
sys.path.append(PATH_INDEXEE)

import pprint
pp = pprint.PrettyPrinter(indent=4)

count = 0
count_row = 0

test = True
v = True # verbose mode

print(f"{os.path.basename(__file__)} boilerplate loaded -----------\n")
####################
# Process .heic images from iPhone

from PIL import Image, ImageOps
import pillow_heif
import shutil

# GLOBALS

input_folder = INPUT_FOLDER
output_folder = OUTPUT_FOLDER


# FUNCTIONS

# pip install pillow pillow-heif
from pathlib import Path

def heic_to_jpg(heic_path: str | Path, quality: int = 95, keep_exif: bool = True) -> Path:
    """
    Convert a .heic image to .jpg in the same directory.

    Args:
        heic_path: Path to the .heic file.
        quality: JPEG quality (1-95).
        keep_exif: Preserve EXIF metadata if present.

    Returns:
        Path to the created .jpg file.
    """
    try:
        import pillow_heif  # registers HEIF support for Pillow
        pillow_heif.register_heif_opener()
    except ImportError as e:
        raise ImportError("Install dependencies first: pip install pillow pillow-heif") from e

    from PIL import Image

    heic_path = Path(heic_path)
    jpg_path = heic_path.with_suffix(".jpg")

    with Image.open(heic_path) as im:
        exif = im.info.get("exif") if keep_exif else None
        im.convert("RGB").save(jpg_path, "JPEG", quality=quality, exif=exif)

    return jpg_path



def optimise_jpg(jpg_path: str | Path, quality: int = 85) -> Path:
    """
    Optimise a JPEG image by compressing and resizing it to 1600x2133.
    
    Args:
        jpg_path: Path to the JPEG file
        quality: JPEG quality (1-95)
        
    Returns:
        Path to the optimised file (overwrites original)
    """
    jpg_path = Path(jpg_path)
    
    with Image.open(jpg_path) as img:
        # Resize maintaining aspect ratio
        img = ImageOps.contain(img, (1600, 2133), Image.LANCZOS)
        
        # Save with optimisation
        img.save(jpg_path, "JPEG", quality=quality, optimize=True)
        
    return jpg_path




# MAIN


existing_files = [f"{input_folder}/{file}" for file in os.listdir(input_folder) if '.heic' in file.lower()]

for file in existing_files:
    count += 1
    print(f"\n#{count} {file=}")

    jpg_path = heic_to_jpg(file)
    optimise_jpg(jpg_path)

    # Rename both files with timestamp prefix
    jpg_new_name = f"{output_folder}/{ts_file}_{count}.jpg"
    heic_new_name = f"{input_folder}/raw/{ts_file}_{count}.heic"
    
    shutil.move(jpg_path, jpg_new_name)
    shutil.move(file, heic_new_name)


    # heif_file = pillow_heif.read_heif(file)
    # image = Image.frombytes(
    #     heif_file.mode,
    #     heif_file.size,
    #     heif_file.data,
    #     "raw",
    # )

    # image = ImageOps.contain(image, (1000,1000))
    # image_save = f"{output_folder}/{ts_file}_{count}.jpg"
    # if test:
    #     print(f"\n{image_save=}")
    # image.save(image_save, optimize=True) # can add quality=80

    # move_to = f'{input_folder}/raw/{ts_file}_{count}.heic'
    # if test:
    #     print(f"{move_to=}")
    # shutil.move(file, move_to)







########################################################################################################

if __name__ == '__main__':
    print()
    print()
    print('-------------------------------')
    print(f"{os.path.basename(__file__)}")
    print()
    print(f"{count=}")
    print()
    print('-------------------------------')
    run_time = round((time.time() - start_time), 1)
    if run_time > 60:
        print(f'{os.path.basename(__file__)} finished in {run_time/60} minutes.')
    else:
        print(f'{os.path.basename(__file__)} finished in {run_time}s.')
    print()