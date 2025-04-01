import argparse
import os
from pypdf import PdfReader, PdfWriter

def rotate_pdf(file_path, direction):
    """Rotates a PDF left (-90 degrees) or right (+90 degrees) and overwrites the file."""
    if not os.path.exists(file_path):
        print("Error: File does not exist.")
        return

    reader = PdfReader(file_path)
    writer = PdfWriter()

    for page in reader.pages:
        if direction == "left":
            page.rotate(-90)  # Rotate counterclockwise
        elif direction == "right":
            page.rotate(90)   # Rotate clockwise
        writer.add_page(page)

    # Overwrite the original file with rotated pages
    with open(file_path, "wb") as output_pdf:
        writer.write(output_pdf)

    print(f"Successfully rotated and saved: {file_path}")

def main():
    parser = argparse.ArgumentParser(description="Rotate a PDF file left or right and save it under the same name.")
    parser.add_argument("-f", "--file", help="Path to the PDF file", required=False)
    parser.add_argument("-d", "--direction", choices=["left", "right"], help="Rotation direction", required=False)

    args = parser.parse_args()

    file_path = args.file if args.file else input("Enter the path to the PDF file: ").strip()
    direction = args.direction if args.direction else input("Enter rotation direction (left/right): ").strip().lower()

    if direction not in ["left", "right"]:
        print("Invalid direction. Please enter 'left' or 'right'.")
        return

    rotate_pdf(file_path, direction)

if __name__ == "__main__":
    main()
