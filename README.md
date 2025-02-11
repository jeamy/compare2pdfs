# PDF Comparison Tools

This repository contains scripts for comparing text content between PDF files. Available in both Shell and Python implementations.

## Scripts

- `compare-pdfs.sh` - Shell script version for comparing PDF files
- `compare-pdfs.py` - Python version with identical functionality

## Prerequisites

### Required Tools

#### For Shell Script Version
- `pdftotext` (from poppler-utils package)
- `bash` (version 4 or higher)
- Standard Unix tools:
  - `grep` - For pattern matching
  - `sed` - For text processing
  - `awk` - For text processing
  - `sort` - For sorting chunks
  - `uniq` - For removing duplicates
  - `tr` - For character translation/deletion

#### For Python Version
- Python 3.8 or higher
- `pdftotext` (from poppler-utils package)
- Python virtual environment (recommended)

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

### Linux Distributions

#### Ubuntu/Debian
```bash
# Install required packages
sudo apt-get update
sudo apt-get install poppler-utils python3 python3-venv python3-pip

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Fedora
```bash
# Install required packages
sudo dnf update
sudo dnf install poppler-utils python3 python3-pip

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Arch Linux
```bash
# Install required packages
sudo pacman -Syu
sudo pacman -S poppler python python-pip

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### openSUSE
```bash
# Install required packages
sudo zypper refresh
sudo zypper install poppler-tools python3 python3-pip

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### CentOS/RHEL
```bash
# Install EPEL repository if not already installed
sudo dnf install epel-release

# Install required packages
sudo dnf update
sudo dnf install poppler-utils python3 python3-pip

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### macOS

#### Using Homebrew (Recommended)
```bash
# Install required tools
brew install poppler python@3.11

# Set up Python environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Using Python.org Installer
1. Download and install Python from [python.org](https://www.python.org/downloads/macos/)
2. Install poppler using Homebrew:
   ```bash
   brew install poppler
   ```
3. Set up Python environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

#### For Shell Script Version
```bash
brew install poppler
brew install coreutils  # For GNU tools

# Optional: Add GNU tools to PATH
echo 'export PATH="/usr/local/opt/coreutils/libexec/gnubin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Windows

#### Option 1: Using WSL (Recommended)
1. Install WSL (Windows Subsystem for Linux):
   - Open PowerShell as Administrator and run:
     ```powershell
     wsl --install
     ```
   - After installation, restart your computer

2. Open Ubuntu on WSL and run:
   ```bash
   # Install required packages
   sudo apt-get update
   sudo apt-get install poppler-utils python3 python3-venv python3-pip

   # Set up Python environment
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

#### Option 2: Native Windows Installation
1. Install Python:
   - Download and install Python from [python.org](https://www.python.org/downloads/windows/)
   - During installation, check "Add Python to PATH"

2. Install poppler:
   - Download the latest poppler release for Windows from [poppler releases](https://github.com/oschwartz10612/poppler-windows/releases/)
   - Extract the downloaded file
   - Add the `bin` directory to your system PATH:
     - Open System Properties → Advanced → Environment Variables
     - Edit the Path variable
     - Add the full path to poppler's bin directory

3. Set up Python environment:
   ```cmd
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   .\venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   ```

#### Option 3: Using Git Bash or Cygwin
1. Install Git Bash or Cygwin
2. During installation, select the following packages:
   - python3
   - python3-pip
   - poppler
   - poppler-utils

3. Set up Python environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Usage

### Shell Script Version
```bash
# Make the script executable
chmod +x compare-pdfs.sh

# Run the comparison
./compare-pdfs.sh <pdf1> <pdf2>
```

### Python Version

#### Linux/macOS
```bash
# Make the script executable
chmod +x compare-pdfs.py

# Activate virtual environment (if not already activated)
source venv/bin/activate

# Run the comparison
./compare-pdfs.py <pdf1> <pdf2>
```

#### Windows (CMD)
```cmd
# Activate virtual environment
.\venv\Scripts\activate

# Run the comparison
python compare-pdfs.py <pdf1> <pdf2>
```

#### Windows (PowerShell)
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run the comparison
python compare-pdfs.py <pdf1> <pdf2>
```

#### Windows (Git Bash/Cygwin)
```bash
# Activate virtual environment
source venv/Scripts/activate

# Run the comparison
python compare-pdfs.py <pdf1> <pdf2>
```

### Example
```bash
# Shell version
./compare-pdfs.sh document1.pdf document2.pdf

# Python version
./compare-pdfs.py document1.pdf document2.pdf
```

### Output
- Shell script version saves results to `vergleich_output.txt`
- Python version saves results to `vergleich_output_py.txt`
- Python version includes color information for matched text
- Output format:
  ```
  === Übereinstimmung N ===
  Gefundener Übereinstimmender Text:
  >>> [matching text]

  Kontext aus '[filename1]':
  -------------------
  Farben: [Textfarbe: Rot | Hintergrund: Gelb]  # Only shown if non-black colors are found
  [2 lines before]
  >>> [matching line]
  [2 lines after]

  Kontext aus '[filename2]':
  -------------------
  Farben: [Textfarbe: Blau]  # Only shown if non-black colors are found
  [2 lines before]
  >>> [matching line]
  [2 lines after]
  ```

  Color information (Python version only):
  - Only available in the Python implementation
  - Shows text and background colors when they are non-black
  - Colors are detected at the exact location of matched text
  - Available colors include: Rot, Grün, Blau, Gelb, Magenta, Cyan, Orange, Braun, Violett, Rosa, and various shades of Grau
  - Shell script version does not include color information

### Features
- Intelligent text extraction from PDFs
- Robust handling of special characters and German umlauts
- Context-aware matching with surrounding text
- Duplicate detection and elimination
- Progress indicators during processing
- Proper handling of bullet points and formatting

### Requirements File
The Python version requires additional packages listed in `requirements.txt`. Install them using:
```bash
pip install -r requirements.txt
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
- LLM babysitting by a human in a virtual environment