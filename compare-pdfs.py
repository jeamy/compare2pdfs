#!/usr/bin/env python3

import sys
import os
import tempfile
import subprocess
import locale
import re
from typing import List, Dict, Set, Tuple, Optional
import atexit
import fitz  # PyMuPDF
from math import sqrt

# Common color names and their RGB values (in percentage)
COLOR_MAP = {
    'Schwarz': (0, 0, 0),
    'Weiß': (100, 100, 100),
    'Rot': (100, 0, 0),
    'Grün': (0, 100, 0),
    'Blau': (0, 0, 100),
    'Gelb': (100, 100, 0),
    'Magenta': (100, 0, 100),
    'Cyan': (0, 100, 100),
    'Grau': (50, 50, 50),
    'Dunkelgrau': (25, 25, 25),
    'Hellgrau': (75, 75, 75),
    'Orange': (100, 65, 0),
    'Braun': (65, 32, 0),
    'Violett': (50, 0, 50),
    'Rosa': (100, 75, 75),
}

def int_to_rgb_percent(color_int):
    """Convert an integer color value to RGB percentages."""
    if isinstance(color_int, (tuple, list)):
        return [round(c * 100, 1) for c in color_int[:3]]
    
    # Convert integer to RGB values
    b = (color_int & 255) / 255.0 * 100
    g = ((color_int >> 8) & 255) / 255.0 * 100
    r = ((color_int >> 16) & 255) / 255.0 * 100
    return [r, g, b]

def rgb_to_color_name(rgb_percent):
    """Convert RGB percentages to the closest color name."""
    def color_distance(c1, c2):
        return sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))
    
    closest_color = min(COLOR_MAP.items(), key=lambda x: color_distance(rgb_percent, x[1]))
    return closest_color[0]

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

def get_text_colors(pdf_path: str, text: str) -> Tuple[Optional[str], Optional[str]]:
    """Get foreground and background colors for text in PDF.
    Returns a tuple of (text_color, background_color) where each color is the name
    of the color found in the exact location of the matched text.
    """
    try:
        doc = fitz.open(pdf_path)
        
        # Normalize the search text
        normalized_text = normalize_for_comparison(text)
        
        for page in doc:
            # Get text instances with their properties
            text_instances = page.search_for(text, quads=True)  # Use quads for more precise location
            if not text_instances:
                continue
                
            # Get all page elements
            blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_SPANS)["blocks"]
            drawings = page.get_drawings()
            
            # Process background rectangles
            colored_rects = []
            for drawing in drawings:
                if 'items' in drawing and drawing.get('fill'):
                    fill_color = drawing.get('fill')
                    if fill_color != (1,1,1):  # Skip pure white backgrounds
                        for item in drawing['items']:
                            if item[0] == 're':  # Rectangle
                                rect = fitz.Rect(item[1])
                                colored_rects.append((rect, fill_color))
            
            # For each instance of the exact text match
            for inst in text_instances:
                match_rect = inst.rect  # Get precise rectangle of match
                text_color = None
                bg_color = None
                
                # Find the exact span containing our text
                for block in blocks:
                    if not text_color:  # Continue until we find the text color
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                span_rect = fitz.Rect(span["bbox"])
                                # Check if this span contains our match
                                if match_rect.intersects(span_rect):
                                    span_text = normalize_for_comparison(span["text"])
                                    if normalized_text in span_text:
                                        if "color" in span:
                                            color_val = span["color"]
                                            rgb_percent = int_to_rgb_percent(color_val)
                                            text_color = rgb_to_color_name(rgb_percent)
                
                # Find the most specific background color
                smallest_area = float('inf')
                for bg_rect, color in colored_rects:
                    if match_rect.intersects(bg_rect):
                        # Calculate intersection area to find most specific background
                        intersection = match_rect.intersect(bg_rect)
                        area = intersection.get_area()
                        if area < smallest_area:
                            smallest_area = area
                            rgb_percent = int_to_rgb_percent(color)
                            bg_color = rgb_to_color_name(rgb_percent)
                
                if text_color or bg_color:
                    doc.close()
                    return text_color, bg_color
                
        doc.close()
        return None, None
    except Exception as e:
        print(f"Warning: Color detection failed: {e}")
        return None, None

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
            f.write(f">>> {orig_chunk1}\n\n")
            
            # Print context from first file
            f.write(f"Kontext aus '{display_name1}':\n")
            f.write("-------------------\n")
            # Add color information if PDF path is available
            if pdf1:
                text_color, bg_color = get_text_colors(pdf1, orig_chunk1)
                color_info = []
                if text_color and text_color != 'Schwarz':
                    color_info.append(f"Textfarbe: {text_color}")
                if bg_color and bg_color != 'Schwarz':
                    color_info.append(f"Hintergrund: {bg_color}")
                if color_info:
                    f.write(f"Farben: {' | '.join(color_info)}\n")
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
            # Add color information if PDF path is available
            if pdf2:
                text_color, bg_color = get_text_colors(pdf2, orig_chunk2)
                color_info = []
                if text_color and text_color != 'Schwarz':
                    color_info.append(f"Textfarbe: {text_color}")
                if bg_color and bg_color != 'Schwarz':
                    color_info.append(f"Hintergrund: {bg_color}")
                if color_info:
                    f.write(f"Farben: {' | '.join(color_info)}\n")
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