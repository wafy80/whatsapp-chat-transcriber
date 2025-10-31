#!/bin/bash
# WhatsApp Chat to PDF Converter - Wrapper Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Show help if requested
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "WhatsApp Chat to PDF Converter"
    echo ""
    echo "Single file mode:"
    echo "  ./convert.sh <zip_file> [-o output.pdf] [-l language]"
    echo ""
    echo "Batch mode:"
    echo "  ./convert.sh --batch [-l language] [--pattern '*.zip'] [--skip-existing]"
    echo ""
    echo "Examples:"
    echo "  # Single file"
    echo "  ./convert.sh 'Chat.zip'"
    echo "  ./convert.sh 'Chat.zip' -o 'output.pdf' -l it"
    echo ""
    echo "  # Batch mode (all .zip files)"
    echo "  ./convert.sh --batch"
    echo "  ./convert.sh --batch -l it"
    echo "  ./convert.sh --batch --skip-existing"
    echo ""
    echo "For more help:"
    echo "  python3 main.py --help"
    exit 0
fi

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q reportlab pillow pydub openai-whisper
else
    source venv/bin/activate
fi

# Run the converter with all arguments
python3 main.py "$@"
