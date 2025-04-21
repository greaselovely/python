import PyPDF2
import argparse

def flatten_pdf(input_path, output_path):
    """
    Flatten a PDF by removing interactive elements while preserving visible content.
    
    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path where the flattened PDF will be saved
    """
    try:
        # Open the existing PDF
        with open(input_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            writer = PyPDF2.PdfWriter()
            
            # Process each page
            for page_num in range(len(reader.pages)):
                # Get the page
                page = reader.pages[page_num]
                
                # Create a new page that only contains the visible content
                writer.add_page(page)
                
                # Remove any form fields, annotations, and other interactive elements
                if '/Annots' in page:
                    del page['/Annots']
                
            # Save the flattened PDF
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
                
            print(f"PDF flattened successfully. Saved to {output_path}")
            return True
            
    except Exception as e:
        print(f"Error flattening PDF: {e}")
        return False

if __name__ == "__main__":
    # Create command line arguments
    parser = argparse.ArgumentParser(description='Flatten a PDF by removing interactive elements.')
    parser.add_argument('input', help='Path to the input PDF file')
    parser.add_argument('output', help='Path where the flattened PDF will be saved')
    args = parser.parse_args()
    
    # Flatten the PDF
    flatten_pdf(args.input, args.output)