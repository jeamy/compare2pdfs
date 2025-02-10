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

## Platform Compatibility

### Linux
- Native support
- All required tools are readily available through package managers

### macOS
- Supported through Homebrew
- Requires installation of GNU tools

### Windows
- Can be run using Windows Subsystem for Linux (WSL)
- Alternatively, can use Git Bash or Cygwin with required packages

## Installation

### Ubuntu/Debian Linux
```bash
sudo apt-get install poppler-utils
```

### macOS (using Homebrew)
```bash
# Install required tools
brew install poppler
brew install coreutils  # For GNU tools

# Optional: Add GNU tools to PATH
echo 'export PATH="/usr/local/opt/coreutils/libexec/gnubin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Windows
1. Install WSL (Windows Subsystem for Linux):
   - Open PowerShell as Administrator and run:
     ```powershell
     wsl --install
     ```
   - After installation, restart your computer
   - Open Ubuntu on WSL and run:
     ```bash
     sudo apt-get update
     sudo apt-get install poppler-utils
     ```

2. Alternative: Using Git Bash or Cygwin
   - Install Git Bash or Cygwin
   - Install required packages through the package manager
   - Ensure `pdftotext` and GNU tools are available

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

- The script is designed to work with UTF-8 encoded PDFs
- Temporary files are automatically cleaned up unless running in debug mode
- On Windows, use forward slashes (/) in file paths when using WSL
- On macOS, ensure GNU versions of tools are being used (installed via Homebrew)
- Performance may vary depending on PDF size and system resources

## Powered By

- [Windsurf](https://www.codeium.com/windsurf) - The world's first agentic IDE
- Claude 3.5 Sonnet - Anthropic's advanced AI model
