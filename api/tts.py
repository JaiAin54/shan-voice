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

            # 1. เชื่อมต่อ Client
            try:
                client = Client("innkl24/shan-tts-api", token=hf_token)
            except TypeError:
                client = Client("innkl24/shan-tts-api", hf_token=hf_token)

            # 2. ดึงชื่อ Named Endpoint อัตโนมัติจาก Space
            api_info = client.view_api(return_format="dict")
            named_endpoints = api_info.get("named_endpoints", {})

            # 3. ยิงคำสั่ง predict เข้า endpoint ที่พบ
            result = None
            if named_endpoints:
                # เลือก endpoint ตัวแรกที่มีใน Space อัตโนมัติ (เช่น '/predict' หรือ '/generate_shan_audio')
                endpoint_name = list(named_endpoints.keys())[0]
                result = client.predict(text=text, speed=speed, api_name=endpoint_name)
            else:
                # กรณีไม่มีชื่อ endpoint ให้ส่งตามลำดับพารามิเตอร์
                result = client.predict(text, speed)

            # 4. ดึง path ของไฟล์เสียงที่สร้างเสร็จ
            audio_path = None
            if isinstance(result, str):
                audio_path = result
            elif isinstance(result, (list, tuple)) and len(result) > 0:
                audio_path = result[0]
            elif isinstance(result, dict) and 'name' in result:
                audio_path = result['name']

            if not audio_path or not os.path.exists(audio_path):
                raise Exception(f"ไม่พบไฟล์เสียงที่สร้าง Result: {result}")

            # 5. ส่งไฟล์เสียงกลับไปที่หน้าบ้าน
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
