#!/usr/bin/env python3
"""
Simple web server to receive WhatsApp chat ZIP files directly from phone
and process them automatically.
"""

import os
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote
import cgi
import subprocess
import sys
import argparse

class UploadHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Serve the upload form or download PDF"""
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
                from PIL import Image, ImageDraw, ImageFont
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
                # Minimal 1x1 purple PNG
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
    // Cache-first strategy for static assets
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
                "start_url": "/?source=pwa",
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
        
        # Check if this is a download request
        if self.path.startswith('/download/'):
            # Decode URL-encoded filename
            filename = unquote(self.path.replace('/download/', ''))
            filepath = os.path.join(os.getcwd(), filename)
            
            print(f"Download request for: {filename}")
            print(f"Looking for file at: {filepath}")
            print(f"File exists: {os.path.exists(filepath)}")
            
            if os.path.exists(filepath):
                self.send_response(200)
                self.send_header('Content-type', 'application/pdf')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.send_header('Content-Length', str(os.path.getsize(filepath)))
                self.end_headers()
                
                with open(filepath, 'rb') as f:
                    self.wfile.write(f.read())
                
                # Clean up PDF after download
                try:
                    os.remove(filepath)
                    print(f"Cleaned up: {filepath}")
                except Exception as e:
                    print(f"Could not remove {filepath}: {e}")
                return
            else:
                print(f"File not found: {filepath}")
                self.send_error(404, f"File not found: {filename}")
                return
        
        # Serve the upload form
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = """
<!DOCTYPE html>
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
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 500px;
            width: 100%;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .upload-area {
            border: 3px dashed #ddd;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            background: #f9f9f9;
            transition: all 0.3s;
            cursor: pointer;
            margin-bottom: 20px;
        }
        .upload-area:hover {
            border-color: #667eea;
            background: #f0f0ff;
        }
        .upload-area.dragover {
            border-color: #667eea;
            background: #e8e8ff;
            transform: scale(1.02);
        }
        .upload-icon {
            font-size: 48px;
            margin-bottom: 15px;
        }
        input[type="file"] {
            display: none;
        }
        .file-info {
            margin: 15px 0;
            padding: 15px;
            background: #e8f5e9;
            border-radius: 10px;
            color: #2e7d32;
            display: none;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #555;
            font-weight: 500;
            font-size: 14px;
        }
        select {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 16px;
            margin-bottom: 20px;
            background: white;
        }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102,126,234,0.4);
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .progress {
            display: none;
            margin-top: 20px;
            text-align: center;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .result {
            display: none;
            margin-top: 20px;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .result.success {
            background: #e8f5e9;
            color: #2e7d32;
        }
        .result.error {
            background: #ffebee;
            color: #c62828;
        }
        .download-link {
            display: inline-block;
            margin-top: 15px;
            padding: 12px 30px;
            background: #4caf50;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
        }
        .download-link:hover {
            background: #45a049;
        }
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
        .install-btn.show {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 WhatsApp to PDF</h1>
        <p class="subtitle">Upload your WhatsApp chat export and get a beautiful PDF</p>
        
        <button id="installBtn" class="install-btn">
            ⬇️ Install App (Enable WhatsApp Share)
        </button>
        
        <form id="uploadForm" enctype="multipart/form-data" method="POST">
            <div class="upload-area" id="uploadArea">
                <div class="upload-icon">📤</div>
                <p><strong>Click to select</strong> or drag and drop</p>
                <p style="font-size: 12px; color: #999; margin-top: 5px;">WhatsApp chat ZIP file</p>
                <input type="file" id="fileInput" name="file" accept=".zip" required>
            </div>
            
            <div class="file-info" id="fileInfo"></div>
            
            <label for="language">Transcription Language (optional)</label>
            <select name="language" id="language">
                <option value="">Auto-detect</option>
                <option value="en">🇬🇧 English</option>
                <option value="es">🇪🇸 Spanish</option>
                <option value="fr">🇫🇷 French</option>
                <option value="de">🇩🇪 German</option>
                <option value="it">🇮🇹 Italian</option>
                <option value="pt">🇵🇹 Portuguese</option>
                <option value="ja">🇯🇵 Japanese</option>
                <option value="zh">🇨🇳 Chinese</option>
                <option value="ru">🇷🇺 Russian</option>
                <option value="nl">🇳🇱 Dutch</option>
                <option value="ko">🇰🇷 Korean</option>
            </select>
            
            <button type="submit" id="submitBtn">Convert to PDF</button>
        </form>
        
        <div class="progress" id="progress">
            <div class="spinner"></div>
            <p>Processing your chat...</p>
            <p style="font-size: 12px; color: #666; margin-top: 10px;">This may take a few minutes</p>
        </div>
        
        <div class="result" id="result"></div>
    </div>

    <script>
        // PWA Install handling
        let deferredPrompt;
        const installBtn = document.getElementById('installBtn');
        
        // Check if running as installed PWA
        if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true) {
            console.log('✅ Running as installed PWA');
            installBtn.style.display = 'none';
        }
        
        // Capture the beforeinstallprompt event
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('✅ beforeinstallprompt fired - PWA is installable');
            e.preventDefault();
            deferredPrompt = e;
            installBtn.classList.add('show');
        });
        
        // Handle install button click
        installBtn.addEventListener('click', async () => {
            if (!deferredPrompt) {
                console.log('❌ No deferred prompt');
                alert('App is already installed or cannot be installed on this device/browser.\n\nTry:\n1. Chrome/Edge on Android\n2. Open via HTTPS\n3. Clear browser data and reload');
                return;
            }
            
            console.log('📱 Showing install prompt');
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            console.log(`User response: ${outcome}`);
            
            if (outcome === 'accepted') {
                console.log('✅ User accepted installation');
                installBtn.textContent = '✅ App Installed!';
                setTimeout(() => {
                    installBtn.classList.remove('show');
                }, 3000);
            } else {
                console.log('❌ User dismissed installation');
            }
            
            deferredPrompt = null;
        });
        
        // Check if already installed
        window.addEventListener('appinstalled', () => {
            console.log('✅ PWA was installed successfully');
            installBtn.classList.remove('show');
        });
        
        // Register Service Worker for PWA
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js')
                    .then(reg => {
                        console.log('✅ Service Worker registered:', reg.scope);
                    })
                    .catch(err => {
                        console.error('❌ Service Worker registration failed:', err);
                    });
            });
        } else {
            console.warn('⚠️ Service Worker not supported');
        }

        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const fileInfo = document.getElementById('fileInfo');
        const form = document.getElementById('uploadForm');
        const submitBtn = document.getElementById('submitBtn');
        const progress = document.getElementById('progress');
        const result = document.getElementById('result');

        // Check if shared from external app
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('shared') === 'true') {
            // File was shared, show message
            console.log('File shared from external app');
        }

        uploadArea.addEventListener('click', () => fileInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                const file = e.dataTransfer.files[0];
                if (!file.name.endsWith('.zip')) {
                    alert('Please upload a ZIP file');
                    return;
                }
                // Create a new FileList-like object
                try {
                    const dt = new DataTransfer();
                    dt.items.add(file);
                    fileInput.files = dt.files;
                    showFileInfo(file);
                } catch (error) {
                    console.error('DataTransfer error:', error);
                    // Fallback: store file reference and handle in submit
                    uploadArea.droppedFile = file;
                    showFileInfo(file);
                }
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
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Check if we have a file from drag & drop fallback
            if (!fileInput.files.length && !uploadArea.droppedFile) {
                alert('Please select a file first');
                return;
            }
            
            const formData = new FormData();
            
            // Add file (from input or dropped)
            if (fileInput.files.length) {
                formData.append('file', fileInput.files[0]);
            } else if (uploadArea.droppedFile) {
                formData.append('file', uploadArea.droppedFile);
            }
            
            // Add language
            const language = document.getElementById('language').value;
            if (language) {
                formData.append('language', language);
            }
            
            submitBtn.disabled = true;
            progress.style.display = 'block';
            result.style.display = 'none';
            
            try {
                const response = await fetch('/', {
                    method: 'POST',
                    body: formData
                });
                
                progress.style.display = 'none';
                
                // Check if response is PDF or JSON error
                const contentType = response.headers.get('content-type');
                
                if (contentType && contentType.includes('application/pdf')) {
                    // Success - download PDF
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    const fileName = fileInput.files.length ? fileInput.files[0].name : uploadArea.droppedFile.name;
                    a.download = fileName.replace('.zip', '_transcript.pdf');
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    result.style.display = 'block';
                    result.className = 'result success';
                    result.innerHTML = `
                        <div style="font-size: 48px; margin-bottom: 10px;">✅</div>
                        <h2>Success!</h2>
                        <p style="margin: 10px 0;">Your PDF has been downloaded</p>
                    `;
                    
                    // Reset form
                    setTimeout(() => {
                        form.reset();
                        fileInfo.style.display = 'none';
                        result.style.display = 'none';
                        uploadArea.droppedFile = null;
                    }, 3000);
                } else if (contentType && contentType.includes('application/json')) {
                    // JSON response (with download link or error)
                    const data = await response.json();
                    
                    if (data.success && data.filename) {
                        // Auto-download the PDF
                        const downloadUrl = '/download/' + encodeURIComponent(data.filename);
                        const downloadResponse = await fetch(downloadUrl);
                        const blob = await downloadResponse.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = data.filename;
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                        
                        result.style.display = 'block';
                        result.className = 'result success';
                        result.innerHTML = `
                            <div style="font-size: 48px; margin-bottom: 10px;">✅</div>
                            <h2>Success!</h2>
                            <p style="margin: 10px 0;">Your PDF has been downloaded</p>
                        `;
                        
                        // Reset form
                        setTimeout(() => {
                            form.reset();
                            fileInfo.style.display = 'none';
                            result.style.display = 'none';
                            uploadArea.droppedFile = null;
                        }, 3000);
                    } else {
                        // Error response
                        result.style.display = 'block';
                        result.className = 'result error';
                        result.innerHTML = `
                            <div style="font-size: 48px; margin-bottom: 10px;">❌</div>
                            <h2>Error</h2>
                            <p style="margin: 10px 0;">${data.error || 'Unknown error'}</p>
                        `;
                    }
                } else {
                    // Unknown response type
                    result.style.display = 'block';
                    result.className = 'result error';
                    result.innerHTML = `
                        <div style="font-size: 48px; margin-bottom: 10px;">❌</div>
                        <h2>Error</h2>
                        <p style="margin: 10px 0;">Unexpected response format</p>
                    `;
                }
            } catch (error) {
                progress.style.display = 'none';
                result.style.display = 'block';
                result.className = 'result error';
                result.innerHTML = `
                    <div style="font-size: 48px; margin-bottom: 10px;">❌</div>
                    <h2>Error</h2>
                    <p style="margin: 10px 0;">${error.message}</p>
                `;
            } finally {
                submitBtn.disabled = false;
            }
        });
    </script>
</body>
</html>
        """
        
        self.wfile.write(html.encode('utf-8'))
    
    def do_POST(self):
        """Handle file upload"""
        content_type = self.headers['Content-Type']
        
        # Check if content type is available
        if not content_type or 'multipart/form-data' not in content_type:
            self.send_error(400, "Invalid content type")
            return
        
        # Check if this is from WhatsApp share
        is_share = self.path == '/share'
        if is_share:
            print("📱 Received share from WhatsApp!")
        
        # Parse multipart form data
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'}
        )
        
        if 'file' not in form:
            self.send_json_response({'success': False, 'error': 'No file uploaded'})
            return
        
        file_item = form['file']
        if not file_item.filename:
            self.send_json_response({'success': False, 'error': 'No file selected'})
            return
        
        # Get language if specified
        language = form.getvalue('language', '')
        
        # Save uploaded file
        filename = os.path.basename(file_item.filename)
        filepath = os.path.join('uploads', filename)
        
        os.makedirs('uploads', exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(file_item.file.read())
        
        # If this is from WhatsApp share, show processing page
        if is_share:
            self.send_processing_page(filename, language, filepath)
            return
        
        # Process the file immediately for normal uploads
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
    
    def send_processing_page(self, filename, language, filepath):
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
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Custom log format"""
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
    parser = argparse.ArgumentParser(description='WhatsApp Chat to PDF Web Server')
    parser.add_argument('--https', action='store_true', 
                       help='Enable HTTPS via ngrok tunnel (required for PWA share on Android)')
    parser.add_argument('--port', type=int, default=8080,
                       help='Local port (default: 8080)')
    args = parser.parse_args()
    
    port = args.port
    local_ip = get_local_ip()
    
    server = HTTPServer(('0.0.0.0', port), UploadHandler)
    
    print("\n" + "="*70)
    print("📱 WhatsApp Chat to PDF - Web Upload Server")
    print("="*70)
    
    # Start ngrok tunnel if requested
    if args.https:
        try:
            from pyngrok import ngrok
            
            # Start ngrok tunnel
            public_url = ngrok.connect(port, bind_tls=True)
            https_url = public_url.public_url
            
            print(f"\n✅ HTTPS tunnel active!")
            print(f"\n🌐 Public URL (share this with your phone):")
            print(f"\n   {https_url}")
            print(f"\n📱 STEPS TO USE PWA SHARE:")
            print(f"\n   1. Open {https_url} on your phone")
            print(f"   2. Tap 'Install app' or 'Add to Home Screen'")
            print(f"   3. From WhatsApp → Export → Share")
            print(f"   4. Select 'Chat2PDF' from share menu!")
            print(f"\n⚠️  Tunnel will close when you stop the server")
            
        except ImportError:
            print(f"\n❌ ERROR: pyngrok not installed!")
            print(f"\n   Install with: pip install pyngrok")
            print(f"\n   Then run: python3 web_upload.py --https")
            return
        except Exception as e:
            print(f"\n❌ ERROR starting ngrok: {e}")
            print(f"\n   Make sure ngrok is configured:")
            print(f"\n   1. Sign up at https://ngrok.com")
            print(f"   2. Get your auth token")
            print(f"   3. Run: ngrok config add-authtoken YOUR_TOKEN")
            return
    else:
        print(f"\n✅ Server running on local network")
        print(f"\n📱 On your phone (same WiFi):")
        print(f"\n   http://{local_ip}:{port}")
        print(f"\n💻 On this computer:")
        print(f"\n   http://localhost:{port}")
        print(f"\n🔒 Note: Phone and computer must be on same WiFi")
        print(f"\n💡 TIP: For PWA share feature, use --https flag:")
        print(f"\n   python3 web_upload.py --https")
    
    print(f"\nPress Ctrl+C to stop\n")
    print("="*70 + "\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
        if args.https:
            try:
                ngrok.disconnect(public_url.public_url)
                print("🔒 Tunnel closed")
            except:
                pass
        server.shutdown()


if __name__ == '__main__':
    main()
