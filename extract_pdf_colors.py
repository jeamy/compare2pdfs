#!/usr/bin/env python3
import fitz  # PyMuPDF

def find_text_and_colors(pdf_path, search_text, target_page=3):  # 0-based index for page 4
    """Find text locations and check for colored sections behind them."""
    try:
        # Open the PDF
        doc = fitz.open(pdf_path)
        page = doc[target_page]
        
        # Split search text into smaller chunks for better matching
        words = search_text.split()
        search_chunks = [' '.join(words[i:i+3]) for i in range(0, len(words), 3)]
        
        # First get all the drawings that might be backgrounds
        drawings = page.get_drawings()
        colored_rects = []
        
        # Look for any colored rectangles
        for drawing in drawings:
            if 'items' in drawing and drawing.get('fill') and drawing.get('fill') != (1,1,1):  # Any non-white fill
                for item in drawing['items']:
                    if item[0] == 're':  # Rectangle
                        rect = fitz.Rect(item[1])
                        colored_rects.append((rect, drawing['fill']))
        
        print(f"Found {len(colored_rects)} colored background rectangles")
        for i, (rect, color) in enumerate(colored_rects):
            rgb_percent = [round(c * 100, 1) for c in color[:3]]
            print(f"Background {i+1}: RGB({rgb_percent[0]}%, {rgb_percent[1]}%, {rgb_percent[2]}%)")
        
        # Now search for text and check its properties
        found_text = False
        for chunk in search_chunks:
            # Get text instances with their properties
            text_instances = page.search_for(chunk)
            blocks = page.get_text("dict")["blocks"]
            
            if text_instances:
                found_text = True
                for rect in text_instances:
                    found_bg = False
                    print(f"\nText: '{chunk}'")
                    print(f"Location: {rect}")
                    
                    # Find the text color by matching location with blocks
                    text_color = None
                    for block in blocks:
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                span_rect = fitz.Rect(span["bbox"])
                                if rect.intersects(span_rect) and chunk.lower() in span["text"].lower():
                                    if "color" in span:
                                        color_val = span["color"]
                                        if isinstance(color_val, (tuple, list)):
                                            rgb_percent = [round(c * 100, 1) for c in color_val[:3]]
                                            text_color = f"RGB({rgb_percent[0]}%, {rgb_percent[1]}%, {rgb_percent[2]}%)"
                                        elif isinstance(color_val, (int, float)):
                                            text_color = f"Grayscale: {round(color_val * 100, 1)}%"
                                    break
                    
                    if text_color:
                        print(f"Text color: {text_color}")
                    else:
                        print("Text color: Not found")
                    
                    # Check background color
                    for bg_rect, color in colored_rects:
                        if rect.intersects(bg_rect):
                            found_bg = True
                            rgb_percent = [round(c * 100, 1) for c in color[:3]]
                            print(f"Background color: RGB({rgb_percent[0]}%, {rgb_percent[1]}%, {rgb_percent[2]}%)")
                            print(f"Background area: {bg_rect}")
                    
                    if not found_bg:
                        print("No colored background found")
        
        if not found_text:
            print("No matching text found on page 4")
        
        doc.close()
        
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        if doc:
            doc.close()
        
        doc.close()
        
        # Convert colors to RGB percentages
        rgb_colors = []
        for color in all_colors:
            if len(color) >= 3:  # Ensure we have at least RGB values
                rgb = [round(c * 100, 1) for c in color[:3]]  # Convert to percentages
                rgb_colors.append(rgb)
        
        if rgb_colors:
            print("\nBackground colors found (RGB percentages):")
            for rgb in rgb_colors:
                print(f"R: {rgb[0]}%, G: {rgb[1]}%, B: {rgb[2]}%")
        else:
            print("No background colors found")
            
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")

if __name__ == "__main__":
    pdf_path = "protokoll-oevp-spoe-neos.pdf"
    # First check page 4
    search_text = """SPÖ: Durchrechnungszeiträume für Arbeitszeiten im Tourismus gesetzlich von 26 Wochen auf maximal 13 Wochen verkürzen und damit die Verkürzung der Vorlage von Arbeitszeitaufzeichnungen bei Kontrollen des Arbeitsinspektorat zu erreichen."""
    find_text_and_colors(pdf_path, search_text)
    
    # Then check page 5
    print("\n\nSearching page 5 for (BUDGETRELEVANT)...")
    find_text_and_colors(pdf_path, "(BUDGETRELEVANT)", target_page=4)
