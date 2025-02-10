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
echo "Extrahiere Text aus PDF Dateien..."
pdftotext -layout -enc UTF-8 "$PDF1" "$TEMP1"
pdftotext -layout -enc UTF-8 "$PDF2" "$TEMP2"

# Function to convert text into sentences
extract_sentences() {
    local text="$1"
    echo "$text" |
        # Replace newlines with spaces, preserving paragraph breaks
        tr '\n' ' ' |
        # Normalize multiple spaces
        tr -s ' ' |
        # Add proper spacing around bullet points
        sed 's/•/\n•/g' |
        # Add newline after each sentence end, but not after abbreviations
        sed 's/\([.!?]\) \([[:upper:]]\)/\1\n\2/g' |
        # Join lines that don't end with sentence-ending punctuation
        awk 'BEGIN{RS="\n";ORS="\n"} {if(NR>1 && $0!~/^[•]/ && prev!~/[.!?]$/) printf "%s ",prev; else if(NR>1) print prev; prev=$0} END{print prev}'
}

# Function to get chunks of N words from a sentence
get_chunks() {
    local text="$1"
    local chunk_size=6
    local words=($text)
    local num_words=${#words[@]}
    local chunks=()
    
    for ((i=0; i<=num_words-chunk_size; i++)); do
        local chunk=""
        for ((j=0; j<chunk_size; j++)); do
            chunk+="${words[$((i+j))]} "
        done
        chunks+=("${chunk% }")
    done
    printf "%s\n" "${chunks[@]}"
}

# Function to normalize text for comparison
normalize_for_comparison() {
    local text="$1"
    echo "$text" |
        # First remove any invalid or replacement characters
        tr -d '\000-\011\013-\037\177\200-\377' |
        # Convert to lowercase
        tr '[:upper:]' '[:lower:]' |
        # Replace various types of dashes and hyphens with a standard one
        sed 's/[–—―­]/-/g' |
        # Remove soft hyphens and other special characters
        tr -d '­​‌‍' |
        # Remove bullet points at start
        sed 's/^[\*•‣◦⁃∙]\s*//' |
        # Normalize spaces
        tr -s ' ' |
        # Remove punctuation except periods for abbreviations
        sed 's/[,;:"""()]//g' |
        # Remove line numbers and page markers
        sed -E 's/^[0-9]+\.//' |
        # Trim whitespace
        sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'
}

# Function to find matching phrases with context
find_matches() {
    local file1="$1"
    local file2="$2"
    local output="$3"
    local matches_found=0
    declare -A seen_matches
    
    # Initialize debug file
    echo "Debug-Informationen für Vergleich" > "$DEBUG_FILE"
    echo "--------------------------------" >> "$DEBUG_FILE"
    echo "" >> "$DEBUG_FILE"
    
    # Read and pre-filter sentences
    echo "Vorverarbeitung der Sätze..."
    
    declare -A normalized_map1
    declare -A normalized_map2
    declare -A sentence_map1
    declare -A sentence_map2
    declare -A position_map1
    declare -A position_map2
    declare -a all_sentences1
    declare -a all_sentences2
    
    echo "Verarbeite '$(basename "$PDF1")'..."
    local pos=0
    while IFS= read -r sentence; do
        [ -z "${sentence// }" ] && continue
        
        all_sentences1+=("$sentence")
        
        # Log original sentence
        echo "Original: $sentence" >> "$DEBUG_FILE"
        
        # Normalize sentence
        local normalized=$(normalize_for_comparison "$sentence")
        
        # Get chunks of 5 words
        while IFS= read -r chunk; do
            [ -z "$chunk" ] && continue
            echo "Chunk: $chunk" >> "$DEBUG_FILE"
            normalized_map1["$chunk"]="$sentence"
            sentence_map1["$sentence"]="$chunk"
            position_map1["$sentence"]=$pos
        done < <(get_chunks "$normalized")
        
        echo "---" >> "$DEBUG_FILE"
        ((pos++))
    done < <(extract_sentences "$(cat "$file1")")
    
    echo "Verarbeite '$(basename "$PDF2")'..."
    pos=0
    while IFS= read -r sentence; do
        [ -z "${sentence// }" ] && continue
        
        all_sentences2+=("$sentence")
        
        # Log original sentence
        echo "Original: $sentence" >> "$DEBUG_FILE"
        
        # Normalize sentence
        local normalized=$(normalize_for_comparison "$sentence")
        
        # Get chunks of 5 words
        while IFS= read -r chunk; do
            [ -z "$chunk" ] && continue
            echo "Chunk: $chunk" >> "$DEBUG_FILE"
            normalized_map2["$chunk"]="$sentence"
            sentence_map2["$sentence"]="$chunk"
            position_map2["$sentence"]=$pos
        done < <(get_chunks "$normalized")
        
        echo "---" >> "$DEBUG_FILE"
        ((pos++))
    done < <(extract_sentences "$(cat "$file2")")
    
    local total1=${#normalized_map1[@]}
    local total2=${#normalized_map2[@]}
    echo "Vergleiche $total1 relevante Sätze aus '$(basename "$PDF1")' mit $total2 relevanten Sätzen aus '$(basename "$PDF2")'..."
    
    # Clear output file
    > "$output"
    
    # Instead of comparing every sentence with every other sentence,
    # we can just look up normalized sentences in our hash tables
    for chunk in "${!normalized_map1[@]}"; do
        # Skip if we've seen this normalized text before
        [ -n "${seen_matches[$chunk]+x}" ] && continue
        
        # Check if this normalized text exists in file 2
        if [ -n "${normalized_map2[$chunk]+x}" ]; then
            ((matches_found++))
            seen_matches["$chunk"]=1
            
            sentence1="${normalized_map1[$chunk]}"
            sentence2="${normalized_map2[$chunk]}"
            
            # Skip if we've already seen this sentence pair
            local sentence_pair="$(normalize_for_comparison "$sentence1")|||$(normalize_for_comparison "$sentence2")"
            [ -n "${seen_matches[$sentence_pair]+x}" ] && continue
            seen_matches["$sentence_pair"]=1
            
            i=${position_map1["$sentence1"]}
            j=${position_map2["$sentence2"]}
                        # Print match header
            {
                echo "=== Übereinstimmung $matches_found ==="
                echo "Gefundener Übereinstimmender Text:"
                # Find the original text that matches the normalized chunk in sentence1
                local original_chunk
                if [[ "$sentence1" =~ .*($chunk).* ]]; then
                    original_chunk="${BASH_REMATCH[1]}"
                else
                    original_chunk="$chunk"
                fi
                echo ">>> $original_chunk"
                echo ""
                
                # Print context from first file
                echo "Kontext aus '$(basename "$PDF1")':"
                echo "-------------------"
                # Two lines before match
                for ((k=i-2; k<i; k++)); do
                    if [ $k -ge 0 ]; then
                        echo "    ${all_sentences1[$k]}"
                    fi
                done
                # Show complete line with the matching chunk
                echo ">>> $sentence1"
                # Two lines after match
                for ((k=i+1; k<=i+2; k++)); do
                    if [ $k -lt ${#all_sentences1[@]} ]; then
                        echo "    ${all_sentences1[$k]}"
                    fi
                done
                
                echo ""
                echo "Kontext aus '$(basename "$PDF2")':"
                echo "-------------------"
                # Two lines before match
                for ((k=j-2; k<j; k++)); do
                    if [ $k -ge 0 ]; then
                        echo "    ${all_sentences2[$k]}"
                    fi
                done
                # Show complete line with the matching chunk
                echo ">>> $sentence2"
                # Two lines after match
                for ((k=j+1; k<=j+2; k++)); do
                    if [ $k -lt ${#all_sentences2[@]} ]; then
                        echo "    ${all_sentences2[$k]}"
                    fi
                done
                echo ""
                echo ""
            } >> "$output"
        fi
    done
    
    echo -e "\nVergleich abgeschlossen."
    
    if [ "$matches_found" -eq 0 ]; then
        echo "Keine Übereinstimmungen gefunden."
        echo "Keine Übereinstimmungen gefunden." >> "$output"
    else
        echo "$matches_found einzigartige Übereinstimmungen gefunden."
        echo "$matches_found einzigartige Übereinstimmungen gefunden." >> "$output"
    fi
}

# Process files and find matches
echo "Suche nach Übereinstimmungen..."
find_matches "$TEMP1" "$TEMP2" "$OUTPUT_FILE"

echo "Ergebnis wurde in $OUTPUT_FILE gespeichert."
echo "Debug-Informationen wurden in $DEBUG_FILE gespeichert."
