# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- GitHub Actions for automated testing
- Docker container support
- Web interface for drag-and-drop conversion
- Additional template styles
- More language translations

## [1.0.0] - 2024-10-31

### Added
- Initial public release
- AI-powered audio transcription using OpenAI Whisper
- HTML template system with 3 built-in templates
- Multi-language support (6 languages: en, es, fr, de, it, pt)
- Smart transcription caching system
- Batch processing mode
- Privacy mode (exclude images)
- Customizable PDF layouts
- Command-line interface
- Comprehensive documentation in English

### Features
- **Core Functionality**
  - Parse WhatsApp chat exports (.zip files)
  - Transcribe audio messages (opus, m4a, mp3, wav, aac)
  - Embed images in PDF
  - Support for documents, videos, and other media
  - System message handling

- **Templates**
  - WhatsApp-style layout with bubbles
  - Minimal clean layout
  - Simple text-based layout
  - Full customization via HTML/CSS

- **Languages**
  - 100+ languages for Whisper transcription
  - 6 interface translations (en, es, fr, de, it, pt)
  - Easy to add new translations

- **Performance**
  - Smart caching reduces re-processing time by 98%
  - Batch mode for multiple chats
  - Skip existing files option

- **Configuration**
  - Extensive config.ini customization
  - PDF margins, colors, fonts
  - Template selection
  - Privacy settings

### Documentation
- Complete README.md with examples
- Template documentation (templates/README.md)
- Language files documentation (languages/README.md)
- Configuration guide (config.example.ini)
- Contributing guidelines (CONTRIBUTING.md)
- MIT License

### Technical
- Python 3.7+ compatibility
- Cross-platform (Linux, macOS, Windows)
- Dependencies: reportlab, pillow, pydub, openai-whisper, weasyprint
- Modular code structure
- Well-commented code

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute to this project.

## Links

- [GitHub Repository](https://github.com/wafy80/whatsapp-chat-transcriber)
- [Issue Tracker](https://github.com/wafy80/whatsapp-chat-transcriber/issues)
- [Latest Release](https://github.com/wafy80/whatsapp-chat-transcriber/releases)
