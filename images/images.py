import os
from PIL import Image
import pyheif

def convert_heif_to_png():
    """
    Converts all HEIF files (.heic or .heif) in the current directory to PNG format.
    """
    current_directory = os.getcwd()
    output_directory = os.path.join(current_directory, "converted_pngs")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for filename in os.listdir(current_directory):
        if filename.lower().endswith((".heic", ".heif")):
            heif_path = os.path.join(current_directory, filename)
            png_filename = os.path.splitext(filename)[0] + ".png"
            png_path = os.path.join(output_directory, png_filename)

            try:
                # Read HEIF file
                heif_file = pyheif.read(heif_path)

                # Convert to PIL image
                image = Image.frombytes(
                    heif_file.mode, heif_file.size, heif_file.data, "raw", heif_file.mode
                )

                # Save as PNG
                image.save(png_path, "PNG")
                print(f"Converted {filename} to {png_filename}")
            except Exception as e:
                print(f"Failed to convert {filename}: {e}")

if __name__ == "__main__":
    convert_heif_to_png()
