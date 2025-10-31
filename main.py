#!/usr/bin/env python3
"""
WhatsApp Chat to PDF Transcriber
Converts WhatsApp chat exports to PDF with audio transcription and media embedding.
"""

import os
import sys
import zipfile
import tempfile
import shutil
import re
import io
import configparser
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Optional

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
    from reportlab.lib.colors import HexColor, grey
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
except ImportError:
    print("Installing required packages...")
    os.system("pip install reportlab pillow pydub openai-whisper")
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
    from reportlab.lib.colors import HexColor, grey
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

try:
    from PIL import Image as PILImage
except ImportError:
    pass

try:
    import whisper
except ImportError:
    print("Installing whisper...")
    os.system("pip install openai-whisper")
    import whisper

try:
    from pydub import AudioSegment
except ImportError:
    pass

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


class WhatsAppChatToPDF:
    def __init__(self, zip_path: str, output_pdf: Optional[str] = None, language: Optional[str] = None):
        """Initialize the converter.
        
        Args:
            zip_path: Path to WhatsApp chat ZIP file
            output_pdf: Output PDF filename (optional)
            language: Language code for Whisper transcription (e.g., 'it', 'en', 'es')
                     If None, Whisper auto-detects the language
        """
        self.zip_path = zip_path
        self.temp_dir = tempfile.mkdtemp()
        self.output_pdf = output_pdf or self._generate_output_name()
        self.messages = []
        self.media_files = {}
        
        # Load configuration
        self.config = self._load_config()
        
        # Language preference (CLI argument overrides config)
        self.language = language or self.config.get('WHISPER', 'language', fallback=None)
        
        # Load language-dependent strings from separate language file
        self._load_language_file()
        
        # Cache directory for transcriptions
        self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(zip_path)), '.transcription_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _generate_output_name(self) -> str:
        """Generate output PDF name based on input zip."""
        base_name = Path(self.zip_path).stem
        return f"{base_name}_transcript.pdf"
    
    def _load_config(self) -> configparser.ConfigParser:
        """Load configuration from config.ini file."""
        config = configparser.ConfigParser()
        
        # Look for config.ini in the same directory as the script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'config.ini')
        
        # Fall back to config.example.ini if config.ini doesn't exist
        if not os.path.exists(config_path):
            config_path = os.path.join(script_dir, 'config.example.ini')
        
        if os.path.exists(config_path):
            try:
                config.read(config_path)
                print(f"📋 Configuration loaded from {os.path.basename(config_path)}")
            except Exception as e:
                print(f"⚠️  Failed to load configuration: {e}")
        
        return config
    
    def _load_language_file(self) -> None:
        """Load language-dependent strings from separate language file.
        
        Language files are loaded from languages/ directory.
        Falls back to config.ini [LANGUAGE_STRINGS] section if language file not found.
        """
        # Determine which language to use
        # Priority: 1) WHISPER language setting, 2) LANGUAGE code setting, 3) default 'en'
        lang_code = self.config.get('LANGUAGE', 'code', fallback=None)
        if not lang_code:
            lang_code = self.config.get('WHISPER', 'language', fallback='en')
        
        # Look for language file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        lang_file = os.path.join(script_dir, 'languages', f'{lang_code}.ini')
        
        # Try to load language file
        lang_config = configparser.ConfigParser()
        loaded_from_file = False
        
        if os.path.exists(lang_file):
            try:
                lang_config.read(lang_file, encoding='utf-8')
                loaded_from_file = True
                print(f"🌍 Loaded language file: languages/{lang_code}.ini")
            except Exception as e:
                print(f"⚠️  Failed to load language file {lang_file}: {e}")
        
        # Load strings from language file or fallback to config.ini
        if loaded_from_file and 'PATTERNS' in lang_config:
            self.str_attached_file = lang_config.get('PATTERNS', 'attached_file', fallback='file attached')
            self.str_zip_pattern = lang_config.get('PATTERNS', 'zip_pattern', fallback='WhatsApp Chat with ')
        else:
            # Fallback to config.ini [LANGUAGE_STRINGS]
            self.str_attached_file = self.config.get('LANGUAGE_STRINGS', 'attached_file_pattern', fallback='file attached')
            self.str_zip_pattern = self.config.get('HTML_TEMPLATE', 'zip_pattern', fallback='WhatsApp Chat with ')
        
        if loaded_from_file and 'LABELS' in lang_config:
            self.str_audio_label = lang_config.get('LABELS', 'audio', fallback='Audio:')
            self.str_image_label = lang_config.get('LABELS', 'image', fallback='IMAGE')
            self.str_video_label = lang_config.get('LABELS', 'video', fallback='VIDEO')
            self.str_document_label = lang_config.get('LABELS', 'document', fallback='DOCUMENT')
            self.str_media_prefix = lang_config.get('LABELS', 'media', fallback='')
        else:
            # Fallback to config.ini [LANGUAGE_STRINGS]
            self.str_audio_label = self.config.get('LANGUAGE_STRINGS', 'audio_label', fallback='Audio:')
            self.str_image_label = self.config.get('LANGUAGE_STRINGS', 'image_label', fallback='IMAGE')
            self.str_video_label = 'VIDEO'
            self.str_document_label = 'DOCUMENT'
            self.str_media_prefix = self.config.get('LANGUAGE_STRINGS', 'media_prefix', fallback='')
        
        if loaded_from_file and 'MESSAGES' in lang_config:
            self.str_image_excluded = lang_config.get('MESSAGES', 'image_excluded', fallback='excluded for privacy')
            self.str_transcription_failed = lang_config.get('MESSAGES', 'transcription_failed', fallback='Transcription failed')
        else:
            # Fallback to config.ini [LANGUAGE_STRINGS]
            self.str_image_excluded = self.config.get('LANGUAGE_STRINGS', 'image_excluded_text', fallback='excluded for privacy')
            self.str_transcription_failed = 'Transcription failed'
        
        # UI messages (optional, for future use)
        if loaded_from_file and 'UI' in lang_config:
            self.str_ui_processing = lang_config.get('UI', 'processing', fallback='Processing')
            self.str_ui_extracting = lang_config.get('UI', 'extracting', fallback='Extracting')
            self.str_ui_parsing = lang_config.get('UI', 'parsing', fallback='Parsing')
            self.str_ui_transcribing = lang_config.get('UI', 'transcribing', fallback='Transcribing')
        else:
            self.str_ui_processing = 'Processing'
            self.str_ui_extracting = 'Extracting'
            self.str_ui_parsing = 'Parsing'
            self.str_ui_transcribing = 'Transcribing'
    
    def _load_language_strings(self) -> None:
        """Load language-dependent strings from config (legacy method).
        
        DEPRECATED: Use _load_language_file() instead.
        Kept for backward compatibility.
        """
        self.str_attached_file = self.config.get('LANGUAGE_STRINGS', 'attached_file_pattern', fallback='file attached')
        self.str_audio_label = self.config.get('LANGUAGE_STRINGS', 'audio_label', fallback='Audio:')
        self.str_image_label = self.config.get('LANGUAGE_STRINGS', 'image_label', fallback='IMAGE')
        self.str_image_excluded = self.config.get('LANGUAGE_STRINGS', 'image_excluded_text', fallback='excluded for privacy')
        self.str_media_prefix = self.config.get('LANGUAGE_STRINGS', 'media_prefix', fallback='')
    
    def extract_zip(self) -> None:
        """Extract the WhatsApp zip file."""
        print(f"📦 Extracting {self.zip_path}...")
        with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)
        print(f"✅ Extracted to {self.temp_dir}")
    
    def find_chat_file(self) -> str:
        """Find the main chat text file."""
        for file in os.listdir(self.temp_dir):
            if file.endswith('.txt'):
                return os.path.join(self.temp_dir, file)
        raise FileNotFoundError("No .txt chat file found in the zip")
    
    def parse_chat(self) -> None:
        """Parse the chat text file."""
        chat_file = self.find_chat_file()
        print(f"📄 Parsing chat from {os.path.basename(chat_file)}...")
        
        with open(chat_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_message = None
        
        for line in lines:
            line = line.rstrip('\n')
            
            # Check if line starts with a date pattern
            if self._is_message_start(line):
                if current_message:
                    self.messages.append(current_message)
                current_message = self._parse_message_line(line)
            elif current_message:
                # Continuation of previous message
                current_message['text'] += '\n' + line
        
        if current_message:
            self.messages.append(current_message)
        
        print(f"✅ Parsed {len(self.messages)} messages")
    
    def _is_message_start(self, line: str) -> bool:
        """Check if line is the start of a new message."""
        pattern = r'^\d{1,2}/\d{1,2}/\d{2,4},\s+\d{1,2}:\d{2}'
        return bool(re.match(pattern, line))
    
    def _parse_message_line(self, line: str) -> Dict:
        """Parse a single message line."""
        # Format: DD/MM/YY, HH:MM - Name: Message
        pattern = r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2})\s*-\s*(.*?):\s*(.*?)$'
        match = re.match(pattern, line)
        
        if match:
            date, time, sender, text = match.groups()
            return {
                'date': date,
                'time': time,
                'sender': sender.strip(),
                'text': text.strip()
            }
        else:
            # System message or message without sender
            pattern = r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2})\s*-\s*(.*)$'
            match = re.match(pattern, line)
            if match:
                date, time, text = match.groups()
                return {
                    'date': date,
                    'time': time,
                    'sender': 'System',
                    'text': text.strip()
                }
        
        return {'date': '', 'time': '', 'sender': '', 'text': line}
    
    def transcribe_audio(self, audio_file: str) -> str:
        """Transcribe audio file using Whisper with caching.
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Transcribed text
        """
        # Check cache first
        cached_text = self._get_cached_transcription(audio_file)
        if cached_text is not None:
            print(f"💾 Using cached transcription for {os.path.basename(audio_file)}")
            return cached_text
        
        print(f"🎙️  Transcribing {os.path.basename(audio_file)}...", end=" ")
        try:
            # Get model from config, default to "small"
            model_name = self.config.get('WHISPER', 'model', fallback='small')
            model = whisper.load_model(model_name)
            
            # Prepare transcription kwargs
            transcribe_kwargs = {"audio": audio_file}
            
            # Add language parameter if specified
            if self.language:
                transcribe_kwargs["language"] = self.language
                print(f"[{self.language.upper()}]")
            else:
                print("[auto-detect]")
            
            result = model.transcribe(**transcribe_kwargs)
            text = result["text"].strip()
            
            # Show detected language if auto-detect was used
            if not self.language and "language" in result:
                detected_lang = result["language"]
                print(f"   Detected language: {detected_lang}")
            
            print(f"✅ Transcribed: {text[:50]}...")
            
            # Save to cache
            self._save_cached_transcription(audio_file, text)
            
            return text
        except Exception as e:
            print(f"⚠️  Failed to transcribe {audio_file}: {e}")
            return f"[{self.str_transcription_failed}]"
    
    def _get_cache_key(self, audio_file: str) -> str:
        """Generate a unique cache key for an audio file."""
        import hashlib
        filename = os.path.basename(audio_file)
        
        # Get file size as part of the key
        try:
            file_size = os.path.getsize(audio_file)
        except:
            file_size = 0
        
        # Create hash from filename and size
        key_string = f"{filename}_{file_size}"
        hash_key = hashlib.md5(key_string.encode()).hexdigest()[:16]
        
        return f"{filename}_{hash_key}"
    
    def _get_cached_transcription(self, audio_file: str) -> Optional[str]:
        """Get cached transcription if it exists."""
        cache_key = self._get_cache_key(audio_file)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.txt")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e:
                print(f"⚠️  Failed to read cache: {e}")
                return None
        
        return None
    
    def _save_cached_transcription(self, audio_file: str, text: str) -> None:
        """Save transcription to cache."""
        cache_key = self._get_cache_key(audio_file)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.txt")
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception as e:
            print(f"⚠️  Failed to save cache: {e}")
    
    def enhance_messages_with_media(self) -> None:
        """Enhance messages with media information."""
        print("🖼️  Processing media files...")
        
        media_types = {
            'audio': ['.opus', '.m4a', '.mp3', '.wav', '.aac'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
            'document': ['.pdf', '.doc', '.docx', '.xls', '.xlsx']
        }
        
        # Create media mappings
        media_index = {}
        for file in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, file)
            if os.path.isfile(file_path):
                for media_type, extensions in media_types.items():
                    if any(file.lower().endswith(ext) for ext in extensions):
                        media_index[file] = {
                            'path': file_path,
                            'type': media_type,
                            'filename': file
                        }
                        break
        
        # Match media files to messages
        for msg in self.messages:
            for media_file, media_info in media_index.items():
                if media_file in msg['text']:
                    msg['media'] = media_info.copy()
                    
                    # Transcribe audio
                    if media_info['type'] == 'audio':
                        msg['transcription'] = self.transcribe_audio(media_info['path'])
                    
                    break
    
    def get_image_for_pdf(self, image_path: str, max_width: Optional[float] = None, 
                         max_height: Optional[float] = None) -> Optional[Image]:
        """Load and resize an image for PDF."""
        # Get max dimensions from config if not provided
        if max_width is None:
            max_width = self.config.getfloat('PDF', 'max_image_width', fallback=4.0) * inch
        if max_height is None:
            max_height = self.config.getfloat('PDF', 'max_image_height', fallback=3.0) * inch
            
        try:
            img = PILImage.open(image_path)
            width, height = img.size
            
            # Calculate scaling
            ratio = min(max_width/width, max_height/height)
            new_width = width * ratio
            new_height = height * ratio
            
            # Create a temporary scaled image
            temp_img_path = os.path.join(self.temp_dir, f"_scaled_{os.path.basename(image_path)}")
            img.thumbnail((int(new_width), int(new_height)), PILImage.Resampling.LANCZOS)
            img.save(temp_img_path)
            
            return Image(temp_img_path, width=new_width, height=new_height)
        except Exception as e:
            print(f"⚠️  Failed to load image {image_path}: {e}")
            return None
    
    def _parse_template(self, template: str, msg: Dict, styles: Dict) -> List:
        """Parse a template string and return PDF elements.
        
        Template syntax:
        - {sender} - Sender name
        - {date} - Message date
        - {time} - Message time
        - {text} - Message text
        - {transcription} - Audio transcription
        - {media} - Media information
        - [style:name]...[/style] - Apply named style
        - [spacer:N] - Add vertical space (N pixels)
        - [image] - Insert image if available
        - [br] - Line break
        """
        elements = []
        parts = re.split(r'(\[.*?\]|\{.*?\})', template)
        
        current_style = None
        current_text = []
        
        def flush_text():
            nonlocal current_text
            if current_text:
                text = ''.join(current_text)
                if text.strip():
                    style = styles.get(current_style, styles['message'])
                    elements.append(Paragraph(text, style))
                current_text = []
        
        for part in parts:
            if not part:
                continue
                
            # Variable substitution
            if part.startswith('{') and part.endswith('}'):
                var = part[1:-1]
                if var == 'sender':
                    current_text.append(msg.get('sender', ''))
                elif var == 'date':
                    current_text.append(msg.get('date', ''))
                elif var == 'time':
                    current_text.append(msg.get('time', ''))
                elif var == 'text':
                    text = msg.get('text', '')
                    # Use configured pattern for attached files
                    pattern = re.escape(self.str_attached_file)
                    text = re.sub(rf'‎[A-Za-z0-9\-\.]+\.(opus|jpg|pdf|etc)\s*\({pattern}\)', '', text)
                    current_text.append(text)
                elif var == 'transcription' and msg.get('transcription'):
                    current_text.append(f"🎙️ {self.str_audio_label} {msg['transcription']}")
                    
            # Transcription tag (auto-insert if available)
            elif part == '[transcription]':
                flush_text()
                if msg.get('transcription'):
                    text = f"<i>🎙️ {self.str_audio_label} {msg['transcription']}</i>"
                    style = styles.get('message', styles['message'])
                    elements.append(Paragraph(text, style))
                    
            # Style tags
            elif part.startswith('[style:') and part.endswith(']'):
                flush_text()
                current_style = part[7:-1]
                
            elif part == '[/style]':
                flush_text()
                current_style = None
                
            # Spacer
            elif part.startswith('[spacer:') and part.endswith(']'):
                flush_text()
                try:
                    space = int(part[8:-1])
                    elements.append(Spacer(1, space))
                except:
                    pass
                    
            # Image
            elif part == '[image]':
                flush_text()
                exclude_images = self.config.getboolean('PRIVACY', 'exclude_images', fallback=False)
                if msg.get('media') and msg['media']['type'] == 'image':
                    if exclude_images:
                        media_info = msg['media']
                        text = f"🖼️ {self.str_image_label}: {media_info['filename']} ({self.str_image_excluded})"
                        elements.append(Paragraph(text, styles.get('media', styles['message'])))
                    else:
                        img = self.get_image_for_pdf(msg['media']['path'])
                        if img:
                            elements.append(img)
                            
            # Media link
            elif part == '[media]':
                flush_text()
                if msg.get('media') and msg['media']['type'] != 'image':
                    media_info = msg['media']
                    text = f"📎 {media_info['type'].upper()}: {media_info['filename']}"
                    elements.append(Paragraph(text, styles.get('media', styles['message'])))
                    
            # Line break
            elif part == '[br]':
                current_text.append('<br/>')
                
            # Regular text
            else:
                current_text.append(part)
        
        flush_text()
        return elements
    
    def _parse_html_template(self, html_template: str, msg: Dict, styles: Dict) -> List:
        """Parse an HTML template and return PDF elements.
        
        Supports standard HTML tags that ReportLab Paragraph can handle:
        - <b>, <i>, <u>, <strike>
        - <font color="#RRGGBB" size="N">
        - <br/>
        - <a href="...">
        
        Variables:
        - {{sender}} - Sender name
        - {{date}} - Message date
        - {{time}} - Message time
        - {{text}} - Message text
        - {{transcription}} - Audio transcription
        """
        elements = []
        
        # Replace variables
        html = html_template
        html = html.replace('{{sender}}', msg.get('sender', ''))
        html = html.replace('{{date}}', msg.get('date', ''))
        html = html.replace('{{time}}', msg.get('time', ''))
        
        # Clean text - use configured pattern
        text = msg.get('text', '')
        pattern = re.escape(self.str_attached_file)
        text = re.sub(rf'‎[A-Za-z0-9\-\.]+\.(opus|jpg|pdf|etc)\s*\({pattern}\)', '', text)
        html = html.replace('{{text}}', text)
        
        # Handle transcription
        if msg.get('transcription'):
            html = html.replace('{{transcription}}', msg['transcription'])
        else:
            html = html.replace('{{transcription}}', '')
        
        # Parse custom tags
        # Extract and process [image], [media], [spacer] tags
        parts = re.split(r'(\[image\]|\[media\]|\[spacer:\d+\])', html)
        
        for part in parts:
            if not part:
                continue
                
            if part == '[image]':
                exclude_images = self.config.getboolean('PRIVACY', 'exclude_images', fallback=False)
                if msg.get('media') and msg['media']['type'] == 'image':
                    if exclude_images:
                        media_info = msg['media']
                        text = f"🖼️ {self.str_image_label}: {media_info['filename']} ({self.str_image_excluded})"
                        elements.append(Paragraph(text, styles['media']))
                    else:
                        img = self.get_image_for_pdf(msg['media']['path'])
                        if img:
                            elements.append(img)
                            
            elif part == '[media]':
                if msg.get('media') and msg['media']['type'] != 'image':
                    media_info = msg['media']
                    text = f"📎 {media_info['type'].upper()}: {media_info['filename']}"
                    elements.append(Paragraph(text, styles['media']))
                    
            elif part.startswith('[spacer:'):
                try:
                    space = int(part[8:-1])
                    elements.append(Spacer(1, space))
                except:
                    pass
                    
            else:
                # Regular HTML content
                if part.strip():
                    # Determine which style to use based on content
                    style = styles['message']
                    elements.append(Paragraph(part, style))
        
        return elements
    
    def _render_html_template(self, template_path: str) -> str:
        """Render a complete HTML template with message data.
        
        Args:
            template_path: Path to HTML template file
            
        Returns:
            Rendered HTML string
        """
        # Load template
        with open(template_path, 'r', encoding='utf-8') as f:
            template_html = f.read()
        
        # Get chat info
        chat_title = Path(self.find_chat_file()).stem.replace('.txt', '')
        generation_date = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        # Calculate statistics
        total_messages = len(self.messages)
        total_media = sum(1 for msg in self.messages if msg.get('media'))
        total_transcriptions = sum(1 for msg in self.messages if msg.get('transcription'))
        
        # Replace global variables
        template_html = template_html.replace('{{chat_title}}', chat_title)
        template_html = template_html.replace('{{generation_date}}', generation_date)
        template_html = template_html.replace('{{total_messages}}', str(total_messages))
        template_html = template_html.replace('{{total_media}}', str(total_media))
        template_html = template_html.replace('{{total_transcriptions}}', str(total_transcriptions))
        
        # Replace UI labels from language file
        template_html = template_html.replace('{{label_messages}}', self.lang_config.get('UI', 'label_messages', fallback='Messages'))
        template_html = template_html.replace('{{label_media}}', self.lang_config.get('UI', 'label_media', fallback='Media'))
        template_html = template_html.replace('{{label_audio}}', self.lang_config.get('UI', 'label_audio', fallback='Audio'))
        template_html = template_html.replace('{{label_transcript}}', self.lang_config.get('UI', 'label_transcript', fallback='Chat Transcript'))
        template_html = template_html.replace('{{label_footer_generated}}', self.lang_config.get('UI', 'label_footer_generated', fallback='Chat transcript generated by WhatsApp Transcriber'))
        
        # Replace language code
        language_code = self.lang_config.get('METADATA', 'language_code', fallback='en')
        template_html = template_html.replace('{{language_code}}', language_code)
        
        # Get config values
        show_stats = self.config.getboolean('HTML_TEMPLATE', 'show_stats', fallback=True)
        footer_text = self.config.get('HTML_TEMPLATE', 'footer_text', fallback='')
        exclude_images = self.config.getboolean('PRIVACY', 'exclude_images', fallback=False)
        
        # Handle conditional blocks
        if show_stats:
            template_html = re.sub(r'\{\{#if show_stats\}\}(.*?)\{\{/if\}\}', r'\1', template_html, flags=re.DOTALL)
        else:
            template_html = re.sub(r'\{\{#if show_stats\}\}.*?\{\{/if\}\}', '', template_html, flags=re.DOTALL)
        
        template_html = template_html.replace('{{footer_text}}', footer_text)
        
        # Build messages HTML
        messages_html = []
        
        # Find the message template section
        msg_template_match = re.search(r'\{\{#each messages\}\}(.*?)\{\{/each\}\}', template_html, re.DOTALL)
        if not msg_template_match:
            raise ValueError("Template must contain {{#each messages}}...{{/each}} block")
        
        msg_template = msg_template_match.group(1)
        
        # Process each message
        for msg in self.messages:
            msg_html = msg_template
            
            # Check if system message
            is_system = not msg.get('sender') or msg.get('sender') == 'System'
            
            # Check if date changed (for date divider)
            current_date = msg.get('date', '')
            show_date = current_date and current_date != getattr(self, '_last_date', None)
            if show_date:
                self._last_date = current_date
            
            if is_system:
                # System message
                msg_html = re.sub(r'\{\{#if this\.is_system\}\}(.*?)\{\{else\}\}.*?\{\{/if\}\}', r'\1', msg_html, flags=re.DOTALL)
                msg_html = msg_html.replace('{{this.text}}', msg.get('text', ''))
                
                # Show date divider for system messages too
                if show_date:
                    msg_html = re.sub(r'\{\{#if this\.show_date\}\}(.*?)\{\{/if\}\}', r'\1', msg_html, flags=re.DOTALL)
                    msg_html = msg_html.replace('{{this.current_date}}', current_date)
                else:
                    msg_html = re.sub(r'\{\{#if this\.show_date\}\}.*?\{\{/if\}\}', '', msg_html, flags=re.DOTALL)
            else:
                # Regular message
                msg_html = re.sub(r'\{\{#if this\.is_system\}\}.*?\{\{else\}\}(.*?)\{\{/if\}\}', r'\1', msg_html, flags=re.DOTALL)
                
                # Handle {{#unless this.is_system}} blocks (remove them for non-system messages)
                msg_html = re.sub(r'\{\{#unless this\.is_system\}\}(.*?)\{\{/unless\}\}', r'\1', msg_html, flags=re.DOTALL)
                
                msg_html = msg_html.replace('{{this.sender}}', msg.get('sender', ''))
                msg_html = msg_html.replace('{{this.time}}', msg.get('time', ''))
                
                # Show date divider?
                if show_date:
                    msg_html = re.sub(r'\{\{#if this\.show_date\}\}(.*?)\{\{/if\}\}', r'\1', msg_html, flags=re.DOTALL)
                    msg_html = msg_html.replace('{{this.current_date}}', current_date)
                else:
                    msg_html = re.sub(r'\{\{#if this\.show_date\}\}.*?\{\{/if\}\}', '', msg_html, flags=re.DOTALL)
                
                # Replace message date (separate from divider date)
                msg_html = msg_html.replace('{{this.date}}', msg.get('date', ''))
                
                # Clean text - use configured pattern
                text = msg.get('text', '')
                pattern = re.escape(self.str_attached_file)
                text = re.sub(rf'‎[A-Za-z0-9\-\.]+\.(opus|jpg|pdf|etc)\s*\({pattern}\)', '', text)
                msg_html = msg_html.replace('{{this.text}}', text)
                
                # Message class (user vs other)
                # Usa il nome del file ZIP per determinare chi è "other"
                # Tutto ciò che NON è nel nome del file = "user" (il proprietario)
                user_name_config = self.config.get('HTML_TEMPLATE', 'user_name', fallback='')
                
                if user_name_config and user_name_config.strip():
                    # Usa il nome configurato
                    msg_class = 'user' if msg.get('sender') == user_name_config else 'other'
                else:
                    # Rileva automaticamente dal nome file ZIP
                    if not hasattr(self, '_user_sender'):
                        # Estrai nome dal file ZIP usando il pattern configurato
                        zip_basename = Path(self.zip_path).stem
                        
                        # Pattern configurabile per estrarre il nome del contatto
                        # Usa il pattern dal file di lingua o dal config
                        zip_pattern = self.str_zip_pattern
                        
                        # Estrai il nome del contatto
                        if zip_pattern and zip_pattern in zip_basename:
                            chat_contact = zip_basename.split(zip_pattern, 1)[1].strip()
                        else:
                            # Fallback: usa tutto il nome del file
                            chat_contact = zip_basename
                        
                        # Raccogli tutti i mittenti
                        senders = set()
                        for m in self.messages:
                            sender = m.get('sender', '')
                            if sender and sender != 'System':
                                senders.add(sender)
                        
                        # Trova quale mittente corrisponde al nome nel file (quello è "other")
                        other_sender = None
                        for sender in senders:
                            # Match esatto o parziale (case-insensitive)
                            if chat_contact.lower() in sender.lower() or sender.lower() in chat_contact.lower():
                                other_sender = sender
                                break
                            # Match con numero di telefono (rimuovi spazi, + e -)
                            clean_contact = chat_contact.replace(' ', '').replace('+', '').replace('-', '')
                            clean_sender = sender.replace(' ', '').replace('+', '').replace('-', '')
                            if len(clean_contact) > 3 and (clean_contact in clean_sender or clean_sender in clean_contact):
                                other_sender = sender
                                break
                        
                        # Se troviamo un match ed è chat 1-a-1 (2 mittenti)
                        if other_sender and len(senders) == 2:
                            # Chat 1-a-1: user è l'altro mittente
                            remaining = [s for s in senders if s != other_sender]
                            self._user_sender = remaining[0] if remaining else None
                        else:
                            # Gruppo (più di 2 mittenti) o nessun match: tutti "other"
                            self._user_sender = None
                    
                    # Assegna classe
                    msg_class = 'user' if msg.get('sender') == self._user_sender else 'other'
                    
                msg_html = msg_html.replace('{{this.message_class}}', msg_class)
                
                # Handle transcription
                if msg.get('transcription'):
                    msg_html = re.sub(r'\{\{#if this\.transcription\}\}(.*?)\{\{/if\}\}', r'\1', msg_html, flags=re.DOTALL)
                    msg_html = msg_html.replace('{{this.transcription}}', msg.get('transcription', ''))
                else:
                    msg_html = re.sub(r'\{\{#if this\.transcription\}\}.*?\{\{/if\}\}', '', msg_html, flags=re.DOTALL)
                
                # Handle media
                if msg.get('media'):
                    media = msg['media']
                    msg_html = re.sub(r'\{\{#if this\.media\}\}(.*?)\{\{/if\}\}', r'\1', msg_html, flags=re.DOTALL)
                    
                    if media['type'] == 'image' and not exclude_images:
                        msg_html = re.sub(r'\{\{#if this\.media\.is_image\}\}(.*?)\{\{else\}\}.*?\{\{/if\}\}', r'\1', msg_html, flags=re.DOTALL)
                        # Convert image to base64 or use file path
                        import base64
                        with open(media['path'], 'rb') as img_file:
                            img_data = base64.b64encode(img_file.read()).decode()
                            ext = os.path.splitext(media['filename'])[1].lower()
                            mime_type = 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png' if ext == '.png' else 'image/gif'
                            img_src = f"data:{mime_type};base64,{img_data}"
                        msg_html = msg_html.replace('{{this.media.path}}', img_src)
                        msg_html = msg_html.replace('{{this.media.filename}}', media['filename'])
                    else:
                        msg_html = re.sub(r'\{\{#if this\.media\.is_image\}\}.*?\{\{else\}\}(.*?)\{\{/if\}\}', r'\1', msg_html, flags=re.DOTALL)
                        msg_html = msg_html.replace('{{this.media.filename}}', media['filename'])
                else:
                    msg_html = re.sub(r'\{\{#if this\.media\}\}.*?\{\{/if\}\}', '', msg_html, flags=re.DOTALL)
            
            # Clean up any remaining conditionals and tags
            msg_html = re.sub(r'\{\{#unless.*?\}\}.*?\{\{/unless\}\}', '', msg_html, flags=re.DOTALL)
            msg_html = re.sub(r'\{\{#if.*?\}\}', '', msg_html)
            msg_html = re.sub(r'\{\{/if\}\}', '', msg_html)
            msg_html = re.sub(r'\{\{else\}\}', '', msg_html)
            
            # Remove any remaining variable tags
            msg_html = re.sub(r'\{\{this\.\w+\}\}', '', msg_html)
            
            messages_html.append(msg_html)
        
        # Replace messages section
        all_messages = ''.join(messages_html)
        template_html = re.sub(r'\{\{#each messages\}\}.*?\{\{/each\}\}', all_messages, template_html, flags=re.DOTALL)
        
        # Clean up any remaining tags in the full template
        template_html = re.sub(r'\{\{#if.*?\}\}', '', template_html)
        template_html = re.sub(r'\{\{/if\}\}', '', template_html)
        template_html = re.sub(r'\{\{else\}\}', '', template_html)
        template_html = re.sub(r'\{\{#unless.*?\}\}', '', template_html)
        template_html = re.sub(r'\{\{/unless\}\}', '', template_html)
        template_html = re.sub(r'\{\{#each.*?\}\}', '', template_html)
        template_html = re.sub(r'\{\{/each\}\}', '', template_html)
        
        # Remove any remaining variable placeholders
        template_html = re.sub(r'\{\{[\w\.]+\}\}', '', template_html)
        
        return template_html
    
    def generate_pdf_from_html_template(self, template_path: str) -> None:
        """Generate PDF from a complete HTML template.
        
        Args:
            template_path: Path to HTML template file
        """
        if not WEASYPRINT_AVAILABLE:
            print("⚠️  WeasyPrint not available. Installing...")
            os.system("pip install weasyprint")
            print("🔄 Please restart the script after installation.")
            raise ImportError("WeasyPrint is required for HTML templates. Please install it and restart.")
        
        print(f"📝 Generating PDF from HTML template: {template_path}...")
        
        # Render template
        html_content = self._render_html_template(template_path)
        
        # Generate PDF with WeasyPrint
        HTML(string=html_content).write_pdf(self.output_pdf)
        
        print(f"✅ PDF generated successfully: {self.output_pdf}")

    def generate_pdf(self) -> None:
        """Generate the final PDF document."""
        print(f"📝 Generating PDF: {self.output_pdf}...")
        
        # Check if using external HTML template
        html_template_enabled = self.config.getboolean('HTML_TEMPLATE', 'enabled', fallback=False)
        
        if html_template_enabled:
            # Get template path from config
            template_file = self.config.get('HTML_TEMPLATE', 'template_file', fallback='templates/template.html')
            
            # Look for template in script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(script_dir, template_file)
            
            if not os.path.exists(template_path):
                print(f"⚠️  Template file not found: {template_path}")
                print("   Falling back to legacy rendering...")
            else:
                # Use HTML template rendering
                return self.generate_pdf_from_html_template(template_path)
        
        # Legacy ReportLab rendering (existing code)
        
        # Get page size from config
        page_size_name = self.config.get('PDF', 'page_size', fallback='A4')
        page_size = A4 if page_size_name.upper() == 'A4' else letter
        
        # Get margins from config (convert to inch)
        left_margin = self.config.getfloat('PDF', 'left_margin', fallback=0.5) * inch
        right_margin = self.config.getfloat('PDF', 'right_margin', fallback=0.5) * inch
        top_margin = self.config.getfloat('PDF', 'top_margin', fallback=0.5) * inch
        bottom_margin = self.config.getfloat('PDF', 'bottom_margin', fallback=0.5) * inch
        
        # Get colors from config
        title_color = HexColor('#' + self.config.get('COLORS', 'title_color', fallback='075E54'))
        sender_color = HexColor('#' + self.config.get('COLORS', 'sender_color', fallback='075E54'))
        media_color = HexColor('#' + self.config.get('COLORS', 'media_color', fallback='0084FF'))
        system_color = HexColor('#' + self.config.get('COLORS', 'system_color', fallback='808080'))
        
        # Get layout parameters from config
        title_font_size = self.config.getint('LAYOUT', 'title_font_size', fallback=24)
        sender_font_size = self.config.getint('LAYOUT', 'sender_font_size', fallback=11)
        message_font_size = self.config.getint('LAYOUT', 'message_font_size', fallback=10)
        time_font_size = self.config.getint('LAYOUT', 'time_font_size', fallback=8)
        system_font_size = self.config.getint('LAYOUT', 'system_font_size', fallback=9)
        media_font_size = self.config.getint('LAYOUT', 'media_font_size', fallback=9)
        
        title_font = self.config.get('LAYOUT', 'title_font', fallback='Helvetica')
        sender_font = self.config.get('LAYOUT', 'sender_font', fallback='Helvetica-Bold')
        message_font = self.config.get('LAYOUT', 'message_font', fallback='Helvetica')
        time_font = self.config.get('LAYOUT', 'time_font', fallback='Helvetica')
        system_font = self.config.get('LAYOUT', 'system_font', fallback='Helvetica')
        media_font = self.config.get('LAYOUT', 'media_font', fallback='Helvetica')
        
        title_space_after = self.config.getint('LAYOUT', 'title_space_after', fallback=30)
        sender_space_after = self.config.getint('LAYOUT', 'sender_space_after', fallback=6)
        message_space_after = self.config.getint('LAYOUT', 'message_space_after', fallback=12)
        time_space_after = self.config.getint('LAYOUT', 'time_space_after', fallback=4)
        system_space_after = self.config.getint('LAYOUT', 'system_space_after', fallback=12)
        
        message_left_indent = self.config.getint('LAYOUT', 'message_left_indent', fallback=20)
        time_left_indent = self.config.getint('LAYOUT', 'time_left_indent', fallback=20)
        
        spacer_title = self.config.getint('LAYOUT', 'spacer_title', fallback=12)
        spacer_subtitle = self.config.getint('LAYOUT', 'spacer_subtitle', fallback=24)
        spacer_before_image = self.config.getint('LAYOUT', 'spacer_before_image', fallback=8)
        spacer_after_image = self.config.getint('LAYOUT', 'spacer_after_image', fallback=8)
        spacer_between_messages = self.config.getint('LAYOUT', 'spacer_between_messages', fallback=12)
        
        # Get alignment settings
        alignment_map = {'LEFT': TA_LEFT, 'CENTER': TA_CENTER, 'RIGHT': TA_LEFT, 'JUSTIFY': TA_JUSTIFY}
        title_alignment = alignment_map.get(self.config.get('LAYOUT', 'title_alignment', fallback='CENTER'), TA_CENTER)
        message_alignment = alignment_map.get(self.config.get('LAYOUT', 'message_alignment', fallback='JUSTIFY'), TA_JUSTIFY)
        
        page_break_after = self.config.getint('PDF', 'page_break_after_messages', fallback=50)
        
        # Create styles
        styles_base = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles_base['Heading1'],
            fontSize=title_font_size,
            fontName=title_font,
            textColor=title_color,
            spaceAfter=title_space_after,
            alignment=title_alignment
        )
        
        sender_style = ParagraphStyle(
            'SenderStyle',
            parent=styles_base['Normal'],
            fontSize=sender_font_size,
            fontName=sender_font,
            textColor=sender_color,
            spaceAfter=sender_space_after
        )
        
        message_style = ParagraphStyle(
            'MessageStyle',
            parent=styles_base['Normal'],
            fontSize=message_font_size,
            fontName=message_font,
            spaceAfter=message_space_after,
            alignment=message_alignment,
            leftIndent=message_left_indent
        )
        
        time_style = ParagraphStyle(
            'TimeStyle',
            parent=styles_base['Normal'],
            fontSize=time_font_size,
            fontName=time_font,
            textColor=grey,
            spaceAfter=time_space_after,
            leftIndent=time_left_indent
        )
        
        system_style = ParagraphStyle(
            'SystemStyle',
            parent=styles_base['Normal'],
            fontSize=system_font_size,
            fontName=system_font,
            textColor=system_color
        )
        
        media_style = ParagraphStyle(
            'MediaStyle',
            parent=styles_base['Normal'],
            fontSize=media_font_size,
            fontName=media_font,
            textColor=media_color
        )
        
        # Style dictionary for template parser
        styles = {
            'title': title_style,
            'sender': sender_style,
            'message': message_style,
            'time': time_style,
            'system': system_style,
            'media': media_style
        }
        
        # Build PDF
        elements = []
        
        # Title
        chat_title = Path(self.find_chat_file()).stem.replace('.txt', '')
        elements.append(Paragraph("WhatsApp Chat Transcript", title_style))
        elements.append(Spacer(1, spacer_title))
        elements.append(Paragraph(f"<b>{chat_title}</b>", styles_base['Normal']))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
                                 time_style))
        elements.append(Spacer(1, spacer_subtitle))
        
        # Check if using template-based layout
        use_template = self.config.getboolean('TEMPLATE', 'enabled', fallback=False)
        use_html_template = self.config.getboolean('TEMPLATE', 'html_enabled', fallback=False)
        
        if use_html_template:
            # HTML template-based rendering
            message_template = self.config.get('TEMPLATE', 'html_message_format', 
                fallback='<b><font color="#25D366">{{sender}}</font></b> <font color="#808080" size="8">• {{date}} {{time}}</font><br/>{{text}}<br/>[transcription][image][media][spacer:12]')
            system_template = self.config.get('TEMPLATE', 'html_system_format',
                fallback='<i><font color="#808080">{{text}}</font></i><br/>[spacer:8]')
            
            for i, msg in enumerate(self.messages):
                if not msg.get('sender'):
                    # System message
                    msg_elements = self._parse_html_template(system_template, msg, styles)
                    elements.extend(msg_elements)
                else:
                    # Regular message
                    msg_elements = self._parse_html_template(message_template, msg, styles)
                    elements.extend(msg_elements)
                
                # Add page break after N messages
                if page_break_after > 0 and (i + 1) % page_break_after == 0:
                    elements.append(PageBreak())
                    
        elif use_template:
            # Markup template-based rendering
            message_template = self.config.get('TEMPLATE', 'message_format', 
                fallback='[style:sender]{sender} • {date} {time}[/style][br][style:message]{text}[/style][spacer:6][transcription][image][media][spacer:12]')
            system_template = self.config.get('TEMPLATE', 'system_format',
                fallback='[style:system]{text}[/style][spacer:8]')
            
            for i, msg in enumerate(self.messages):
                if not msg.get('sender'):
                    # System message
                    msg_elements = self._parse_template(system_template, msg, styles)
                    elements.extend(msg_elements)
                else:
                    # Regular message
                    msg_elements = self._parse_template(message_template, msg, styles)
                    elements.extend(msg_elements)
                
                # Add page break after N messages
                if page_break_after > 0 and (i + 1) % page_break_after == 0:
                    elements.append(PageBreak())
        else:
            # Legacy hardcoded rendering
            for i, msg in enumerate(self.messages):
                if not msg.get('sender'):
                    # System message
                    elements.append(Paragraph(f"<i>{msg.get('text', '')}</i>", system_style))
                    elements.append(Spacer(1, system_space_after))
                    continue
                
                # Regular message
                sender_text = f"{msg['sender']} • {msg.get('date', '')} {msg.get('time', '')}"
                elements.append(Paragraph(sender_text, sender_style))
                
                # Add transcription if available
                if msg.get('transcription'):
                    elements.append(Paragraph(f"<i>🎙️ {self.str_audio_label} {msg['transcription']}</i>", message_style))
                
                # Add message text
                if msg.get('text') and not msg['text'].startswith('‎'):
                    text = msg['text']
                    # Remove media file references - use configured pattern
                    pattern = re.escape(self.str_attached_file)
                    text = re.sub(rf'‎[A-Za-z0-9\-\.]+\.(opus|jpg|pdf|etc)\s*\({pattern}\)', '', text)
                    if text.strip() and text.strip() != f'({self.str_attached_file})':
                        elements.append(Paragraph(text, message_style))
                
                # Check if images should be excluded (privacy setting)
                exclude_images = self.config.getboolean('PRIVACY', 'exclude_images', fallback=False)
                
                # Add image if present (unless excluded for privacy)
                if msg.get('media') and msg['media']['type'] == 'image':
                    if exclude_images:
                        # Show link instead of embedding image
                        media_info = msg['media']
                        media_link = f"🖼️ <b>{self.str_image_label}</b>: {media_info['filename']} ({self.str_image_excluded})"
                        elements.append(Paragraph(media_link, media_style))
                    else:
                        # Embed image normally
                        elements.append(Spacer(1, spacer_before_image))
                        img = self.get_image_for_pdf(msg['media']['path'])
                        if img:
                            elements.append(img)
                        elements.append(Spacer(1, spacer_after_image))
                
                # Add media link for other types
                elif msg.get('media'):
                    media_info = msg['media']
                    media_link = f"📎 <b>{media_info['type'].upper()}</b>: {media_info['filename']}"
                    elements.append(Paragraph(media_link, media_style))
                
                elements.append(Spacer(1, spacer_between_messages))
                
                # Add page break after N messages
                if page_break_after > 0 and (i + 1) % page_break_after == 0:
                    elements.append(PageBreak())
        
        # Create PDF
        doc = SimpleDocTemplate(
            self.output_pdf,
            pagesize=page_size,
            rightMargin=right_margin,
            leftMargin=left_margin,
            topMargin=top_margin,
            bottomMargin=bottom_margin
        )
        
        doc.build(elements)
        print(f"✅ PDF generated successfully: {self.output_pdf}")
    
    def cleanup(self) -> None:
        """Clean up temporary files."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"🧹 Cleaned up temporary files")
    
    def process(self) -> str:
        """Main processing pipeline."""
        try:
            self.extract_zip()
            self.parse_chat()
            self.enhance_messages_with_media()
            self.generate_pdf()
            return self.output_pdf
        finally:
            self.cleanup()


def main():
    """Main entry point."""
    import argparse
    import glob
    from datetime import datetime
    
    parser = argparse.ArgumentParser(
        description='WhatsApp Chat to PDF Converter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file
  python main.py chat.zip
  python main.py chat.zip -o output.pdf
  python main.py chat.zip -l it
  
  # Batch mode (all .zip files in current directory)
  python main.py --batch
  python main.py --batch -l it
  python main.py --batch --pattern "Chat*.zip"
  
Supported languages: it, en, es, fr, de, pt, ru, ja, ko, zh, and many more
(leave blank for auto-detect)
        """
    )
    
    # Positional or optional
    parser.add_argument('zip_file', nargs='?', help='WhatsApp chat ZIP file')
    parser.add_argument('-o', '--output', help='Output PDF filename')
    parser.add_argument('-l', '--language', help='Language for transcription (e.g., it, en, es)')
    
    # Batch mode
    parser.add_argument('--batch', action='store_true', help='Process all .zip files in current directory')
    parser.add_argument('--pattern', default='*.zip', help='File pattern for batch mode (default: *.zip)')
    parser.add_argument('--skip-existing', action='store_true', help='Skip files that already have PDF output')
    
    args = parser.parse_args()
    
    # Batch mode
    if args.batch:
        return batch_process(args.pattern, args.language, args.skip_existing)
    
    # Single file mode
    if not args.zip_file:
        parser.print_help()
        return 1
    
    if not os.path.exists(args.zip_file):
        print(f"❌ Error: File '{args.zip_file}' not found")
        return 1
    
    try:
        converter = WhatsAppChatToPDF(args.zip_file, args.output, args.language)
        output_pdf = converter.process()
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def batch_process(pattern: str, language: Optional[str], skip_existing: bool) -> int:
    """Process multiple ZIP files in batch mode."""
    import glob
    from datetime import datetime
    
    # Load config to get default language if not specified via CLI
    if language is None:
        config = configparser.ConfigParser()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'config.ini')
        if not os.path.exists(config_path):
            config_path = os.path.join(script_dir, 'config.example.ini')
        if os.path.exists(config_path):
            config.read(config_path)
            language = config.get('WHISPER', 'language', fallback=None)
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     WhatsApp Chat Batch Converter                         ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    start_time = datetime.now()
    
    # Find all ZIP files
    zip_files = sorted(glob.glob(pattern))
    
    if not zip_files:
        print(f"❌ No files found matching pattern: {pattern}")
        return 1
    
    print(f"📋 Found {len(zip_files)} file(s)")
    print(f"🌍 Language: {language or 'auto-detect'}")
    print()
    
    results = []
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for i, zip_file in enumerate(zip_files, 1):
        file_start = datetime.now()
        
        # Generate output name
        output_pdf = Path(zip_file).stem + "_transcript.pdf"
        
        # Skip if exists
        if skip_existing and os.path.exists(output_pdf):
            print(f"⏭️  [{i}/{len(zip_files)}] Skipping: {zip_file}")
            print(f"   Output already exists: {output_pdf}")
            print()
            skip_count += 1
            results.append({
                'file': zip_file,
                'status': 'skipped',
                'output': output_pdf
            })
            continue
        
        print(f"🔄 [{i}/{len(zip_files)}] Processing: {zip_file}")
        
        try:
            converter = WhatsAppChatToPDF(zip_file, output_pdf, language)
            converter.process()
            
            file_time = (datetime.now() - file_start).total_seconds()
            file_size = os.path.getsize(output_pdf)
            size_kb = file_size / 1024
            
            print(f"✅ ✓ Success: {zip_file}")
            print(f"   Output: {output_pdf} ({size_kb:.0f} KB)")
            print(f"   Time: {file_time:.0f}s")
            print()
            
            success_count += 1
            results.append({
                'file': zip_file,
                'status': 'success',
                'output': output_pdf,
                'time': file_time,
                'size': size_kb
            })
            
        except Exception as e:
            print(f"❌ ✗ Failed: {zip_file}")
            print(f"   Error: {str(e)}")
            print()
            
            fail_count += 1
            results.append({
                'file': zip_file,
                'status': 'failed',
                'error': str(e)
            })
    
    # Summary
    total_time = (datetime.now() - start_time).total_seconds()
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     Summary                                                ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    print(f"📊 Total files: {len(zip_files)}")
    print(f"✅ Success: {success_count}")
    if skip_count > 0:
        print(f"⏭️  Skipped: {skip_count}")
    if fail_count > 0:
        print(f"❌ Failed: {fail_count}")
    print(f"⏱️  Total time: {total_time:.0f}s ({total_time/60:.1f}m)")
    print()
    
    # Save log
    log_file = "batch_convert_log.txt"
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Batch Conversion Log - {datetime.now()}\n")
        f.write(f"Pattern: {pattern}\n")
        f.write(f"Language: {language or 'auto-detect'}\n")
        f.write(f"\n")
        
        for result in results:
            f.write(f"\nFile: {result['file']}\n")
            f.write(f"Status: {result['status']}\n")
            if result['status'] == 'success':
                f.write(f"Output: {result['output']}\n")
                f.write(f"Time: {result['time']:.0f}s\n")
                f.write(f"Size: {result['size']:.0f} KB\n")
            elif result['status'] == 'failed':
                f.write(f"Error: {result['error']}\n")
    
    print(f"📝 Log saved to: {log_file}")
    
    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
