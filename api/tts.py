import os
import json
from http.server import BaseHTTPRequestHandler
from gradio_client import Client

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            text = data.get('text', '')
            # แปลง speed ให้เป็น float เสมอ
            try:
                speed = float(data.get('speed', 1.0))
            except (ValueError, TypeError):
                speed = 1.0
            
            hf_token = os.environ.get('HF_TOKEN')
            if not hf_token:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "HF_TOKEN not configured on server"}).encode('utf-8'))
                return

            # รองรับทั้งเวอร์ชันใหม่ (token) และเก่า (hf_token) แบบกันเหนียว 100%
            try:
                client = Client("innkl24/shan-tts-api", token=hf_token)
            except TypeError:
                client = Client("innkl24/shan-tts-api", hf_token=hf_token)

            # จุดสำคัญ: gr.Interface จะใช้ api_name="/predict"
            result = client.predict(
                text=text, 
                speed=speed, 
                api_name="/predict"
            )
            
            # ดึง path ของไฟล์เสียงที่สร้างเสร็จ
            audio_path = result if isinstance(result, str) else result[0]
            
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()

            self.send_response(200)
            self.send_header('Content-Type', 'audio/wav')
            self.send_header('Content-Length', str(len(audio_bytes)))
            self.end_headers()
            self.wfile.write(audio_bytes)
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
