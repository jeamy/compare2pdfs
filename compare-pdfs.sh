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
    local chunk_size=5
    local -a words
    read -ra words <<< "$text"
    local num_words=${#words[@]}
    
    # Pre-normalize the entire text once
    local normalized_text=$(normalize_for_comparison "$text")
    local -a norm_words
    read -ra norm_words <<< "$normalized_text"
    
    local result=()
    for ((i=0; i<=num_words-chunk_size; i++)); do
        local orig_chunk=""
        local norm_chunk=""
        for ((j=0; j<chunk_size; j++)); do
            orig_chunk+="${words[$((i+j))]} "
            norm_chunk+="${norm_words[$((i+j))]} "
        done
        echo "${orig_chunk% }|${norm_chunk% }"
    done
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
    declare -A matched_sentences
    
    # Declare an associative array to track matched sentences
    declare -A matched_sentences

    # Read and pre-filter sentences
    echo "Vorverarbeitung der Sätze..."
    
    declare -A chunks_map1 chunks_map2
    declare -a all_sentences1 all_sentences2
    declare -A pos_map1 pos_map2
    
    process_file() {
        local file="$1"
        local -n _sentences="$2"
        local -n _chunks_map="$3"
        local -n _pos_map="$4"
        
        local content=$(cat "$file")
        local pos=0
        
        while IFS= read -r sentence; do
            [ -z "${sentence// }" ] && continue
            _sentences+=("$sentence")
            _pos_map["$sentence"]=$pos
            
            while IFS='|' read -r orig_chunk norm_chunk; do
                [ -z "$norm_chunk" ] && continue
                _chunks_map["$norm_chunk"]="$orig_chunk"
            done < <(get_chunks "$sentence")
            
            ((pos++))
        done < <(extract_sentences "$content")
    }
    
    echo "Verarbeite '$(basename "$PDF1")'..."
    process_file "$file1" all_sentences1 chunks_map1 pos_map1
    
    echo "Verarbeite '$(basename "$PDF2")'..."
    process_file "$file2" all_sentences2 chunks_map2 pos_map2
    
    local total1=${#chunks_map1[@]}
    local total2=${#chunks_map2[@]}
    echo "Vergleiche $total1 relevante Sätze aus '$(basename "$PDF1")' mit $total2 relevanten Sätzen aus '$(basename "$PDF2")'..."
    
    # Clear output file
    > "$output"
    
    # Initialize counters
    local matches_found=0
    
    # Create sorted arrays for faster lookup
    readarray -t sorted_chunks1 < <(printf '%s\n' "${!chunks_map1[@]}" | sort)
    
    # Compare chunks using sorted array
    for chunk in "${sorted_chunks1[@]}"; do
        # Skip if we've seen this chunk before
        [ -n "${seen_matches[$chunk]+x}" ] && continue
        
        # Check if this chunk exists in file 2
        if [ -n "${chunks_map2[$chunk]+x}" ]; then
            seen_matches["$chunk"]=1
            
            # Find matching sentences
            local orig_chunk1="${chunks_map1[$chunk]}"
            local orig_chunk2="${chunks_map2[$chunk]}"
            local i j matching_sentence1 matching_sentence2
            
            # Debug output
            #echo "Checking chunk: $chunk" >&2
            #echo "Original chunk 1: $orig_chunk1" >&2
            #echo "Original chunk 2: $orig_chunk2" >&2
            
            # Validate that both chunks exist and match after normalization
            local norm_chunk1=$(normalize_for_comparison "$orig_chunk1")
            local norm_chunk2=$(normalize_for_comparison "$orig_chunk2")
            
            if [[ "$norm_chunk1" != "$norm_chunk2" ]]; then
                #echo "Chunks don't match after normalization:" >&2
                #echo "Norm 1: $norm_chunk1" >&2
                #echo "Norm 2: $norm_chunk2" >&2
                continue
            fi
            
            # Find sentences containing the chunks
            for sentence in "${all_sentences1[@]}"; do
                if [[ "$sentence" == *"$orig_chunk1"* ]]; then
                    i=${pos_map1["$sentence"]}
                    matching_sentence1="$sentence"
                    break
                fi
            done
            
            for sentence in "${all_sentences2[@]}"; do
                if [[ "$sentence" == *"$orig_chunk2"* ]]; then
                    j=${pos_map2["$sentence"]}
                    matching_sentence2="$sentence"
                    break
                fi
            done
            
            # Skip if we couldn't find the matching sentences
            if [ -z "$matching_sentence1" ] || [ -z "$matching_sentence2" ]; then
                echo "Could not find matching sentences:" >&2
                echo "Sentence 1 found: ${matching_sentence1:-none}" >&2
                echo "Sentence 2 found: ${matching_sentence2:-none}" >&2
                continue
            fi
            
            # Skip if we've already matched these sentences
            if [[ -n "${matched_sentences[$matching_sentence1]+x}" || -n "${matched_sentences[$matching_sentence2]+x}" ]]; then
                continue
            fi
            
            # Increment match counter for valid matches
            ((matches_found++))
            
            # Mark the sentences as matched
            matched_sentences[$matching_sentence1]=1
            matched_sentences[$matching_sentence2]=1
            
            # Print match header
            {
                echo "=== Übereinstimmung $matches_found ==="
                echo "Gefundener Übereinstimmender Text:"
                echo ">>> $orig_chunk1"
                echo ""
                
                # Print context from first file
                echo "Kontext aus '$(basename "$PDF1")':"
                echo "-------------------"
                # Two lines before match
                for ((k=i-2; k<i; k++)); do
                    if [ $k -ge 0 ] && [ -n "${all_sentences1[$k]}" ]; then
                        echo "    ${all_sentences1[$k]}"
                    fi
                done
                # Show complete line with the matching chunk
                echo ">>> $matching_sentence1"
                # Two lines after match
                for ((k=i+1; k<=i+2; k++)); do
                    if [ $k -lt ${#all_sentences1[@]} ] && [ -n "${all_sentences1[$k]}" ]; then
                        echo "    ${all_sentences1[$k]}"
                    fi
                done
                
                echo ""
                echo "Kontext aus '$(basename "$PDF2")':"
                echo "-------------------"
                # Two lines before match
                for ((k=j-2; k<j; k++)); do
                    if [ $k -ge 0 ] && [ -n "${all_sentences2[$k]}" ]; then
                        echo "    ${all_sentences2[$k]}"
                    fi
                done
                # Show complete line with the matching chunk
                echo ">>> $matching_sentence2"
                # Two lines after match
                for ((k=j+1; k<=j+2; k++)); do
                    if [ $k -lt ${#all_sentences2[@]} ] && [ -n "${all_sentences2[$k]}" ]; then
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
