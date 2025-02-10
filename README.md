# PDF Comparison Tools

This repository contains a script for comparing text content between PDF files.

## Script

`compare-pdfs.sh` - Compares text content between PDF files

## Prerequisites

### Required Tools
- `pdftotext` (from poppler-utils package)
- `bash` (version 4 or higher)
- Standard Unix tools:
  - `grep` - For pattern matching
  - `sed` - For text processing
  - `awk` - For text processing
  - `sort` - For sorting chunks
  - `uniq` - For removing duplicates
  - `tr` - For character translation/deletion

### Installation on Ubuntu/Debian
```bash
sudo apt-get install poppler-utils
```

## Usage

### Command Line
```bash
./compare-pdfs.sh <pdf1> <pdf2>
```

### Example
```bash
./compare-pdfs.sh document1.pdf document2.pdf
```

### Output
- Results are saved to `vergleich_output.txt`
- Each match is formatted as:
  ```
  === Übereinstimmung N ===
  Gefundener Übereinstimmender Text:
  >>> [matching text]

  Kontext in Datei 1:
  [previous lines]
  [matching line]
  [following lines]

  Kontext in Datei 2:
  [previous lines]
  [matching line]
  [following lines]
  ```

### Features
- Identifies matching text passages between two PDF documents
- Shows context around each match (lines before and after)
- Handles German characters and special formatting
- Ignores duplicate matches to reduce redundancy
- Uses 5-word chunks for comparison to balance accuracy and performance

## Notes

- The scripts are designed to work with UTF-8 encoded PDFs
- Temporary files are automatically cleaned up unless running in debug mode

## Powered By

- [Windsurf](https://www.codeium.com/windsurf) - The world's first agentic IDE
- Claude 3.5 Sonnet - Anthropic's advanced AI model
