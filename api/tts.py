import os
import json
import shutil
from http.server import BaseHTTPRequestHandler
from gradio_client import Client

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            text = data.get('text', '')
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

            # เชื่อมต่อ Client กับ Private Space
            try:
                client = Client("innkl24/shan-tts-api", token=hf_token)
            except TypeError:
                client = Client("innkl24/shan-tts-api", hf_token=hf_token)

            # ใช้ fn_index=0 เพื่อเรียกฟังก์ชันแรกสุดของ Space เสมอ (หมดปัญหาเรื่อง api_name)
            result = client.predict(
                text,
                speed,
                fn_index=0
            )

            # ดึง path ของไฟล์เสียง
            audio_path = None
            if isinstance(result, str):
                audio_path = result
            elif isinstance(result, (list, tuple)) and len(result) > 0:
                audio_path = result[0]
            elif isinstance(result, dict) and 'name' in result:
                audio_path = result['name']

            if not audio_path or not os.path.exists(audio_path):
                raise Exception(f"Audio file was not generated properly. Result: {result}")

            # อ่านไฟล์เสียงส่งกลับหน้าเว็บ
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
