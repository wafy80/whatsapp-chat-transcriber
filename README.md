# WhatsApp Chat to PDF Transcriber

Convert WhatsApp chat exports to beautifully formatted PDFs with automatic audio transcription using AI.

## ✨ Features

- 📝 **Automatic message parsing** from WhatsApp exports
- 🎙️ **AI-powered audio transcription** using OpenAI Whisper
- 🖼️ **Embedded images** directly in PDF
- 📎 **Media file references** (documents, videos)
- 🌍 **100+ languages supported** (auto-detect or manual selection)
- ⚙️ **Highly customizable** (40+ layout parameters)
- 🎨 **3 rendering systems**:
  - Legacy (simple, hardcoded)
  - Markup Template (custom syntax)
  - **HTML Template** (maximum flexibility) ⭐
- 💾 **Smart caching** (instant regeneration)
- 🔄 **Batch processing** (multiple chats at once)
- 🔒 **Privacy options** (exclude images)

## 🚀 Quick Start

```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Single chat
python3 main.py "chat.zip"

# With language specification
python3 main.py "chat.zip" -l en

# All chats in folder (batch mode)
python3 main.py --batch
```

## 📋 Requirements

- Python 3.7+
- ffmpeg (for audio conversion)
- ~500 MB disk space (for Whisper model)

### Installing ffmpeg

```bash
# Linux (Ubuntu/Debian)
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from: https://ffmpeg.org/download.html
# Or use: choco install ffmpeg
```

## 📖 Usage

### Single File

```bash
# Basic usage
python3 main.py chat.zip

# Specify output filename
python3 main.py chat.zip -o output.pdf

# Specify language for transcription
python3 main.py chat.zip -l en

# Using the wrapper script
./convert.sh chat.zip -l en
```

### Batch Mode

Process multiple chat files at once:

```bash
# Process all .zip files in current directory
python3 main.py --batch

# With language specification
python3 main.py --batch -l en

# Skip files that already have PDF output
python3 main.py --batch --skip-existing

# Custom file pattern
python3 main.py --batch --pattern "WhatsApp*.zip"
```

### Command Line Options

```
Single file mode:
  python3 main.py <zip_file> [-o output.pdf] [-l language]

Batch mode:
  python3 main.py --batch [-l language] [--pattern "*.zip"] [--skip-existing]

Options:
  -o, --output      Output PDF filename
  -l, --language    Language for transcription (e.g., en, es, it, fr)
  --batch           Process all .zip files in current directory
  --pattern         File pattern for batch mode (default: *.zip)
  --skip-existing   Skip files that already have PDF output
  --help            Show help message
```

## ⚙️ Configuration

Customize everything via `config.ini`:

```bash
# Copy example configuration
cp config.example.ini config.ini

# Edit as needed
nano config.ini
```

### Key Configuration Sections

**PDF Settings**
```ini
[PDF]
page_size = A4              # or letter
left_margin = 0.5           # inches
right_margin = 0.5
max_image_width = 3.0       # inches
max_image_height = 2.5
```

**Whisper AI Settings**
```ini
[WHISPER]
model = small               # tiny, base, small, medium, large
language = en               # Leave empty for auto-detect
```

**Layout Customization**
```ini
[LAYOUT]
title_font_size = 20
sender_font_size = 10
message_font_size = 9
message_alignment = JUSTIFY  # LEFT, CENTER, RIGHT, JUSTIFY
```

**Colors**
```ini
[COLORS]
title_color = 075E54        # Hex color without #
sender_color = 25D366
media_color = 0084FF
system_color = 808080
```

**Privacy**
```ini
[PRIVACY]
exclude_images = false      # Set to true to exclude images from PDF
```

### Template Systems

**1. Legacy (Default)** - Simple, hardcoded layout
```ini
[TEMPLATE]
enabled = false
html_enabled = false
```

**2. Markup Template** - Custom syntax for flexibility
```ini
[TEMPLATE]
enabled = true
message_format = [style:sender]{sender}[/style]: {text}
```

**3. HTML Template** ⭐ **Recommended** - Maximum flexibility
```ini
[HTML_TEMPLATE]
enabled = true
template_file = template.html
```

## 💾 Transcription Cache

Audio transcriptions are automatically cached to save time:

```bash
# First time: ~10 minutes
python3 main.py chat.zip

# Regeneration: ~3 seconds ⚡
python3 main.py chat.zip -o chat_v2.pdf
```

**Time savings: up to 98%!**

The cache is stored in `.transcription_cache/` directory and is automatically created when needed.

## 🌍 Supported Languages

100+ languages supported by Whisper AI:

- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `it` - Italian
- `pt` - Portuguese
- `ru` - Russian
- `ja` - Japanese
- `zh` - Chinese
- `ar` - Arabic
- `hi` - Hindi
- `ko` - Korean
- And many more...

**Tip**: Specifying the language is faster than auto-detect (up to 50% faster).

## 📂 Project Structure

```
WhatsappTranscriber/
├── main.py                 # Main script
├── convert.sh              # Wrapper script
├── config.example.ini      # Example configuration
├── requirements.txt        # Python dependencies
├── template.html           # Default HTML template
├── template_minimal.html   # Minimal HTML template
├── template_simple.html    # Simple HTML template
├── languages/              # Language files
│   ├── en.ini
│   ├── es.ini
│   ├── fr.ini
│   ├── de.ini
│   ├── it.ini
│   └── pt.ini
├── LICENSE                 # MIT License
└── README.md              # This file
```

## 📥 Exporting Chats from WhatsApp

### Android

1. Open WhatsApp
2. Open the chat you want to export
3. Tap **⋮** (menu) → **More** → **Export chat**
4. Choose **"Include Media"**
5. Save the .zip file

### iPhone

1. Open WhatsApp
2. Open the chat you want to export
3. Tap the contact/group name at the top
4. Scroll down and tap **Export Chat**
5. Choose **"Attach Media"**
6. Save the .zip file

The exported .zip file contains:
```
chat.zip
├── _chat.txt              # Message history
├── IMG-*.jpg              # Images
├── PTT-*.opus             # Audio messages
├── VID-*.mp4              # Videos
└── *.pdf                  # Documents
```

## 📄 Output

Generated PDF includes:

- ✅ Title and metadata
- ✅ Formatted messages (sender, date, time)
- ✅ **Audio transcriptions** embedded inline
- ✅ **Images** embedded (optional)
- ✅ Links to documents/videos
- ✅ System messages (group changes, etc.)

Example output: `chat_transcript.pdf`

## 💡 Examples

### Example 1: Single Chat

```bash
python3 main.py "WhatsApp Chat with John.zip" -l en
```

Output: `WhatsApp_Chat_with_John_transcript.pdf`

### Example 2: Multiple Chats

```bash
# Process all WhatsApp exports in folder
python3 main.py --batch -l en
```

### Example 3: Regenerate After Layout Changes

```bash
# Modify config.ini (colors, margins, etc.)

# Regenerate all PDFs (uses cached audio transcriptions)
python3 main.py --batch

# Fast! ⚡ (seconds instead of minutes)
```

### Example 4: Only New Chats

```bash
# Process only files without existing PDF output
python3 main.py --batch --skip-existing
```

## 🔧 Advanced Features

### HTML Templates

Create custom PDF layouts using HTML:

```html
<!-- template.html -->
<!DOCTYPE html>
<html>
<head>
    <style>
        .message.user { background: #DCF8C6; }
        .message.other { background: #FFFFFF; }
    </style>
</head>
<body>
    <h1>{{chat_title}}</h1>
    {{#each messages}}
        <div class="message {{this.message_class}}">
            <strong>{{this.sender}}</strong>
            <span>{{this.time}}</span>
            <p>{{this.text}}</p>
            {{#if this.transcription}}
                <em>🎙️ {{this.transcription}}</em>
            {{/if}}
        </div>
    {{/each}}
</body>
</html>
```

### Language Files

Customize language-specific patterns:

```ini
# languages/en.ini
[PATTERNS]
attached_file = file attached
zip_pattern = WhatsApp Chat with 

[LABELS]
audio = Audio:
image = IMAGE
video = VIDEO
document = DOCUMENT

[MESSAGES]
image_excluded = excluded for privacy
transcription_failed = Transcription failed
```

## 🆘 Troubleshooting

### Error: "No module named reportlab"

```bash
# Make sure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "ffmpeg not found"

Install ffmpeg (see Requirements section above).

### Cache Not Working

Cache is stored in `.transcription_cache/`:

```bash
# Verify cache directory exists
ls -la .transcription_cache/

# Clear cache to force re-transcription
rm -rf .transcription_cache/
```

### Batch Mode: "No files found"

```bash
# Check for .zip files
ls *.zip

# Use specific pattern
python3 main.py --batch --pattern "WhatsApp*.zip"
```

### Poor Transcription Quality

- Specify the language explicitly: `-l en`
- Use a better model in config.ini: `model = medium` or `model = large`
- Check audio quality in original files

## ⚡ Performance

| Operation | First Time | With Cache |
|-----------|-----------|------------|
| 1 chat (10 audio) | ~10 min | ~3 sec ⚡ |
| 10 chats (100 audio) | ~100 min | ~30 sec ⚡ |
| PDF regeneration | ~10 min | ~3 sec ⚡ |

**Cache provides up to 98% time savings!**

## 📝 Technical Details

- **AI Model**: Whisper by OpenAI
- **Default Model**: small (466 MB)
- **First Run**: Model download (~2-3 min)
- **Accuracy**: 85-95% (depends on audio quality)
- **Supported Audio**: opus, m4a, mp3, wav, aac
- **Supported Images**: jpg, jpeg, png, gif, webp
- **Cache**: Automatic, file-based

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is released under the MIT License. See LICENSE file for details.

It uses the following open-source libraries:
- **Whisper** by OpenAI (MIT License)
- **ReportLab** (BSD License)
- **WeasyPrint** (BSD License)

## 🙏 Acknowledgments

- OpenAI for the amazing Whisper model
- The ReportLab team for PDF generation
- The WeasyPrint team for HTML to PDF conversion

---

**Made with ❤️ for preserving your conversations**
