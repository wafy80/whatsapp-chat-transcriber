# WhatsApp Chat to PDF Transcriber

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey.svg)](https://github.com/wafy80/whatsapp-chat-transcriber)
[![CI](https://github.com/wafy80/whatsapp-chat-transcriber/workflows/CI/badge.svg)](https://github.com/wafy80/whatsapp-chat-transcriber/actions)
[![GitHub release](https://img.shields.io/github/v/release/wafy80/whatsapp-chat-transcriber.svg)](https://github.com/wafy80/whatsapp-chat-transcriber/releases)
[![GitHub stars](https://img.shields.io/github/stars/wafy80/whatsapp-chat-transcriber.svg)](https://github.com/wafy80/whatsapp-chat-transcriber/stargazers)

Convert WhatsApp chat exports to beautifully formatted PDFs with automatic audio transcription using AI.

> **⭐ Star this repo if you find it useful!**

## 📸 Screenshots

<details>
<summary>Click to see examples</summary>

### WhatsApp-Style Layout (Default)
Beautiful chat bubbles with green messages and audio transcriptions
<!-- ![WhatsApp Style](docs/screenshots/whatsapp-style.png) -->

### Minimal Layout
Clean, simple design perfect for archiving
<!-- ![Minimal Style](docs/screenshots/minimal-style.png) -->

### Sample Output
Generated PDF with embedded images and transcribed audio
<!-- ![Sample PDF](docs/screenshots/sample-output.png) -->

</details>

## ✨ Features

- 📝 **Automatic message parsing** from WhatsApp exports
- 🎙️ **AI-powered audio transcription** using OpenAI Whisper
- 🖼️ **Embedded images** directly in PDF
- 📎 **Media file references** (documents, videos)
- 🌍 **100+ languages supported** (6 built-in translations + auto-detect)
- 🎨 **Customizable HTML templates** (WhatsApp-style layouts)
- 🌐 **Multi-language interface** (language files in `languages/` folder)
- ⚙️ **Highly customizable** (colors, fonts, spacing)
- 💾 **Smart caching** (instant regeneration, up to 98% time savings)
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

**Or use the convenience wrapper:**
```bash
# Automatically sets up environment
./convert.sh "chat.zip"

# Verify setup
./check_setup.sh
```

## 📱 Getting the Chat ZIP from WhatsApp

WhatsApp exports are created on your phone. Here are the easiest ways to transfer them to your computer:

### Method 1: Direct Upload via Web Interface ⭐ EASIEST!

**No file transfer needed!** Upload directly from your phone:

#### Option A: Same WiFi (Local Network)

```bash
# Start the web server on your computer
python3 web_upload.py
```

Then on your phone:
1. Connect to the **same WiFi** as your computer
2. Open browser → go to URL shown (e.g., `http://192.168.1.100:8080`)
3. Upload WhatsApp ZIP file
4. Download generated PDF!

#### Option B: HTTPS Tunnel (PWA Share) 🚀 RECOMMENDED!

**Enable direct sharing from WhatsApp!**

```bash
# Option 1: Cloudflared (Recommended - No warning page)
# Install cloudflared first:
# Linux:
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
sudo chmod +x /usr/local/bin/cloudflared
# macOS:
brew install cloudflared

# Start with HTTPS tunnel
python3 web_upload.py --https

# Option 2: ngrok (Alternative - Shows warning page on first visit)
pip install pyngrok
python3 web_upload.py --ngrok
```

**Setup (one time only):**
1. Open the **HTTPS URL** shown on your phone (e.g., `https://xxxx.trycloudflare.com` or `https://xxxx.ngrok-free.app`)
2. Tap **"Install app"** or **"Add to Home Screen"**
3. The "Chat2PDF" app will be installed on your phone

**Every time you export a chat:**
1. WhatsApp → Open chat → ⋮ → **More** → **Export chat**
2. Choose "**Include Media**"
3. Tap **"Share"** button
4. Select **"Chat2PDF"** from the share menu! 📱
5. File uploads automatically → Download PDF when ready!

**Requirements:**
- ✅ **Android + Chrome/Edge** (iOS Safari doesn't support Share Target API)
- ✅ **Cloudflared installed** (recommended) OR **Free ngrok account**: [Sign up here](https://ngrok.com) → Get auth token → Run `ngrok config add-authtoken YOUR_TOKEN`

**Features:**
- 📱 Mobile-friendly interface
- 🎨 Drag & drop upload
- 🌍 Language selection
- ⚡ Auto processing
- 📥 Direct PDF download
- 🔗 **PWA Share Target** (share directly from WhatsApp!)
- 🚀 **Cloudflared**: No warning pages, instant access

---

### Method 2: Cloud Storage
1. Export chat on WhatsApp → Choose "**Include Media**"
2. Save to **Google Drive**, **iCloud**, **Dropbox**, etc.
3. Download on your computer from the cloud service

### Method 3: Email
1. Export chat on WhatsApp
2. Choose "**Email**" as share method
3. Open email on computer and download attachment
4. ⚠️ **Limit**: Email attachments usually max at 25 MB

### Method 4: USB Cable
1. Export chat on WhatsApp → Save to phone storage
2. Connect phone to computer via USB cable
3. Copy ZIP file from phone's WhatsApp folder:
   - **Android**: `/Internal Storage/WhatsApp/`
   - **iOS**: Use iTunes File Sharing or Finder

### Method 5: Messaging Apps
1. Export chat on WhatsApp
2. Share via **Telegram** (send to "Saved Messages"), **Signal**, etc.
3. Download from desktop app

### Method 6: Local Network Transfer
Use apps like:
- **SendAnywhere** (no account needed)
- **LocalSend** (open source, no internet needed)
- **Snapdrop** (web-based, same network)

**💡 Tip**: For large chats with media, cloud storage or local network transfer are fastest!

## 📋 Requirements

- Python 3.8+
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

# Using the wrapper script (easier)
./convert.sh chat.zip
./convert.sh chat.zip -o output.pdf -l en
```

**Tip**: The `convert.sh` wrapper script automatically:
- Creates virtual environment if needed
- Installs dependencies
- Activates the environment
- Runs the transcriber

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
sender_color = 25D366       # WhatsApp green
media_color = 0084FF
system_color = 808080
```

**Privacy**
```ini
[PRIVACY]
exclude_images = false      # Set to true to exclude images from PDF
```

**HTML Templates**
```ini
[HTML_TEMPLATE]
enabled = true                    # HTML templates enabled by default
template_file = templates/template.html     # WhatsApp-style layout
show_stats = true                 # Show message/media statistics
```

Available templates:
- `templates/template.html` - Full WhatsApp-style layout (default)
- `templates/template_minimal.html` - Minimal clean layout
- `templates/template_simple.html` - Simple text-based layout

**Language Translation**
```ini
[LANGUAGE]
code = en                         # en, es, fr, de, it, pt
```

The program loads language-specific strings from `languages/XX.ini` files. These control:
- **Pattern matching** in exported WhatsApp files
  - "file attached" (English)
  - "archivo adjunto" (Spanish)
  - "fichier joint" (French)
- **PDF labels**: "Audio:", "IMAGE", "VIDEO", "DOCUMENT"
- **System messages**: "excluded for privacy", "Transcription failed"

**Note**: All language-dependent strings are now in `languages/` folder.
The config file no longer contains language strings.

See `languages/README.md` for how to add new languages.

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

## 🌍 Language Support

### Whisper Transcription Languages

Whisper AI supports 100+ languages for audio transcription:

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

**Tip**: Specifying the language with `-l` is faster than auto-detect (up to 50% faster).

### Interface Translations

Built-in translations for the PDF interface (labels, patterns, messages):

| Language | Code | File | Status |
|----------|------|------|--------|
| 🇬🇧 English | `en` | `languages/en.ini` | ✅ Default |
| 🇪🇸 Spanish | `es` | `languages/es.ini` | ✅ Complete |
| 🇫🇷 French | `fr` | `languages/fr.ini` | ✅ Complete |
| 🇩🇪 German | `de` | `languages/de.ini` | ✅ Complete |
| 🇮🇹 Italian | `it` | `languages/it.ini` | ✅ Complete |
| 🇵🇹 Portuguese | `pt` | `languages/pt.ini` | ✅ Complete |

These files control:
- WhatsApp export patterns ("file attached" vs "archivo adjunto")
- PDF labels ("Audio:", "IMAGE", "VIDEO", etc.)
- System messages

To use a different language:
```bash
# Set in config.ini
[LANGUAGE]
code = es

# Or use command line
python3 main.py chat.zip -l es
```

See `languages/README.md` to add new translations.

## 📂 Project Structure

```
WhatsappTranscriber/
├── main.py                 # Main script
├── convert.sh              # Wrapper script
├── check_setup.sh          # Environment verification script
├── config.example.ini      # Example configuration
├── requirements.txt        # Python dependencies
├── templates/              # HTML templates
│   ├── template.html           # Full WhatsApp-style layout (default)
│   ├── template_minimal.html   # Minimal clean layout
│   └── template_simple.html    # Simple text-based layout
├── languages/              # Language files
│   ├── README.md
│   ├── en.ini              # English (default)
│   ├── es.ini              # Spanish
│   ├── fr.ini              # French
│   ├── de.ini              # German
│   ├── it.ini              # Italian
│   └── pt.ini              # Portuguese
├── LICENSE                 # MIT License
└── README.md              # This file
```

## 🛠️ Helper Scripts

### convert.sh
Convenience wrapper that handles environment setup automatically:
```bash
./convert.sh chat.zip              # Single file
./convert.sh --batch               # All .zip files  
./convert.sh chat.zip -l en        # With language
./convert.sh --help                # Show help
```

### check_setup.sh
Verifies your environment is correctly configured:
```bash
./check_setup.sh
```

This checks:
- ✅ Python 3 installation
- ✅ Virtual environment
- ✅ Required dependencies (ReportLab, Pillow, PyDub, Whisper)
- ✅ FFmpeg availability
- ✅ Project files integrity


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

## 🔧 Advanced Customization

### HTML Templates

The project uses HTML templates for PDF generation. You can customize the layout by editing or creating your own template:

**Template Variables:**
- `{{chat_title}}` - Chat name
- `{{generation_date}}` - PDF generation date
- `{{total_messages}}` - Message count
- `{{total_media}}` - Media files count
- `{{total_transcriptions}}` - Transcribed audio count

**Message Loop:**
```html
{{#each messages}}
  <div class="message {{this.message_class}}">
    <strong>{{this.sender}}</strong>
    <span>{{this.time}}</span>
    <p>{{this.text}}</p>
    {{#if this.transcription}}
      <em>🎙️ {{this.transcription}}</em>
    {{/if}}
    {{#if this.media}}
      <!-- Media handling -->
    {{/if}}
  </div>
{{/each}}
```

**Conditionals:**
- `{{#if condition}}...{{/if}}` - Show if true
- `{{#if condition}}...{{else}}...{{/if}}` - If-else
- `{{#each array}}...{{/each}}` - Loop through array

**Available templates:**
1. `templates/template.html` - WhatsApp-style with green bubbles and statistics
2. `templates/template_minimal.html` - Clean minimal design
3. `templates/template_simple.html` - Simple text-based layout

To use a different template, edit `config.ini`:
```ini
[HTML_TEMPLATE]
enabled = true
template_file = templates/template_minimal.html
```

### Language Translation Files

Interface strings are stored in `languages/XX.ini` files. Create new translations by copying an existing file:

```bash
cp languages/en.ini languages/ja.ini
```

Then edit the strings:
```ini
[PATTERNS]
# Must match WhatsApp export format in your language
attached_file = 添付ファイル

[LABELS]
# Labels shown in PDF
audio = オーディオ:
image = 画像
video = ビデオ

[MESSAGES]
# System messages
image_excluded = プライバシーのため除外
transcription_failed = 転写に失敗しました
```

See `languages/README.md` for detailed instructions.

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

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on:
- Reporting bugs
- Suggesting enhancements
- Adding language translations
- Creating templates
- Code contributions

**Ways to contribute:**
- 🐛 Report bugs
- 💡 Suggest features
- 🌍 Add language translations
- 🎨 Create new templates
- 📝 Improve documentation
- ⭐ Star this repository

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
