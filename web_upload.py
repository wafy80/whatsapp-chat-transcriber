#!/usr/bin/env python3
"""
Simple web server to upload and process WhatsApp chat ZIP files.
"""

import os
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import cgi
import subprocess
import sys
import argparse

class UploadHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Serve the upload form, PWA assets, or download PDF"""
        # Handle processing endpoint
        if self.path.startswith('/process?'):
            from urllib.parse import parse_qs, urlparse
            
            query = urlparse(self.path).query
            params = parse_qs(query)
            
            filename = params.get('filename', [''])[0]
            language = params.get('language', [''])[0]
            
            if not filename:
                self.send_json_response({'success': False, 'error': 'No filename provided'})
                return
            
            filepath = os.path.join('uploads', filename)
            
            if not os.path.exists(filepath):
                self.send_json_response({'success': False, 'error': 'File not found'})
                return
            
            # Process the file
            try:
                output_pdf = filename.replace('.zip', '_transcript.pdf')
                output_path = os.path.join(os.getcwd(), output_pdf)
                cmd = [sys.executable, 'main.py', filepath, '-o', output_path]
                
                if language:
                    cmd.extend(['-l', language])
                
                print(f"Running: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                print(f"Return code: {result.returncode}")
                print(f"Output file exists: {os.path.exists(output_path)}")
                
                if result.returncode == 0 and os.path.exists(output_path):
                    # Return PDF directly
                    self.send_response(200)
                    self.send_header('Content-type', 'application/pdf')
                    self.send_header('Content-Disposition', f'attachment; filename="{output_pdf}"')
                    self.send_header('Content-Length', str(os.path.getsize(output_path)))
                    self.end_headers()
                    
                    with open(output_path, 'rb') as f:
                        self.wfile.write(f.read())
                    
                    # Clean up
                    os.remove(output_path)
                    return
                else:
                    error_msg = result.stderr if result.stderr else 'Unknown error'
                    self.send_json_response({
                        'success': False,
                        'error': f'Processing failed: {error_msg}'
                    })
            
            except subprocess.TimeoutExpired:
                self.send_json_response({
                    'success': False,
                    'error': 'Processing timeout (>10 minutes)'
                })
            except Exception as e:
                self.send_json_response({
                    'success': False,
                    'error': str(e)
                })
            finally:
                # Clean up uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
            
            return
        
        # Serve icons
        if self.path in ['/icon-192.png', '/icon-512.png']:
            size = 192 if '192' in self.path else 512
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.send_header('Cache-Control', 'public, max-age=31536000')
            self.end_headers()
            
            try:
                from PIL import Image, ImageDraw
                import io
                
                # Create simple icon with gradient
                img = Image.new('RGB', (size, size), color=(102, 126, 234))
                draw = ImageDraw.Draw(img)
                
                # Draw white circle in center
                margin = size // 4
                draw.ellipse([margin, margin, size-margin, size-margin], fill='white', outline=(102, 126, 234), width=size//20)
                
                # Draw chat bubble symbol
                chat_size = size // 3
                chat_x = size // 2 - chat_size // 2
                chat_y = size // 2 - chat_size // 2
                draw.rounded_rectangle([chat_x, chat_y, chat_x + chat_size, chat_y + chat_size * 0.7], 
                                       radius=size//15, fill=(102, 126, 234))
                # Tail of bubble
                tail_points = [(chat_x + chat_size * 0.3, chat_y + chat_size * 0.7),
                              (chat_x + chat_size * 0.2, chat_y + chat_size * 0.9),
                              (chat_x + chat_size * 0.4, chat_y + chat_size * 0.7)]
                draw.polygon(tail_points, fill=(102, 126, 234))
                
                # Save to bytes
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG', optimize=True)
                self.wfile.write(img_bytes.getvalue())
            except ImportError:
                # Fallback: simple solid color PNG if PIL not available
                import base64
                png_data = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')
                self.wfile.write(png_data)
            return
        
        # Serve service worker
        if self.path == '/sw.js':
            self.send_response(200)
            self.send_header('Content-type', 'application/javascript')
            self.end_headers()
            
            sw_code = """
const CACHE_NAME = 'chat2pdf-v1';

self.addEventListener('install', (event) => {
    console.log('Service Worker installed');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('Service Worker activated');
    event.waitUntil(clients.claim());
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request);
        })
    );
});
"""
            self.wfile.write(sw_code.encode('utf-8'))
            return
        
        # Serve manifest.json
        if self.path == '/manifest.json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            import json
            manifest = {
                "name": "WhatsApp Chat to PDF Converter",
                "short_name": "Chat2PDF",
                "description": "Convert WhatsApp chats to PDF with audio transcription",
                "start_url": "/",
                "scope": "/",
                "display": "standalone",
                "display_override": ["standalone", "fullscreen"],
                "background_color": "#ffffff",
                "theme_color": "#667eea",
                "orientation": "portrait",
                "prefer_related_applications": False,
                "categories": ["productivity", "utilities"],
                "icons": [
                    {
                        "src": "/icon-192.png",
                        "sizes": "192x192",
                        "type": "image/png",
                        "purpose": "any"
                    },
                    {
                        "src": "/icon-512.png",
                        "sizes": "512x512",
                        "type": "image/png",
                        "purpose": "maskable"
                    },
                    {
                        "src": "/icon-512.png",
                        "sizes": "512x512",
                        "type": "image/png",
                        "purpose": "any"
                    }
                ],
                "share_target": {
                    "action": "/share",
                    "method": "POST",
                    "enctype": "multipart/form-data",
                    "params": {
                        "title": "title",
                        "text": "text",
                        "files": [
                            {
                                "name": "file",
                                "accept": ["application/zip", "application/x-zip-compressed", ".zip"]
                            }
                        ]
                    }
                }
            }
            
            self.wfile.write(json.dumps(manifest, indent=2).encode('utf-8'))
            return
        
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WhatsApp Chat to PDF</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#667eea">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Chat2PDF">
    <link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">
    <link rel="apple-touch-icon" href="/icon-512.png">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 500px;
            width: 100%;
        }
        h1 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 24px;
            text-align: center;
        }
        .subtitle {
            color: #666;
            font-size: 14px;
            margin-bottom: 30px;
            text-align: center;
        }
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 40px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: #f8f9ff;
            margin-bottom: 20px;
        }
        .upload-area:hover { background: #f0f2ff; transform: translateY(-2px); }
        .upload-area.drag-over, .upload-area.dragover { background: #e8ebff; border-color: #764ba2; transform: scale(1.02); }
        .upload-icon { font-size: 48px; margin-bottom: 15px; }
        .upload-text { color: #667eea; font-size: 16px; font-weight: 500; }
        .upload-hint { color: #999; font-size: 12px; margin-top: 8px; }
        input[type="file"] { display: none; }
        select, button {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            margin-bottom: 15px;
            transition: all 0.3s;
        }
        select:focus { outline: none; border-color: #667eea; }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            font-weight: 600;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4); }
        button:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            display: none;
            text-align: center;
            font-size: 14px;
        }
        .status.success { background: #d4edda; color: #155724; display: block; }
        .status.error { background: #f8d7da; color: #721c24; display: block; }
        .status.processing { background: #d1ecf1; color: #0c5460; display: block; }
        .file-info {
            margin: 15px 0;
            padding: 15px;
            background: #e8f5e9;
            border-radius: 10px;
            color: #2e7d32;
            display: none;
        }
        .loader {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            display: inline-block;
            margin-right: 10px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .install-btn {
            display: none;
            margin-bottom: 20px;
            padding: 12px 24px;
            background: #25d366;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            font-size: 16px;
        }
        .install-btn:hover {
            background: #20bd5a;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 WhatsApp Chat to PDF</h1>
        <p class="subtitle">Convert your WhatsApp chats to PDF with audio transcription</p>
        
        <button id="installBtn" class="install-btn">
            ⬇️ Install App (Enable WhatsApp Share)
        </button>
        
        <form id="uploadForm">
            <div class="upload-area" id="uploadArea">
                <div class="upload-icon">📁</div>
                <div class="upload-text">Click or drag ZIP file here</div>
                <div class="upload-hint">WhatsApp exported chat (.zip)</div>
                <input type="file" id="fileInput" name="file" accept=".zip" required>
            </div>
            
            <div class="file-info" id="fileInfo"></div>
            
            <select id="language" name="language">
                <option value="">Auto-detect language</option>
                <option value="en">English</option>
                <option value="es">Español</option>
                <option value="fr">Français</option>
                <option value="de">Deutsch</option>
                <option value="it">Italiano</option>
                <option value="pt">Português</option>
                <option value="ja">日本語</option>
                <option value="zh">中文</option>
                <option value="ru">Русский</option>
                <option value="nl">Nederlands</option>
                <option value="ko">한국어</option>
            </select>
            
            <button type="submit" id="submitBtn">Convert to PDF</button>
        </form>
        
        <div class="status" id="status"></div>
    </div>

    <script>
        // PWA Install handling
        let deferredPrompt;
        const installBtn = document.getElementById('installBtn');
        
        // Hide install button by default
        installBtn.style.display = 'none';
        
        // Capture beforeinstallprompt event - only then show the button
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            // Only show button if NOT in standalone mode
            if (!window.matchMedia('(display-mode: standalone)').matches && !window.navigator.standalone) {
                installBtn.style.display = 'block';
            }
        });
        
        // Handle install button click
        installBtn.addEventListener('click', async () => {
            if (!deferredPrompt) {
                return;
            }
            
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            
            if (outcome === 'accepted') {
                installBtn.textContent = '✅ App Installed!';
                setTimeout(() => {
                    installBtn.style.display = 'none';
                }, 2000);
            }
            
            deferredPrompt = null;
        });
        
        // Register Service Worker
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(reg => console.log('Service Worker registered'))
                .catch(err => console.error('SW registration failed:', err));
        }

        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const fileInfo = document.getElementById('fileInfo');
        const form = document.getElementById('uploadForm');
        const submitBtn = document.getElementById('submitBtn');
        const status = document.getElementById('status');

        // Check if shared from external app
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('shared') === 'true') {
            // File was shared, show message
            console.log('File shared from external app');
        }

        uploadArea.addEventListener('click', () => fileInput.click());

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const file = files[0];
                if (!file.name.endsWith('.zip')) {
                    alert('Please upload a ZIP file');
                    return;
                }
                
                // Create a new DataTransfer to programmatically set files
                const dt = new DataTransfer();
                dt.items.add(file);
                fileInput.files = dt.files;
                
                showFileInfo(file);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                showFileInfo(e.target.files[0]);
            }
        });

        function showFileInfo(file) {
            const sizeMB = (file.size / 1024 / 1024).toFixed(2);
            fileInfo.textContent = `✅ ${file.name} (${sizeMB} MB)`;
            fileInfo.style.display = 'block';
        }

        function showStatus(message, type) {
            status.className = 'status ' + type;
            status.innerHTML = message;
        }

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const file = fileInput.files[0];
            if (!file) {
                showStatus('Please select a file', 'error');
                return;
            }

            if (!file.name.endsWith('.zip')) {
                showStatus('Please select a ZIP file', 'error');
                return;
            }

            submitBtn.disabled = true;
            showStatus('<span class="loader"></span>Uploading and processing... This may take several minutes', 'processing');

            const formData = new FormData();
            formData.append('file', file);
            formData.append('language', document.getElementById('language').value);

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/pdf')) {
                        // PDF returned directly - download it
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = file.name.replace('.zip', '_transcript.pdf');
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                        
                        showStatus('✅ PDF generated and downloaded successfully!', 'success');
                        
                        // Reset form
                        setTimeout(() => {
                            form.reset();
                            fileInfo.style.display = 'none';
                            status.style.display = 'none';
                        }, 3000);
                    } else {
                        const result = await response.json();
                        if (result.success) {
                            showStatus('✅ ' + result.message, 'success');
                        } else {
                            showStatus('❌ Error: ' + result.error, 'error');
                        }
                    }
                } else {
                    showStatus('❌ Server error: ' + response.statusText, 'error');
                }
            } catch (error) {
                showStatus('❌ Error: ' + error.message, 'error');
            } finally {
                submitBtn.disabled = false;
            }
        });
    </script>
</body>
</html>"""
            self.wfile.write(html.encode('utf-8'))
            return

    def do_POST(self):
        """Handle file upload"""
        # Handle WhatsApp share
        if self.path == '/share':
            try:
                # Parse multipart form data
                content_type = self.headers['Content-Type']
                if 'multipart/form-data' not in content_type:
                    self.send_json_response({'success': False, 'error': 'Invalid content type'})
                    return

                # Create uploads directory
                os.makedirs('uploads', exist_ok=True)

                # Parse form data
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST'}
                )

                # Get file
                if 'file' not in form:
                    self.send_json_response({'success': False, 'error': 'No file uploaded'})
                    return

                fileitem = form['file']
                if not fileitem.filename:
                    self.send_json_response({'success': False, 'error': 'No file selected'})
                    return

                # Save file
                filename = os.path.basename(fileitem.filename)
                filepath = os.path.join('uploads', filename)
                
                with open(filepath, 'wb') as f:
                    f.write(fileitem.file.read())

                print(f"📱 File shared from WhatsApp: {filepath}")
                
                # Get language if specified
                language = form.getvalue('language', '')
                
                # Show processing page
                self.send_processing_page(filename, language)
                return

            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
                self.send_json_response({
                    'success': False,
                    'error': str(e)
                })
            return
        
        # Handle normal upload
        if self.path == '/upload':
            try:
                # Parse multipart form data
                content_type = self.headers['Content-Type']
                if 'multipart/form-data' not in content_type:
                    self.send_json_response({'success': False, 'error': 'Invalid content type'})
                    return

                # Create uploads directory
                os.makedirs('uploads', exist_ok=True)

                # Parse form data
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST'}
                )

                # Get file
                if 'file' not in form:
                    self.send_json_response({'success': False, 'error': 'No file uploaded'})
                    return

                fileitem = form['file']
                if not fileitem.filename:
                    self.send_json_response({'success': False, 'error': 'No file selected'})
                    return

                # Save file
                filename = os.path.basename(fileitem.filename)
                filepath = os.path.join('uploads', filename)
                
                with open(filepath, 'wb') as f:
                    f.write(fileitem.file.read())

                # Get language
                language = form.getvalue('language', '')

                # Process file
                output_pdf = filename.replace('.zip', '_transcript.pdf')
                output_path = os.path.join(os.getcwd(), output_pdf)
                cmd = [sys.executable, 'main.py', filepath, '-o', output_path]
                
                if language:
                    cmd.extend(['-l', language])

                print(f"Running: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

                if result.returncode == 0 and os.path.exists(output_path):
                    # Return PDF directly
                    self.send_response(200)
                    self.send_header('Content-type', 'application/pdf')
                    self.send_header('Content-Disposition', f'attachment; filename="{output_pdf}"')
                    self.send_header('Content-Length', str(os.path.getsize(output_path)))
                    self.end_headers()
                    
                    with open(output_path, 'rb') as f:
                        self.wfile.write(f.read())
                    
                    # Clean up
                    os.remove(output_path)
                else:
                    error_msg = result.stderr if result.stderr else 'Unknown error'
                    self.send_json_response({
                        'success': False,
                        'error': f'Processing failed: {error_msg}'
                    })

            except subprocess.TimeoutExpired:
                self.send_json_response({
                    'success': False,
                    'error': 'Processing timeout (>10 minutes)'
                })
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
                self.send_json_response({
                    'success': False,
                    'error': str(e)
                })
            finally:
                # Clean up uploaded file
                if 'filepath' in locals() and os.path.exists(filepath):
                    os.remove(filepath)

    def send_processing_page(self, filename, language):
        """Send processing page that handles conversion and download"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # URL encode filename for API call
        from urllib.parse import quote
        filename_encoded = quote(filename)
        lang_param = f"&language={language}" if language else ""
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Processing...</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .container {{
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 500px;
            width: 100%;
            text-align: center;
        }}
        h1 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 24px;
        }}
        .spinner {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            animation: spin 1s linear infinite;
            margin: 30px auto;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        .status {{
            color: #666;
            margin: 20px 0;
            font-size: 16px;
        }}
        .filename {{
            color: #333;
            font-weight: 600;
            margin: 10px 0;
            word-break: break-word;
        }}
        .success {{
            display: none;
            color: #4caf50;
            font-size: 48px;
            margin: 20px 0;
        }}
        .error {{
            display: none;
            background: #ffebee;
            color: #c62828;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }}
        .back-btn {{
            display: none;
            margin-top: 20px;
            padding: 12px 24px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Processing Your Chat</h1>
        
        <div id="processing">
            <div class="spinner"></div>
            <div class="filename">{filename}</div>
            <div class="status" id="status">Converting to PDF...</div>
            <p style="font-size: 12px; color: #999; margin-top: 20px;">
                This may take a few minutes depending on file size
            </p>
        </div>
        
        <div class="success" id="success">✅</div>
        
        <div class="error" id="error"></div>
        
        <a href="/" class="back-btn" id="backBtn">← Back to Upload</a>
    </div>

    <script>
        async function processFile() {{
            try {{
                const response = await fetch('/process?filename={filename_encoded}{lang_param}');
                
                if (!response.ok) {{
                    throw new Error('Processing failed');
                }}
                
                const contentType = response.headers.get('content-type');
                
                if (contentType && contentType.includes('application/pdf')) {{
                    // Success - download PDF
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = '{filename}'.replace('.zip', '_transcript.pdf');
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    // Show success
                    document.getElementById('processing').style.display = 'none';
                    document.getElementById('success').style.display = 'block';
                    document.getElementById('status').textContent = 'PDF downloaded successfully!';
                    document.getElementById('status').style.color = '#4caf50';
                    document.getElementById('backBtn').style.display = 'inline-block';
                    
                    // Auto-redirect after 3 seconds
                    setTimeout(() => {{
                        window.location.href = '/';
                    }}, 3000);
                }} else {{
                    const data = await response.json();
                    throw new Error(data.error || 'Unknown error');
                }}
            }} catch (error) {{
                console.error('Error:', error);
                document.getElementById('processing').style.display = 'none';
                document.getElementById('error').style.display = 'block';
                document.getElementById('error').innerHTML = `
                    <div style="font-size: 48px; margin-bottom: 10px;">❌</div>
                    <h2>Error</h2>
                    <p style="margin: 10px 0;">${{error.message}}</p>
                `;
                document.getElementById('backBtn').style.display = 'inline-block';
            }}
        }}
        
        // Start processing
        processFile();
    </script>
</body>
</html>
        """
        
        self.wfile.write(html.encode('utf-8'))

    def send_json_response(self, data):
        """Send JSON response"""
        import json
        self.send_response(200 if data.get('success') else 400)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def log_message(self, format, *args):
        """Custom logging"""
        print(f"[{self.address_string()}] {format % args}")


def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def main():
    parser = argparse.ArgumentParser(description='WhatsApp Chat to PDF Web Upload Server')
    parser.add_argument('--port', type=int, default=58080, help='Port to listen on (default: 58080)')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), UploadHandler)
    local_ip = get_local_ip()
    
    print("=" * 60)
    print("WhatsApp Chat to PDF - Web Upload Server")
    print("=" * 60)
    print(f"\n✅ Server started successfully!\n")
    print(f"📱 On your phone, open:")
    print(f"   http://{local_ip}:{args.port}")
    print(f"\n💻 On this computer:")
    print(f"   http://localhost:{args.port}")
    print(f"\n🔧 Press Ctrl+C to stop the server\n")
    print("=" * 60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
        server.shutdown()


if __name__ == '__main__':
    main()
