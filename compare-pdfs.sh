#!/bin/bash

# Check if we have the required number of arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <pdf1> <pdf2>"
    exit 1
fi

# Set proper locale for German characters
export LANG=de_DE.UTF-8
export LC_ALL=de_DE.UTF-8

PDF1="$1"
PDF2="$2"
MIN_WORDS=3
OUTPUT_FILE="vergleich_output.txt"
DEBUG_FILE="debug_output.txt"

# Create temporary files
TEMP1=$(mktemp)
TEMP2=$(mktemp)
NORMALIZED1=$(mktemp)
NORMALIZED2=$(mktemp)
DEBUG1=$(mktemp)
DEBUG2=$(mktemp)

# Function to clean up temporary files
cleanup() {
    if [ "${DEBUG:-0}" != "1" ]; then
        rm -f "$TEMP1" "$TEMP2" "$NORMALIZED1" "$NORMALIZED2" "$DEBUG1" "$DEBUG2"
    fi
}

# Set up trap to clean temporary files on script exit
trap cleanup EXIT

# Check if required tools are available
for cmd in pdftotext grep sed awk; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: $cmd is not installed."
        exit 1
    fi
done

# Extract text from PDFs with UTF-8 encoding
pdftotext -layout -enc UTF-8 "$PDF1" "$TEMP1"
pdftotext -layout -enc UTF-8 "$PDF2" "$TEMP2"

# Function to normalize text while preserving important phrases
normalize_text() {
    local text="$1"
    echo "$text" |
        # Replace various types of dashes and hyphens with a standard one
        sed 's/[–—―]/\-/g' |
        # Normalize spaces around dashes
        sed 's/ \- /\-/g' |
        # Remove line numbers and page markers
        sed -E 's/^[0-9]+\.//' |
        sed -E 's/^Page-[0-9]+$//' |
        # Remove bullet points and list markers
        sed -E 's/^[[:space:]]*[-•·\*○●♦][[:space:]]*//' |
        sed -E 's/^[[:space:]]*[0-9]+[\.\)][[:space:]]*//' |
        sed -E 's/^[[:space:]]*[a-zäöüA-ZÄÖÜ][\.\)][[:space:]]*//' |
        # Normalize spaces
        tr -s '[:space:]' ' ' |
        # Trim whitespace
        sed 's/^[[:space:]]*//;s/[[:space:]]*$//'
}

# Process each file line by line
process_file() {
    local infile="$1"
    local outfile="$2"
    local debugfile="$3"
    local buffer=""
    local line_count=0
    local total_lines=$(wc -l < "$infile")
    
    > "$debugfile"  # Clear debug file
    
    while IFS= read -r line || [ -n "$line" ]; do
        ((line_count++))
        echo -ne "Verarbeite Zeile $line_count von $total_lines\r"
        
        # Skip empty lines
        [ -z "${line// }" ] && continue
        
        # Normalize the line
        local normalized_line=$(normalize_text "$line")
        [ -z "$normalized_line" ] && continue
        
        # Add to buffer if line doesn't end with sentence-ending punctuation
        if [[ ! "$normalized_line" =~ [.!?]$ && -n "$normalized_line" ]]; then
            if [ -n "$buffer" ]; then
                buffer="$buffer $normalized_line"
            else
                buffer="$normalized_line"
            fi
            continue
        elif [ -n "$buffer" ]; then
            normalized_line="$buffer $normalized_line"
            buffer=""
        fi
        
        # Count words
        local word_count=$(echo "$normalized_line" | wc -w)
        
        # Store lines that meet minimum word count
        if [ "$word_count" -ge "$MIN_WORDS" ]; then
            echo "$normalized_line" >> "$outfile"
            # Store debug info
            echo "Line $line_count: $normalized_line" >> "$debugfile"
        fi
    done < "$infile"
    
    # Handle any remaining buffer content
    if [ -n "$buffer" ]; then
        local word_count=$(echo "$buffer" | wc -w)
        if [ "$word_count" -ge "$MIN_WORDS" ]; then
            echo "$buffer" >> "$outfile"
            echo "Buffer: $buffer" >> "$debugfile"
        fi
    fi
    
    # Sort and remove duplicates while preserving German characters
    LC_ALL=de_DE.UTF-8 sort -u -o "$outfile" "$outfile"
}

# Process both files
echo "Processing $PDF1..."
process_file "$TEMP1" "$NORMALIZED1" "$DEBUG1"
echo "Processing $PDF2..."
process_file "$TEMP2" "$NORMALIZED2" "$DEBUG2"

# Clear output file
> "$OUTPUT_FILE"

echo "Vergleiche PDFs und extrahiere Kontext..."

# Function to normalize for comparison
normalize_for_comparison() {
    echo "$1" |
        # Convert to lowercase
        tr '[:upper:]' '[:lower:]' |
        # Replace umlauts with base characters
        sed 's/ä/a/g; s/ö/o/g; s/ü/u/g; s/ß/ss/g' |
        # Remove line numbers and references
        sed -E 's/^[0-9]+[\.:]//g' |
        # Remove party tags and annotations
        sed -E 's/\([^)]*\)//g' |
        sed -E 's/(ovp|spoe|neos|fpoe)://g' |
        sed -E 's/-[[:space:]]*[[:alpha:]]+[[:space:]]*dagegen//g' |
        # Remove bullet points and formatting
        sed -E 's/^[[:space:]]*[o−▪•·\*○●♦]([[:space:]]|$)//g' |
        # Normalize spaces and punctuation
        tr -s '[:space:]' ' ' |
        # Remove remaining punctuation except periods
        sed 's/[,;:]/ /g' |
        # Trim
        sed 's/^[[:space:]]*//;s/[[:space:]]*$//'
}

# Function to find matching phrases
find_matches() {
    local file1="$1"
    local file2="$2"
    local output="$3"
    local min_words=3
    
    > "$output"
    
    while IFS= read -r line1; do
        # Skip empty lines
        [ -z "${line1// }" ] && continue
        
        # Normalize the line
        local norm_line1=$(normalize_for_comparison "$line1")
        [ -z "$norm_line1" ] && continue
        
        while IFS= read -r line2; do
            [ -z "${line2// }" ] && continue
            local norm_line2=$(normalize_for_comparison "$line2")
            [ -z "$norm_line2" ] && continue
            
            # Find common phrases
            if [ ${#norm_line1} -gt 20 ] && [ ${#norm_line2} -gt 20 ]; then
                # Split into words and compare
                for phrase in $(echo "$norm_line1" | tr ' ' '\n'); do
                    if echo "$norm_line2" | grep -q -F "$phrase"; then
                        local context=$(echo "$norm_line2" | grep -o -E ".{0,30}$phrase.{0,30}")
                        if [ "$(echo "$context" | wc -w)" -ge "$min_words" ]; then
                            echo "Match found:" >> "$output"
                            echo "File 1: $line1" >> "$output"
                            echo "File 2: $line2" >> "$output"
                            echo "Matching context: $context" >> "$output"
                            echo "---" >> "$output"
                        fi
                    fi
                done
            fi
        done < "$file2"
    done < "$file1"
}

# Compare files
echo "Suche nach Übereinstimmungen..."
find_matches "$NORMALIZED1" "$NORMALIZED2" "$OUTPUT_FILE"

echo "Ergebnis wurde in $OUTPUT_FILE gespeichert."
echo "Debug-Informationen wurden in $DEBUG_FILE gespeichert."
