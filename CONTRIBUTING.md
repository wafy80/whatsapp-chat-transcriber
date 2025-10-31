# Contributing to WhatsApp Chat to PDF Transcriber

First off, thank you for considering contributing to WhatsApp Chat to PDF Transcriber! 🎉

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Adding Language Translations](#adding-language-translations)
  - [Creating Templates](#creating-templates)
  - [Code Contributions](#code-contributions)
- [Development Setup](#development-setup)
- [Style Guidelines](#style-guidelines)
- [Commit Messages](#commit-messages)

## Code of Conduct

This project and everyone participating in it is governed by common sense and respect. Be kind, be professional, and help create a welcoming environment for everyone.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the problem
- **Expected behavior** vs actual behavior
- **Screenshots** if applicable
- **Environment details**:
  - OS (Linux/macOS/Windows)
  - Python version
  - WhatsApp export language

**Example bug report:**
```
Title: Audio transcription fails for .m4a files on Windows

Description:
When processing WhatsApp chats with .m4a audio files on Windows 11, 
the transcription fails with "file not found" error.

Steps to reproduce:
1. Export WhatsApp chat with audio messages (Windows phone)
2. Run: python main.py chat.zip
3. Error occurs during audio transcription

Expected: Audio should be transcribed
Actual: Error message "file not found"

Environment:
- Windows 11
- Python 3.10.5
- WhatsApp export: English
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description**
- **Why this enhancement would be useful**
- **Possible implementation** (if you have ideas)
- **Examples from other projects** (if applicable)

### Adding Language Translations

We welcome translations for new languages! See `languages/README.md` for detailed instructions.

**Quick guide:**
1. Copy `languages/en.ini` to `languages/XX.ini` (where XX is your language code)
2. Translate all strings to your language
3. Test with a WhatsApp export in that language
4. Submit a pull request

**Important:** The `attached_file` pattern must match EXACTLY what WhatsApp uses in your language's export file.

### Creating Templates

Create new HTML templates for different PDF styles:

1. Copy an existing template from `templates/`
2. Modify the HTML/CSS to your liking
3. Test with various chat exports
4. Add documentation in `templates/README.md`
5. Submit a pull request

### Code Contributions

1. **Fork** the repository
2. **Create a branch** for your feature: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Test thoroughly** with different chat exports
5. **Commit** with clear messages: `git commit -m "Add amazing feature"`
6. **Push** to your fork: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/whatsapp-chat-transcriber.git
cd whatsapp-chat-transcriber

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (if any)
pip install pytest black flake8

# Run tests (if you add them)
pytest

# Format code
black main.py

# Lint code
flake8 main.py
```

## Style Guidelines

### Python Code

- **Follow PEP 8** style guide
- **Use meaningful variable names**
- **Add docstrings** to functions
- **Keep functions focused** (single responsibility)
- **Comment complex logic**

**Example:**
```python
def transcribe_audio(self, audio_file: str) -> str:
    """Transcribe audio file using Whisper with caching.
    
    Args:
        audio_file: Path to audio file
        
    Returns:
        Transcribed text
    """
    # Check cache first
    cached_text = self._get_cached_transcription(audio_file)
    if cached_text:
        return cached_text
    
    # Transcribe with Whisper
    # ... implementation
```

### Configuration Files

- **Add comments** explaining each option
- **Provide examples** for different use cases
- **Keep it organized** by section

### Documentation

- **Use clear English**
- **Provide examples** for commands
- **Keep it concise** but complete
- **Use code blocks** for terminal commands
- **Add screenshots** when helpful

## Commit Messages

Write clear, descriptive commit messages:

**Good:**
```
Add Spanish language translation

- Created languages/es.ini with all translations
- Tested with Spanish WhatsApp export
- Updated languages/README.md
```

**Bad:**
```
fixed stuff
```

**Format:**
```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

## Pull Request Process

1. **Update documentation** if needed
2. **Add tests** if applicable
3. **Ensure all tests pass**
4. **Update CHANGELOG** if exists
5. **Describe your changes** clearly in PR description

**PR Template:**
```markdown
## Description
Brief description of changes

## Type of change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Translation
- [ ] Template

## Testing
How did you test this?

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
```

## Questions?

Feel free to:
- Open an issue with your question
- Ask in discussions (if enabled)
- Contact the maintainer

## Recognition

Contributors will be recognized in:
- README.md contributors section (if we add one)
- Release notes
- Language file credits (for translators)

Thank you for contributing! 🙌

---

**Happy coding!** 🚀
