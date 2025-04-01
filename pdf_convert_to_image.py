import os
import argparse
from pdf2image import convert_from_path
from tqdm import tqdm

def convert_pdfs_to_images(input_folder, output_folder, image_format="jpg"):
    """Converts all PDFs in a folder to images (JPG/PNG) and saves them."""
    
    # Ensure output directory exists
    os.makedirs(output_folder, exist_ok=True)

    # List all PDF files in the input directory
    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print("No PDF files found in the directory.")
        return

    print(f"Converting {len(pdf_files)} PDFs to {image_format.upper()}...")

    for pdf in tqdm(pdf_files, desc="Processing PDFs"):
        pdf_path = os.path.join(input_folder, pdf)
        
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=300)  # High-quality conversion

        base_name = os.path.splitext(pdf)[0]  # Get filename without extension

        for i, img in enumerate(images):
            output_filename = f"{base_name}.{image_format}"
            output_path = os.path.join(output_folder, output_filename)
            img.save(output_path, image_format.upper())  # Save image
            print(f"Saved: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Convert PDFs in a directory to images (JPG/PNG).")
    parser.add_argument("-i", "--input", help="Path to the input folder containing PDFs", required=False)
    parser.add_argument("-o", "--output", help="Path to the output folder for images", required=False)
    parser.add_argument("-f", "--format", choices=["jpg", "png"], default="jpg", help="Image format (jpg/png)")

    args = parser.parse_args()

    input_folder = args.input if args.input else input("Enter the path to the input folder: ").strip()
    output_folder = args.output if args.output else input("Enter the path to the output folder: ").strip()
    image_format = args.format

    convert_pdfs_to_images(input_folder, output_folder, image_format)

if __name__ == "__main__":
    main()
