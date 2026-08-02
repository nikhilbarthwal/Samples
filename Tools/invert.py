import os
import sys
from PIL import Image


def invert_image_colors():
    # 1. Check if the filename was actually provided on the command line
    # sys.argv[0] is the script name itself, sys.argv[1] is the first argument
    if len(sys.argv) < 2:
        print("Error: Missing image filename.")
        print("Usage: python invert.py <filename.jpg>")
        sys.exit(1)

    file_name = sys.argv[1]

    # 2. Check if the file exists
    if not os.path.exists(file_name):
        print(f"Error: The file '{file_name}' could not be found.")
        sys.exit(1)

    try:
        # 3. Open and convert to RGB
        with Image.open(file_name) as img:
            rgb_img = img.convert("RGB")

            print(f"Inverting pixels for '{file_name}'...")

            # 4. Perform the 255 - x inversion math
            inverted_img = Image.eval(rgb_img, lambda x: 255 - x)

            # 5. Generate output name and save
            name, ext = os.path.splitext(file_name)
            output_name = f"{name}_inverted{ext}"

            inverted_img.save(output_name)
            print(f"Success! Saved as: {output_name}")

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    invert_image_colors()
