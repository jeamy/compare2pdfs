# PDF Comparison Tools

This repository contains scripts for comparing text content between PDF files, with an additional capability to detect and compare text colors.

## Scripts

1. `compare-pdfs.sh` - Basic PDF text comparison
2. `compare-pdfs-color.sh` - Enhanced version that includes text color information

## Prerequisites

### Required Command-line Tools

- `pdftotext` (part of poppler-utils) - For extracting text from PDFs
- `grep` - For pattern matching
- `sed` - For text processing
- `awk` - For text processing
- `tr` - For character translation/deletion

### Additional Tools for Color Detection (`compare-pdfs-color.sh`)

- `pdfinfo` (part of poppler-utils) - For extracting PDF metadata
- `pdftoppm` (part of poppler-utils) - For converting PDF pages to images
- `convert` (part of ImageMagick) - For image processing and color extraction

### Installation

#### Ubuntu/Debian
```bash
# Install basic requirements
sudo apt-get update
sudo apt-get install poppler-utils

# For color detection script
sudo apt-get install imagemagick
```

#### macOS
```bash
# Using Homebrew
brew install poppler
brew install imagemagick
```

## Usage

### Basic Text Comparison
```bash
./compare-pdfs.sh file1.pdf file2.pdf
```
- Output will be saved to `vergleich_output.txt`
- Compares text content between PDFs
- Identifies matching phrases with context

### Text Comparison with Color Information
```bash
./compare-pdfs-color.sh file1.pdf file2.pdf
```
- Output will be saved to `vergleich_output_color.txt`
- Includes all features of the basic comparison
- Additionally extracts and compares text color information
- Appends color information to each matching line

## Output Format

### Basic Comparison (`vergleich_output.txt`)
```
Vergleichsergebnis:
===================

Übereinstimmung gefunden:
------------------------
Datei 1: [matching text from file 1]
Datei 2: [matching text from file 2]
```

### Color Comparison (`vergleich_output_color.txt`)
```
Vergleichsergebnis:
===================

Übereinstimmung gefunden:
------------------------
Datei 1: [matching text from file 1] [Color: color_info]
Datei 2: [matching text from file 2] [Color: color_info]
```

## Features

- UTF-8 support with German character handling
- Minimum word count filtering (default: 7 words)
- Context-aware sentence matching
- Bullet point handling
- Color information extraction (in color version)
- Temporary file cleanup
- Debug mode support

## Debug Mode

To run either script in debug mode (keeping temporary files):
```bash
DEBUG=1 ./compare-pdfs.sh file1.pdf file2.pdf
# or
DEBUG=1 ./compare-pdfs-color.sh file1.pdf file2.pdf
```

## Notes

- The scripts are designed to work with UTF-8 encoded PDFs
- Color detection may vary depending on PDF formatting and structure
- Large PDFs may require more processing time, especially with color detection
- Temporary files are automatically cleaned up unless running in debug mode

## Powered By

- [Windsurf](https://www.codeium.com/windsurf) - The world's first agentic IDE
- Claude 3.5 Sonnet - Anthropic's advanced AI model
