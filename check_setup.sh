#!/bin/bash
# Health check script for WhatsApp Chat to PDF Converter

set -e

echo "🔍 Verificando ambiente WhatsApp Chat to PDF Converter..."
echo ""

# Check Python
echo -n "✓ Python 3: "
python3 --version

# Check venv
if [ -d "venv" ]; then
    echo "✓ Virtual Environment: trovato"
else
    echo "⚠️  Virtual Environment: non trovato"
    echo "  Esegui: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Check dependencies
echo ""
echo "📦 Verificando dipendenze..."

check_package() {
    if python3 -c "import $1" 2>/dev/null; then
        echo "✓ $2"
    else
        echo "✗ $2 - MANCANTE"
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
    echo "⚠️  NON TROVATO - Audio transcription potrebbe non funzionare"
fi

# Check main.py
echo ""
if [ -f "main.py" ]; then
    echo "✓ main.py: trovato"
else
    echo "✗ main.py: NON TROVATO"
    exit 1
fi

if [ -f "convert.sh" ]; then
    echo "✓ convert.sh: trovato"
else
    echo "✗ convert.sh: NON TROVATO"
    exit 1
fi

# Check example zips
echo ""
echo "📁 File di esempio disponibili:"
if ls *.zip 1> /dev/null 2>&1; then
    ls -lh *.zip | awk '{print "  " $9 " (" $5 ")"}'
else
    echo "  ⚠️  Nessun file .zip trovato"
fi

echo ""
echo "✅ Setup completato! Pronto per l'uso."
echo ""
echo "Uso:"
echo "  ./convert.sh 'Chat WhatsApp.zip'"
echo "  ./convert.sh 'Chat WhatsApp.zip' 'output.pdf'"
