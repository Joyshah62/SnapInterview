import asyncio
import websockets
import json
import os
import wave
import time

class WebSocketServer:
    def __init__(self, host="0.0.0.0", port=8765, on_connect=None, on_disconnect=None):
        self.host = host
        self.port = port
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.server = None
        self.clients = set()
        self.recording = False
        self.audio_buffer = bytearray()
    
    async def save_audio(self):
        if not self.audio_buffer:
            print("No audio to save")
            return
        
        os.makedirs("recordings", exist_ok=True)
        filename = f"recordings/interview_{int(time.time())}.wav"
        
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)   # PCM16 = 2 bytes
            wf.setframerate(16000)
            wf.writeframes(self.audio_buffer)
        
        print(f"✅ Audio saved to {filename}")
    
    async def handler(self, websocket, path=None):
        self.clients.add(websocket)
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
                        print(f"Recording chunk: {len(message)} bytes")
                
                elif isinstance(message, str):
                    data = json.loads(message)
                    
                    if data["type"] == "start_audio":
                        print("🎙️ Start recording")
                        self.recording = True
                        self.audio_buffer = bytearray()
                    
                    elif data["type"] == "stop_audio":
                        print("🛑 Stop recording")
                        self.recording = False
                        await self.save_audio()
        
        except Exception as e:
            print(f"WebSocket handler error: {type(e).__name__}: {e}")
        
        finally:
            print(">>> Handler exiting, removing client")
            self.clients.discard(websocket)
            if self.on_disconnect:
                self.on_disconnect()
    
    async def start(self):
        if self.server is not None:
            print("Server already running")
            return
        
        self.server = await websockets.serve(self.handler, self.host, self.port)
        print(f"WebSocket server running on {self.host}:{self.port}")
        print(f"Bound sockets: {self.server.sockets}")
    
    async def stop(self):
        if self.server is None:
            return
        
        print("Stopping WebSocket server...")
        self.server.close()
        await self.server.wait_closed()
        self.server = None
        print("WebSocket server stopped")