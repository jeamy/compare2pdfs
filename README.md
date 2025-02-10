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

## Notes

- The scripts are designed to work with UTF-8 encoded PDFs
- Color detection may vary depending on PDF formatting and structure
- Large PDFs may require more processing time, especially with color detection
- Temporary files are automatically cleaned up unless running in debug mode

## Powered By

- [Windsurf](https://www.codeium.com/windsurf) - The world's first agentic IDE
- Claude 3.5 Sonnet - Anthropic's advanced AI model
