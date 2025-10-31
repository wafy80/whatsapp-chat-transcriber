# Language Files

This folder contains translation files for WhatsApp Chat to PDF Transcriber.

## 📋 Available Languages

| Language | File | Code | Status |
|----------|------|------|--------|
| 🇬🇧 English | `en.ini` | `en` | ✅ Complete |
| 🇪🇸 Spanish | `es.ini` | `es` | ✅ Complete |
| 🇫🇷 French | `fr.ini` | `fr` | ✅ Complete |
| 🇩🇪 German | `de.ini` | `de` | ✅ Complete |
| 🇮🇹 Italian | `it.ini` | `it` | ✅ Complete |
| 🇵🇹 Portuguese | `pt.ini` | `pt` | ✅ Complete |

## 🔧 File Structure

Each translation file contains 4 sections:

```ini
[METADATA]
language_name = Language Name
language_code = en
version = 1.0
translator = Translator Name

[PATTERNS]
# Patterns used by WhatsApp in exported .txt file
attached_file = file attached

[LABELS]
# Labels displayed in PDF
audio = Audio:
image = IMAGE
video = VIDEO
document = DOCUMENT

[MESSAGES]
# System messages
image_excluded = excluded for privacy
transcription_failed = Transcription failed

[UI]
# Interface messages (optional)
processing = Processing
extracting = Extracting
transcribing = Transcribing
```

## 🌍 How to Use

### Method 1: Configure in config.ini

Specify language code in `config.ini`:

```ini
[LANGUAGE]
code = en  # en, es, fr, de, it, pt, etc.
```

The program will automatically load `languages/en.ini`

### Method 2: Command line parameter

```bash
python main.py chat.zip -l en
```

### Method 3: Auto-detect from Whisper

If you don't specify anything, the program uses the language detected by Whisper.

## ➕ Add a New Language

### Step 1: Create the file

Copy an existing file and rename it with the ISO 639-1 language code:

```bash
cp en.ini xx.ini  # xx = your language code
```

### Step 2: Translate strings

Open the file and translate all strings:

```ini
[METADATA]
language_name = Your Language Name
language_code = xx
translator = Your Name

[PATTERNS]
attached_file = (text WhatsApp uses in your language)

[LABELS]
audio = Audio: (or equivalent)
image = IMAGE (or equivalent)
# ... translate everything
```

### Step 3: Find the correct pattern

To find `attached_file` in your language:

1. Export a WhatsApp chat in your language
2. Open the `.txt` file in the ZIP archive
3. Look for a message with attached file, like:
   - `IMG-001.jpg (file attached)`
   - `IMG-001.jpg (archivo adjunto)`
   - `IMG-001.jpg (fichier joint)`
4. Copy the text in parentheses

## 🧪 Test a Translation

```bash
# Verify the file is valid
python -c "import configparser; c = configparser.ConfigParser(); c.read('languages/xx.ini'); print('✅ OK')"

# Test with a chat file
python main.py chat.zip -l xx
```

## 📝 Translation Guidelines

### WhatsApp Patterns
- **Must match EXACTLY** the text in exported .txt file
- Include spaces if present

### Labels
- Keep punctuation consistent (e.g., "Audio:" with colon)
- Use UPPERCASE for IMAGE, VIDEO, DOCUMENT

### Messages
- Be concise and clear
- Use appropriate technical terminology

### Metadata
- `language_name`: Native name of language (e.g., "Español", not "Spanish")
- `language_code`: 2-letter ISO 639-1 code
- `version`: Keep 1.0 for new translations
- `translator`: Your name or "Community"

## 🤝 Contributing

Have you translated WhatsApp Transcriber to a new language?

1. Create the file `languages/xx.ini`
2. Test it thoroughly
3. Open a Pull Request
4. Add your name as translator!

---

**Version**: 1.0  
**Last update**: November 2024

