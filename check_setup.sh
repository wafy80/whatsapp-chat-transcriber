#!/bin/bash
# Health check script for WhatsApp Chat to PDF Transcriber

set -e

echo "🔍 Checking WhatsApp Chat to PDF Transcriber environment..."
echo ""

# Check Python
echo -n "✓ Python 3: "
python3 --version

# Check venv
if [ -d "venv" ]; then
    echo "✓ Virtual Environment: found"
else
    echo "⚠️  Virtual Environment: not found"
    echo "  Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Check dependencies
echo ""
echo "📦 Checking dependencies..."

check_package() {
    if python3 -c "import $1" 2>/dev/null; then
        echo "✓ $2"
    else
        echo "✗ $2 - MISSING"
        return 1
    fi
}

check_package "reportlab" "ReportLab"
check_package "PIL" "Pillow"
check_package "pydub" "PyDub"
check_package "whisper" "OpenAI Whisper"

# Check ffmpeg
echo ""
echo -n "✓ FFmpeg: "
if command -v ffmpeg &> /dev/null; then
    ffmpeg -version | head -1
else
    echo "⚠️  NOT FOUND - Audio transcription may not work"
fi

# Check main.py
echo ""
if [ -f "main.py" ]; then
    echo "✓ main.py: found"
else
    echo "✗ main.py: NOT FOUND"
    exit 1
fi

if [ -f "convert.sh" ]; then
    echo "✓ convert.sh: found"
else
    echo "✗ convert.sh: NOT FOUND"
    exit 1
fi

# Check example zips
echo ""
echo "📁 Available chat files:"
if ls *.zip 1> /dev/null 2>&1; then
    ls -lh *.zip | awk '{print "  " $9 " (" $5 ")"}'
else
    echo "  ⚠️  No .zip files found"
fi

echo ""
echo "✅ Setup complete! Ready to use."
echo ""
echo "Usage:"
echo "  ./convert.sh 'WhatsApp Chat.zip'"
echo "  ./convert.sh 'WhatsApp Chat.zip' -o 'output.pdf' -l en"
echo "  ./convert.sh --batch"

