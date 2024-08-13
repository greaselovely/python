# clever_words.py

import os
import sys
import nltk
import string
import argparse
import platform
import itertools
from collections import Counter
from collections import defaultdict
from nltk.corpus import words as nltk_words


description = """
This script generates words based on the structure of an input word,
replacing consonants with consonants and vowels with vowels. It then
categorizes these words into different language registers.

Key concepts:
- Register: The overall term for different levels of language formality and complexity.
- Colloquial: Everyday casual speech.
- Vernacular: Common, everyday speech.
- Standard: More "proper" or standardized forms.
- Formal: More sophisticated communication.
"""

def print_install_instructions():
    os_name = platform.system().lower()
    if os_name == 'windows':
        print("To install 'enchant' on Windows:")
        print("1. Run: pip install pyenchant")
        print("2. If you still encounter issues, you may need to install the C library:")
        print("   - Download the appropriate binary from https://github.com/AbiWord/enchant/releases")
        print("   - Add the path to the installed library to your system PATH")
    elif os_name == 'darwin':  # macOS
        print("To install 'enchant' on macOS:")
        print("1. Install 'enchant' using Homebrew: brew install enchant")
        print("2. Then install pyenchant: pip install pyenchant")
    elif os_name == 'linux':
        print("To install 'enchant' on Linux:")
        print("For Ubuntu/Debian:")
        print("1. Run: sudo apt-get install libenchant1c2a")
        print("2. Then run: pip install pyenchant")
        print("For other distributions, use the appropriate package manager to install libenchant,")
        print("then install pyenchant using pip.")
    else:
        print("Please install the 'enchant' library for your operating system.")
    print("\nAfter installation, restart your Python environment before running this script.")

try:
    import enchant
except ImportError:
    print("Error: The 'enchant' library is not installed.")
    print_install_instructions()
    sys.exit(1)



def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate words based on the structure of an input word.")
    parser.add_argument('-w', '--word', type=str, default='kyuss',
                        help='Input word to base the structure on (default: kyuss)')
    return parser.parse_args()

# Download necessary NLTK data
nltk.download('words', quiet=True)

# Create a set of common words and letter frequency
common_words = set(w.lower() for w in nltk_words.words())
all_letters = ''.join(common_words)
letter_freq = Counter(all_letters)
total_letters = sum(letter_freq.values())

def letter_unusualness(letter):
    """Calculate how unusual a letter is based on its frequency in common words."""
    return 1 - (letter_freq[letter] / total_letters)

def determine_register(word):
    """
    Determine the register of a word based on its frequency and letter unusualness.
    """
    if word in common_words:
        return 'colloquial'
    
    # Calculate average letter unusualness
    avg_unusualness = sum(letter_unusualness(letter) for letter in word) / len(word)
    
    if avg_unusualness < 0.02:
        return 'vernacular'
    elif avg_unusualness < 0.035:
        return 'standard'
    else:
        return 'formal'

# Initialize the English dictionary
d = enchant.Dict("en_US")

# Define vowels and consonants
vowels = 'aeiouy'
consonants = 'bcdfghjklmnpqrstvwxz'

def is_vowel(char):
    return char.lower() in vowels

def generate_words(template):
    """
    Generate words based on the structure of the input word.
    
    Args:
    template (str): The input word to base the structure on.
    
    Returns:
    list: A list of valid words matching the structure of the input.
    """
    structure = ['vowel' if is_vowel(char) else 'consonant' for char in template]
    valid_words = []

    for combination in itertools.product(*(vowels if s == 'vowel' else consonants for s in structure)):
        word = ''.join(combination)
        if d.check(word):
            valid_words.append(word)

    return valid_words

def determine_register(word):
    """
    Determine the register of a word based on its length and complexity.
    This is a simplified method and can be improved for more accuracy.
    """
    if len(word) <= 4:
        return 'colloquial'
    elif len(word) == 5:
        return 'vernacular'
    elif len(word) == 6:
        return 'standard'
    else:
        return 'formal'

def categorize_words(words):
    """
    Categorize words into different registers.
    """
    categories = defaultdict(list)
    for word in words:
        register = determine_register(word)
        categories[register].append(word)
    return categories



# ... (previous parts of the script remain the same)

def format_words(words, words_per_line=6):
    """Format a list of words with a specified number of words per line."""
    lines = []
    for i in range(0, len(words), words_per_line):
        line = ", ".join(words[i:i+words_per_line])
        lines.append(line)
    return "\n".join(lines)

def main():
    args = parse_arguments()
    input_word = args.word.lower()

    # Get input word
    if not input_word:
        input_word = "kyuss" if not input_word else input("Enter word [kyuss]: ").lower()

    print(f"Generating words based on the structure of '{input_word}'...")

    # Generate valid words
    valid_words = generate_words(input_word)

    # Categorize words
    categorized_words = categorize_words(valid_words)

    # Prepare output
    output = f"Words generated based on the structure of '{input_word}':\n\n"
    for register, words in categorized_words.items():
        output += f"{register.capitalize()} words:\n"
        output += format_words(words) + "\n\n"

    output += f"Total valid words found: {len(valid_words)}"

    # Write to file in home directory
    home_dir = os.path.expanduser("~")
    file_name = f"{input_word}_words.txt"
    file_path = os.path.join(home_dir, file_name)

    with open(file_path, 'w') as f:
        f.write(description + "\n\n")
        f.write(output)

    print(f"Results have been written to: {file_path}")

if __name__ == "__main__":
    main()