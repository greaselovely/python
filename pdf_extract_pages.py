import argparse
import os
from pypdf import PdfReader, PdfWriter

def get_input(prompt):
    """Helper function to prompt user input"""
    while True:
        path = input(prompt).strip()
        if os.path.exists(path):
            return path
        print("Invalid path. Please enter a valid file or directory.")

def split_pdf(input_pdf, output_folder):
    """Function to split each page of a PDF into its own file"""
    reader = PdfReader(input_pdf)

    os.makedirs(output_folder, exist_ok=True)  # Ensure output directory exists

    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)

        output_filename = os.path.join(output_folder, f"page_{i+1}.pdf")
        with open(output_filename, "wb") as output_pdf:
            writer.write(output_pdf)

        print(f"Saved: {output_filename}")

def main():
    parser = argparse.ArgumentParser(description="Extract each page of a PDF into separate files.")
    parser.add_argument("-i", "--input", help="Path to the input PDF file", required=False)
    parser.add_argument("-o", "--output", help="Path to the output folder", required=False)

    args = parser.parse_args()

    input_pdf = args.input if args.input else get_input("Enter the path to the input PDF file: ")
    output_folder = args.output if args.output else get_input("Enter the output directory: ")

    split_pdf(input_pdf, output_folder)

if __name__ == "__main__":
    main()
