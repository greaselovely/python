import os
import sys
import json
import time
from openai import OpenAI

file_name = 'readme.json'
output_dir = os.path.dirname(__file__)
output_path = os.path.join(output_dir, file_name)

def load_api_key():
    """Load the API key from a JSON file, or create the file if it doesn't exist."""
    if not os.path.exists(output_path):
        with open(output_path, 'w') as file:
            json.dump({'openai_api_key': ''}, file, indent=2)
            print(f'\n\n[!]\tCreated {file_name}. Please add your OpenAI API key to the file.\n\n')
            sys.exit(1)
    
    with open(output_path, 'r') as file:
        data = json.load(file)
        api_key = data.get('openai_api_key')
        if not api_key:
            print(f'\n\n[!]\tAPI key not found in {file_name}. Please add your OpenAI API key to the file.\n\n')
            sys.exit(1)
    return api_key

def summarize_code(file_path, openai_api_key):
    """Generate a summary for the given file's code using the OpenAI API."""
    with open(file_path, 'r', encoding='utf-8') as file:
        code_snippet = file.read()

    client = OpenAI(api_key=openai_api_key)
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": f"Summarize this Python code for a technical README file:\n\n{code_snippet}"
                }
            ],
            model="gpt-3.5-turbo",
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"API call failed: {e}")
        time.sleep(60)  # Wait and retry or adjust based on the API's rate limit response
        return "Summary could not be generated due to an API error."

def generate_readme(directory, openai_api_key):
    """Generates a README.md file with summaries for each Python file in the directory."""
    readme_contents = "# Project Documentation\n\n"
    files_to_summarize = [os.path.join(root, file)
                          for root, dirs, files in os.walk(directory)
                          for file in files if file.endswith(".py")]

    for file_path in files_to_summarize:
        print(f"Generating summary for {file_path}...")
        summary = summarize_code(file_path, openai_api_key)
        readme_contents += f"## {os.path.basename(file_path)}\n\n{summary}\n\n"

    with open("README.md", "w", encoding='utf-8') as readme_file:
        readme_file.write(readme_contents)

if __name__ == "__main__":
    api_key = load_api_key()
    current_directory = "."
    generate_readme(current_directory, api_key)
