"""
Script triggered with Hazel, monitoring a Dropbox folder where images are uploaded. 
Images are resized to a max canvas size (eg 1000x1000), optimised in size, and stripped from metadata - made available in a dedicated output folder. 
"""

from datetime import datetime
import os
print("----------")
ts_file = f"{datetime.now().strftime('%y%m%d-%H%M%S-%f')}"

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

input_folder = INPUT_FOLDER
output_folder = OUTPUT_FOLDER

existing_files = [f"{input_folder}/{file}" for file in os.listdir(input_folder) if '.heic' in file.lower()]

for file in existing_files:
    count += 1
    print(f"\n#{count} {file=}")
    heif_file = pillow_heif.read_heif(file)
    image = Image.frombytes(
        heif_file.mode,
        heif_file.size,
        heif_file.data,
        "raw",
    )

    image = ImageOps.contain(image, (1000,1000))
    image_save = f"{output_folder}/{ts_file}_{count}.jpg"
    if test:
        print(f"\n{image_save=}")
    image.save(image_save, optimize=True) # can add quality=80

    move_to = f'{input_folder}/raw/{ts_file}_{count}.heic'
    if test:
        print(f"{move_to=}")
    shutil.move(file, move_to)

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