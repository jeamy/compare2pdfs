#!/usr/bin/env python3

import sys
import os
import tempfile
import subprocess
import locale
import re
from typing import List, Dict, Set, Tuple, Optional
import atexit
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTChar

def check_dependencies():
    """Check if required command line tools are available."""
    required_tools = ['pdftotext', 'grep', 'sed', 'awk']
    for tool in required_tools:
        if not subprocess.run(['which', tool], capture_output=True).returncode == 0:
            print(f"Error: {tool} is not installed.")
            sys.exit(1)

def cleanup_temp_files(temp_files: List[str]):
    """Clean up temporary files."""
    if not os.environ.get('DEBUG') == '1':
        for file in temp_files:
            try:
                os.remove(file)
            except OSError:
                pass

def rgb2hex(rgb: Tuple[float, float, float]) -> str:
    """Convert RGB values (0-1) to hex color code."""
    r, g, b = rgb
    return '#{:02x}{:02x}{:02x}'.format(
        int(r * 255),
        int(g * 255),
        int(b * 255)
    )

def get_color_name(rgb: Tuple[float, float, float]) -> str:
    """Convert RGB values to color names."""
    r, g, b = rgb
    # Convert to 0-255 range for easier comparison
    r255 = int(r * 255)
    g255 = int(g * 255)
    b255 = int(b * 255)

    # Define color thresholds
    def is_close(a: int, b: int, threshold: int = 30) -> bool:
        return abs(a - b) <= threshold

    # For grayscale colors
    if is_close(r255, g255, 5) and is_close(g255, b255, 5):
        if r255 < 30:
            return 'schwarz'
        elif r255 > 225:
            return 'weiß'
        elif r255 > 150:
            return 'hellgrau'
        elif r255 > 75:
            return 'grau'
        else:
            return 'dunkelgrau'

    # Basic colors with tolerance
    if r255 > 200 and g255 < 50 and b255 < 50:
        return 'rot'
    elif r255 < 50 and g255 > 200 and b255 < 50:
        return 'grün'
    elif r255 < 50 and g255 < 50 and b255 > 200:
        return 'blau'
    elif r255 > 200 and g255 > 200 and b255 < 50:
        return 'gelb'
    elif r255 > 200 and g255 < 50 and b255 > 200:
        return 'magenta'
    elif r255 < 50 and g255 > 200 and b255 > 200:
        return 'cyan'
    elif r255 > 200 and g255 > 100 and b255 < 50:
        return 'orange'
    elif r255 > 150 and g255 < 100 and b255 < 100:
        return 'dunkelrot'
    elif r255 < 100 and g255 > 150 and b255 < 100:
        return 'dunkelgrün'
    else:
        hex_color = rgb2hex((r, g, b))
        return f'RGB({hex_color})'

def get_color_from_colorspace(color_space) -> Optional[Tuple[float, float, float]]:
    """Extract RGB values from a PDFColorSpace object."""
    if hasattr(color_space, 'rgb'):
        return color_space.rgb
    elif hasattr(color_space, 'color'):
        # Some color spaces store color in the 'color' attribute
        if len(color_space.color) == 3:  # RGB color
            return tuple(color_space.color)
        elif len(color_space.color) == 1:  # Grayscale
            gray = color_space.color[0]
            return (gray, gray, gray)
    elif hasattr(color_space, 'ncomponents') and color_space.ncomponents == 1:
        # Handle DeviceGray colorspace
        if hasattr(color_space, 'color') and color_space.color:
            gray = color_space.color[0]
        elif hasattr(color_space, 'value'):
            gray = color_space.value
        else:
            gray = 0
        return (gray, gray, gray)
    elif hasattr(color_space, '_color'):
        # Some PDFs store color in _color
        if isinstance(color_space._color, tuple) and len(color_space._color) == 3:
            return color_space._color
    return None

def extract_text_with_colors(pdf_path: str) -> Dict[str, Tuple[Optional[str], Optional[str]]]:
    """Extract text and its colors from PDF."""
    text_colors = {}
    debug = os.environ.get('DEBUG') == '1'
    if debug:
        print(f"\nExtracting colors from {pdf_path}...")
    for page in extract_pages(pdf_path):
        for element in page:
            if isinstance(element, LTTextBox):
                for text_line in element:
                    text = ''
                    fg_color = None
                    bg_color = None
                    for char in text_line:
                        if isinstance(char, LTChar):
                            text += char.get_text()
                            # Try to get foreground color from various attributes
                            if debug and text.strip():
                                print(f"\nAnalyzing text: {text.strip()}")
                                if hasattr(char, 'ncs'):
                                    print(f"NCS: {char.ncs}")
                                if hasattr(char, 'graphicstate'):
                                    gs = char.graphicstate
                                    print(f"GraphicState attrs: {[attr for attr in dir(gs) if not attr.startswith('_')]}")
                            
                            # Try to get foreground color
                            if hasattr(char, 'ncs') and char.ncs:
                                rgb = get_color_from_colorspace(char.ncs)
                                if rgb:
                                    fg_color = get_color_name(rgb)
                            
                            if hasattr(char, 'graphicstate'):
                                gs = char.graphicstate
                                
                                # Try to get foreground color from graphicstate if not already found
                                if not fg_color:
                                    # Try ncolor/scolor first (these seem most reliable)
                                    if hasattr(gs, 'ncolor') and gs.ncolor:
                                        rgb = get_color_from_colorspace(gs.ncolor)
                                        if rgb:
                                            fg_color = get_color_name(rgb)
                                    elif hasattr(gs, 'scolor') and gs.scolor:
                                        rgb = get_color_from_colorspace(gs.scolor)
                                        if rgb:
                                            fg_color = get_color_name(rgb)
                                    # Then try other color attributes
                                    elif hasattr(gs, 'strokecolor') and gs.strokecolor:
                                        rgb = get_color_from_colorspace(gs.strokecolor)
                                        if rgb:
                                            fg_color = get_color_name(rgb)
                                    elif hasattr(gs, 'stroking_color') and gs.stroking_color:
                                        rgb = get_color_from_colorspace(gs.stroking_color)
                                        if rgb:
                                            fg_color = get_color_name(rgb)
                                
                                # Try to get background color
                                if hasattr(gs, 'fillcolor') and gs.fillcolor:
                                    rgb = get_color_from_colorspace(gs.fillcolor)
                                    if rgb:
                                        bg_color = get_color_name(rgb)
                                elif hasattr(gs, 'color') and gs.color:
                                    rgb = get_color_from_colorspace(gs.color)
                                    if rgb:
                                        bg_color = get_color_name(rgb)
                                elif hasattr(gs, 'non_stroking_color') and gs.non_stroking_color:
                                    rgb = get_color_from_colorspace(gs.non_stroking_color)
                                    if rgb:
                                        bg_color = get_color_name(rgb)
                    if text.strip():
                        text_colors[text.strip()] = (fg_color, bg_color)
    return text_colors

def extract_text_from_pdf(pdf_path: str, output_path: str):
    """Extract text from PDF with UTF-8 encoding."""
    subprocess.run(['pdftotext', '-layout', '-enc', 'UTF-8', pdf_path, output_path], check=True)

def normalize_for_comparison(text: str) -> str:
    """Normalize text for comparison."""
    # Remove invalid or replacement characters
    text = re.sub(r'[\x00-\x09\x0b-\x1f\x7f\x80-\xff]', '', text)
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace various types of dashes and hyphens with a standard one
    text = re.sub(r'[–—―­]', '-', text)
    
    # Remove soft hyphens and other special characters
    text = re.sub(r'[­​‌‍]', '', text)
    
    # Remove bullet points at start
    text = re.sub(r'^[\*•‣◦⁃∙]\s*', '', text)
    
    # Normalize spaces
    text = ' '.join(text.split())
    
    # Remove punctuation except periods for abbreviations
    text = re.sub(r'[,;:"""()]', '', text)
    
    # Remove line numbers and page markers
    text = re.sub(r'^[0-9]+\.', '', text)
    
    # Trim whitespace
    return text.strip()

def extract_sentences(text: str) -> List[str]:
    """Convert text into sentences."""
    # Replace newlines with spaces, preserving paragraph breaks
    text = ' '.join(text.splitlines())
    
    # Normalize multiple spaces
    text = ' '.join(text.split())
    
    # Add proper spacing around bullet points
    text = re.sub(r'•', '\n•', text)
    
    # Add newline after each sentence end, but not after abbreviations
    text = re.sub(r'([.!?]) ([A-ZÄÖÜ])', r'\1\n\2', text)
    
    # Split into sentences
    sentences = text.split('\n')
    
    # Process sentences to join lines that don't end with sentence-ending punctuation
    processed_sentences = []
    current_sentence = ''
    
    for sentence in sentences:
        if not sentence.strip():
            continue
            
        if current_sentence and not re.search(r'[.!?]$', current_sentence):
            current_sentence += ' ' + sentence
        else:
            if current_sentence:
                processed_sentences.append(current_sentence)
            current_sentence = sentence
    
    if current_sentence:
        processed_sentences.append(current_sentence)
    
    return processed_sentences

def get_chunks(text: str, chunk_size: int = 5) -> List[Tuple[str, str]]:
    """Get chunks of N words from a sentence."""
    words = text.split()
    normalized_text = normalize_for_comparison(text)
    norm_words = normalized_text.split()
    
    chunks = []
    for i in range(len(words) - chunk_size + 1):
        orig_chunk = ' '.join(words[i:i+chunk_size])
        norm_chunk = ' '.join(norm_words[i:i+chunk_size])
        chunks.append((orig_chunk, norm_chunk))
    
    return chunks

def find_matches(file1: str, file2: str, output_file: str, pdf1: str = None, pdf2: str = None):
    # Extract color information from PDFs
    colors1 = extract_text_with_colors(pdf1) if pdf1 else {}
    colors2 = extract_text_with_colors(pdf2) if pdf2 else {}
    """Find matching phrases with context."""
    def process_file(file_path: str) -> Tuple[List[str], Dict[str, str], Dict[str, int]]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        sentences = extract_sentences(content)
        chunks_map = {}
        pos_map = {sentence: i for i, sentence in enumerate(sentences)}
        
        for sentence in sentences:
            for orig_chunk, norm_chunk in get_chunks(sentence):
                if norm_chunk:
                    chunks_map[norm_chunk] = orig_chunk
        
        return sentences, chunks_map, pos_map
    
    # Use original PDF names for display if provided, otherwise use temp file names
    display_name1 = os.path.basename(pdf1) if pdf1 else os.path.basename(file1)
    display_name2 = os.path.basename(pdf2) if pdf2 else os.path.basename(file2)
    
    print(f"Verarbeite '{display_name1}'...")
    sentences1, chunks_map1, pos_map1 = process_file(file1)
    
    print(f"Verarbeite '{display_name2}'...")
    sentences2, chunks_map2, pos_map2 = process_file(file2)
    
    total1, total2 = len(chunks_map1), len(chunks_map2)
    print(f"Vergleiche {total1} relevante Sätze aus '{display_name1}' "
          f"mit {total2} relevanten Sätzen aus '{display_name2}'...")
    
    seen_matches: Set[str] = set()
    matched_sentences: Dict[str, int] = {}
    matches_found = 0
    
    # Clear output file
    with open(output_file, 'w', encoding='utf-8') as f:
        pass
    
    for chunk in sorted(chunks_map1.keys()):
        # Skip if we've seen this chunk before
        if chunk in seen_matches or chunk not in chunks_map2:
            continue
            
        seen_matches.add(chunk)
        orig_chunk1 = chunks_map1[chunk]
        orig_chunk2 = chunks_map2[chunk]
        
        # Validate chunks match after normalization
        norm_chunk1 = normalize_for_comparison(orig_chunk1)
        norm_chunk2 = normalize_for_comparison(orig_chunk2)
        
        if norm_chunk1 != norm_chunk2:
            continue
        
        # Find sentences containing the chunks
        matching_sentence1 = next((s for s in sentences1 if orig_chunk1 in s), None)
        matching_sentence2 = next((s for s in sentences2 if orig_chunk2 in s), None)
        
        # Skip if we couldn't find the matching sentences
        if not matching_sentence1 or not matching_sentence2:
            continue
        
        # Skip if we've already matched these sentences
        if matching_sentence1 in matched_sentences or matching_sentence2 in matched_sentences:
            continue
        
        # Increment match counter for valid matches
        matches_found += 1
        
        # Mark the sentences as matched
        matched_sentences[matching_sentence1] = 1
        matched_sentences[matching_sentence2] = 1
        
        i = pos_map1[matching_sentence1]
        j = pos_map2[matching_sentence2]
        
        with open(output_file, 'a', encoding='utf-8') as f:
            # Print match header
            f.write(f"=== Übereinstimmung {matches_found} ===\n")
            f.write("Gefundener Übereinstimmender Text:\n")
            # Get color information for the matching text
            fg_color1, bg_color1 = colors1.get(orig_chunk1.strip(), (None, None))
            fg_color2, bg_color2 = colors2.get(orig_chunk2.strip(), (None, None))
            
            f.write(f">>> {orig_chunk1}\n")
            if fg_color1 or bg_color1:
                f.write(f"Farbe in Datei 1: {fg_color1 or 'standard'}, Hintergrund: {bg_color1 or 'standard'}\n")
            if fg_color2 or bg_color2:
                f.write(f"Farbe in Datei 2: {fg_color2 or 'standard'}, Hintergrund: {bg_color2 or 'standard'}\n")
            f.write("\n")
            
            # Print context from first file
            f.write(f"Kontext aus '{display_name1}':\n")
            f.write("-------------------\n")
            # Two lines before match
            for k in range(i-2, i):
                if k >= 0 and k < len(sentences1):
                    f.write(f"    {sentences1[k]}\n")
            # Show complete line with the matching chunk
            f.write(f">>> {matching_sentence1}\n")
            # Two lines after match
            for k in range(i+1, i+3):
                if k < len(sentences1):
                    f.write(f"    {sentences1[k]}\n")
            
            f.write("\n")
            f.write(f"Kontext aus '{display_name2}':\n")
            f.write("-------------------\n")
            # Two lines before match
            for k in range(j-2, j):
                if k >= 0 and k < len(sentences2):
                    f.write(f"    {sentences2[k]}\n")
            # Show complete line with the matching chunk
            f.write(f">>> {matching_sentence2}\n")
            # Two lines after match
            for k in range(j+1, j+3):
                if k < len(sentences2):
                    f.write(f"    {sentences2[k]}\n")
            f.write("\n\n")
    
    print("\nVergleich abgeschlossen.")
    
    with open(output_file, 'a', encoding='utf-8') as f:
        if matches_found == 0:
            print("Keine Übereinstimmungen gefunden.")
            f.write("Keine Übereinstimmungen gefunden.\n")
        else:
            print(f"{matches_found} einzigartige Übereinstimmungen gefunden.")
            f.write(f"{matches_found} einzigartige Übereinstimmungen gefunden.\n")

def main():
    # Check arguments
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <pdf1> <pdf2>")
        sys.exit(1)
    
    # Set proper locale for German characters
    locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
    
    pdf1, pdf2 = sys.argv[1], sys.argv[2]
    output_file = "vergleich_output_py.txt"
    
    # Create temporary files
    temp_files = [tempfile.mktemp() for _ in range(6)]
    temp1, temp2 = temp_files[0:2]
    atexit.register(cleanup_temp_files, temp_files)
    
    # Check dependencies
    check_dependencies()
    
    # Extract text from PDFs
    print("Extrahiere Text aus PDF Dateien...")
    extract_text_from_pdf(pdf1, temp1)
    extract_text_from_pdf(pdf2, temp2)
    
    # Find matches
    print("Suche nach Übereinstimmungen...")
    find_matches(temp1, temp2, output_file, pdf1, pdf2)

if __name__ == "__main__":
    main()
