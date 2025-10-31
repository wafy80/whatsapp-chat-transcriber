# WhatsApp Chat to PDF Transcriber v1.0.0

**First public release! 🎉**

Transform your WhatsApp conversations into beautifully formatted PDFs with AI-powered audio transcription.

## ✨ Highlights

- 🎙️ **Automatic audio transcription** using OpenAI Whisper AI
- 🎨 **3 professional HTML templates** (WhatsApp-style, Minimal, Simple)
- 🌍 **6 built-in languages** (English, Spanish, French, German, Italian, Portuguese)
- 💾 **Smart caching system** - 98% faster re-processing
- 🔄 **Batch processing** for multiple chats
- 🔒 **Privacy mode** to exclude images

## 🚀 Quick Start

```bash
# Install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Convert a chat
python3 main.py "chat.zip"

# Batch convert all chats
python3 main.py --batch -l en
```

## 📦 What's Included

### Core Features
- Parse WhatsApp chat exports (.zip files)
- Transcribe audio messages (opus, m4a, mp3, wav, aac)
- Embed images in PDF
- Support for documents, videos, and other media
- System message handling
- 100+ languages supported for transcription

### Templates
- **template.html** - Full WhatsApp-style layout with bubbles
- **template_minimal.html** - Clean minimal design
- **template_simple.html** - Simple text-based layout
- Full customization via HTML/CSS

### Languages
All interface strings localized in:
- 🇬🇧 English
- 🇪🇸 Spanish  
- 🇫🇷 French
- 🇩🇪 German
- 🇮🇹 Italian
- 🇵🇹 Portuguese

### Performance
- Smart caching reduces re-processing time by **up to 98%**
- Batch mode for multiple chats
- Skip existing files option
- Efficient memory usage

## 🔧 Requirements

- Python 3.7+
- ffmpeg (for audio conversion)
- ~500 MB disk space (for Whisper model)

## 📝 Documentation

- [README.md](README.md) - Complete usage guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [templates/README.md](templates/README.md) - Template documentation
- [languages/README.md](languages/README.md) - Translation guide

## 🐛 Known Issues

None at this time. Please report any issues you find!

## 🙏 Acknowledgments

- OpenAI for the amazing Whisper model
- The ReportLab team for PDF generation
- The WeasyPrint team for HTML to PDF conversion

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

---

**⭐ If you find this useful, please star the repository!**

**🐛 Found a bug?** [Report it here](https://github.com/wafy80/whatsapp-chat-transcriber/issues/new?template=bug_report.md)

**💡 Have an idea?** [Suggest a feature](https://github.com/wafy80/whatsapp-chat-transcriber/issues/new?template=feature_request.md)

**🤝 Want to contribute?** See [CONTRIBUTING.md](CONTRIBUTING.md)
