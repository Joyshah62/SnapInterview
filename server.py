import asyncio
import base64
import websockets
import json
import os
import wave
import time
import socket
from s3_handler import S3Handler
from ssl_generator import get_ssl_context
from resume_parser import parse_and_save
from interview_engine import (
    create_interview_session,
    get_opening,
    generate_question,
    add_response_and_generate,
)
from whisper import transcribe_from_pcm16_bytes, transcribe_pcm16_chunk, merge_transcripts, CHUNK_BYTES, OVERLAP_BYTES

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))  # OS assigns free port
    port = s.getsockname()[1]
    s.close()
    print(port)
    return port

class WebSocketServer:
    def __init__(self, host="0.0.0.0", port=None, on_connect=None, on_disconnect=None):
        self.host = host
        self.port = port
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.server = None
        self.clients = set()
        self.recording = False
        self.audio_buffer = bytearray()
        self.live_transcript_parts = []
        self.current_username = None
        self.s3_handler = S3Handler()
        self.interview_sessions = {}
    
    def set_current_user(self, username: str):
        """Set the current username for organizing S3 uploads"""
        self.current_username = username
        print(f"📂 Current user set to: {username}")
    
    async def save_audio(self):
        """Save audio locally and upload to S3"""
        if not self.audio_buffer:
            print("No audio to save")
            return None
        
        # Save locally first
        os.makedirs("recordings", exist_ok=True)
        timestamp = int(time.time())
        filename = f"interview_{timestamp}.wav"
        local_path = f"recordings/{filename}"
        
        with wave.open(local_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)   # PCM16 = 2 bytes
            wf.setframerate(16000)
            wf.writeframes(self.audio_buffer)
        
        print(f"✅ Audio saved locally: {local_path}")
        
        # Upload to S3 if user is set
        if self.current_username and self.s3_handler.s3_client:
            result = self.s3_handler.upload_audio_recording(
                local_file_path=local_path,
                username=self.current_username
            )
            
            if result['success']:
                print(f"☁️ Audio uploaded to S3: {result['url']}")
                return {
                    'local_path': local_path,
                    's3_url': result['url'],
                    's3_key': result['key'],
                    'filename': result['filename']
                }
            else:
                print(f"❌ S3 upload failed: {result['message']}")
                return {
                    'local_path': local_path,
                    's3_url': None,
                    'error': result['message']
                }
        else:
            print("⚠️ No username set or S3 not configured, skipping cloud upload")
            return {
                'local_path': local_path,
                's3_url': None
            }
    
    async def handler(self, websocket, path=None):
        self.clients.add(websocket)
        session_key = id(websocket)
        print("Client connected:", path)
        
        if self.on_connect:
            self.on_connect()
        
        try:
            message = {
                "type": "server_message",
                "text": "Mobile connected successfully"
            }
            print(">>> About to send message...")
            await websocket.send(json.dumps(message))
            print(">>> Message sent successfully")
            
            async for message in websocket:
                if isinstance(message, bytes):
                    if self.recording:
                        self.audio_buffer.extend(message)
                        while len(self.audio_buffer) >= CHUNK_BYTES:
                            chunk = bytes(self.audio_buffer[:CHUNK_BYTES])
                            del self.audio_buffer[:CHUNK_BYTES - OVERLAP_BYTES]
                            ws = websocket
                            async def process_live_chunk(chunk_bytes=chunk):
                                loop = asyncio.get_event_loop()
                                text = await loop.run_in_executor(None, lambda cb=chunk_bytes: transcribe_pcm16_chunk(cb))
                                if text:
                                    self.live_transcript_parts.append(text)
                                    await ws.send(json.dumps({"type": "candidate_transcript", "text": text}))
                            asyncio.create_task(process_live_chunk())
                
                elif isinstance(message, str):
                    data = json.loads(message)
                    
                    if data["type"] == "start_audio":
                        print("🎙️ Start recording")
                        self.recording = True
                        self.audio_buffer = bytearray()
                        self.live_transcript_parts = []
                    
                    elif data["type"] == "stop_audio":
                        print("🛑 Stop recording")
                        self.recording = False
                        save_result = await self.save_audio()
                        if save_result:
                            response = {
                                "type": "audio_saved",
                                "local_path": save_result.get('local_path'),
                                "s3_url": save_result.get('s3_url'),
                                "success": True
                            }
                            await websocket.send(json.dumps(response))
                            if session_key in self.interview_sessions:
                                remainder_bytes = bytes(self.audio_buffer)
                                output_txt = os.path.join("recordings", f"transcript_{int(time.time())}.txt")
                                loop = asyncio.get_event_loop()
                                live_parts = list(self.live_transcript_parts)
                                def do_transcribe_and_next():
                                    remainder_text = transcribe_pcm16_chunk(remainder_bytes) if remainder_bytes else ""
                                    full_text = ""
                                    for t in live_parts + ([remainder_text] if remainder_text else []):
                                        full_text = merge_transcripts(full_text, t)
                                    with open(output_txt, "w", encoding="utf-8") as f:
                                        f.write(full_text.strip())
                                    if not full_text.strip():
                                        return None, None, remainder_text
                                    next_q = add_response_and_generate(
                                        self.interview_sessions[session_key],
                                        full_text.strip(),
                                    )
                                    return full_text.strip(), next_q, remainder_text
                                try:
                                    transcript, next_question, remainder_text = await loop.run_in_executor(None, do_transcribe_and_next)
                                    if remainder_text:
                                        await websocket.send(json.dumps({
                                            "type": "candidate_transcript",
                                            "text": remainder_text,
                                        }))
                                    if next_question:
                                        await websocket.send(json.dumps({
                                            "type": "interviewer_text",
                                            "text": next_question,
                                        }))
                                except Exception as ex:
                                    print(f"Interview step error: {ex}")
                    
                    elif data["type"] == "document_upload":
                        doc_type = data.get("doc_type", "resume")
                        filename = data.get("filename", "document")
                        content_b64 = data.get("content", "")
                        if not content_b64:
                            await websocket.send(json.dumps({"type": "document_upload_result", "success": False, "error": "missing content"}))
                            continue
                        try:
                            content = base64.b64decode(content_b64)
                            root = os.path.join("documents", "resumes" if doc_type == "resume" else "jds")
                            os.makedirs(root, exist_ok=True)
                            name_root, ext = os.path.splitext(filename)
                            if ext.lower() not in (".pdf", ".docx"):
                                ext = ".pdf"
                            base_name = "".join(c for c in name_root if c.isalnum() or c in "._- ") or "document"
                            safe_name = f"{base_name}{ext}"
                            ts = int(time.time())
                            local_path = os.path.join(root, f"{ts}_{safe_name}")
                            with open(local_path, "wb") as f:
                                f.write(content)
                            print(f"✅ Document saved: {local_path}")
                            if doc_type == "resume":
                                try:
                                    script_dir = os.path.dirname(os.path.abspath(__file__))
                                    resume_md = os.path.join(script_dir, "resume_text.md")
                                    parse_and_save(local_path, resume_md)
                                    print(f"✅ Resume parsed to resume_text.md")
                                except Exception as parse_err:
                                    print(f"Resume parse error: {parse_err}")
                            s3_url = None
                            if self.current_username and self.s3_handler.s3_client:
                                s3_result = self.s3_handler.upload_document(
                                    local_file_path=local_path,
                                    username=self.current_username,
                                    doc_type=doc_type,
                                    timestamp=ts,
                                )
                                if s3_result["success"]:
                                    s3_url = s3_result["url"]
                                    print(f"☁️ Document uploaded to S3: {s3_url}")
                                else:
                                    print(f"❌ S3 document upload failed: {s3_result['message']}")
                            await websocket.send(json.dumps({
                                "type": "document_upload_result",
                                "success": True,
                                "local_path": local_path,
                                "s3_url": s3_url,
                            }))
                        except Exception as doc_err:
                            print(f"Document save error: {doc_err}")
                            await websocket.send(json.dumps({"type": "document_upload_result", "success": False, "error": str(doc_err)}))
                    elif data["type"] == "interview_setup":
                        role = data.get("role", "Software Engineer")
                        difficulty = str(data.get("difficulty", "Medium")).upper()
                        if difficulty not in ("EASY", "MEDIUM", "HARD"):
                            difficulty = "MEDIUM"
                        try:
                            session = create_interview_session(role, difficulty)
                            self.interview_sessions[session_key] = session
                            opening = get_opening(role)
                            await websocket.send(json.dumps({
                                "type": "interviewer_text",
                                "text": opening,
                            }))
                        except Exception as ex:
                            print(f"Interview start error: {ex}")
                            await websocket.send(json.dumps({"type": "interviewer_text", "text": "Hi, could you briefly introduce yourself?"}))
                    elif data["type"] == "end_interview":
                        self.interview_sessions.pop(session_key, None)
        
        except Exception as e:
            print(f"WebSocket handler error: {type(e).__name__}: {e}")
        
        finally:
            print(">>> Handler exiting, removing client")
            self.interview_sessions.pop(session_key, None)
            self.clients.discard(websocket)
            if self.on_disconnect:
                self.on_disconnect()
    
    async def start(self):
        if self.server is not None:
            print("Server already running")
            return

        # Pick random free port if not set
        if self.port is None:
            self.port = get_free_port()

        ssl_context = get_ssl_context()
        self.server = await websockets.serve(
            self.handler,
            self.host,
            self.port,
            ssl=ssl_context,
        )

        print(f"Secure WebSocket server running on wss://{self.host}:{self.port}")

    
    async def stop(self):
        if self.server is None:
            return

        print("Stopping WebSocket server...")
        self.server.close()
        await self.server.wait_closed()

        self.server = None
        self.port = None   # 🔥 Reset so next start gets new port

        print("WebSocket server stopped")
