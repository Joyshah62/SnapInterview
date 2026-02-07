# import asyncio
# import base64
# import websockets
# import json
# import os
# import wave
# import time
# import socket
# from datetime import datetime
# from pathlib import Path

# from s3_handler import S3Handler
# from start_evaluation import run_evaluation
# from ssl_generator import get_ssl_context
# from resume_parser import parse_and_save
# from interview_engine import (
#     create_interview_session,
#     get_opening,
#     get_closing,
#     generate_question,
#     add_response_and_generate,
#     record_qa,
# )

# # ✅ IMPORTANT: use STEP_BYTES (correct buffer advance)
# from whisper_stt import (
#     # transcribe_from_pcm16_bytes,
#     transcribe_pcm16_chunk,
#     merge_transcripts,
#     CHUNK_BYTES,
#     STEP_BYTES,
# )

# from text_to_speech import (
#     synthesize_opening_mp3,
#     synthesize_question_mp3,
#     synthesize_closing_mp3,
# )


# def get_free_port():
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     s.bind(("", 0))
#     port = s.getsockname()[1]
#     s.close()
#     print(port)
#     return port


# async def _run_evaluation_and_send(websocket, local_log_path: str):
#     loop = asyncio.get_event_loop()
#     try:
#         result = await loop.run_in_executor(None, lambda: run_evaluation(Path(local_log_path)))
#         payload = {"type": "evaluation_result", "success": True, "result": result}
#     except Exception as e:
#         print(f"❌ Evaluation failed: {e}")
#         payload = {"type": "evaluation_result", "success": False, "error": str(e)}
#     try:
#         await websocket.send(json.dumps(payload))
#     except Exception:
#         pass


# class WebSocketServer:
#     def __init__(self, host="0.0.0.0", port=None, on_connect=None, on_disconnect=None):
#         self.host = host
#         self.port = port
#         self.on_connect = on_connect
#         self.on_disconnect = on_disconnect
#         self.server = None
#         self.clients = set()

#         self.recording = False
#         self.audio_buffer = bytearray()

#         # ✅ Keep ONE live transcript (merged), do NOT keep parts
#         self.live_transcript = ""

#         # ✅ Ensure chunk merges happen in order (prevents race duplicates)
#         self.transcribe_lock = asyncio.Lock()

#         self.current_username = None
#         self.s3_handler = S3Handler()
#         self.interview_sessions = {}

#     def set_current_user(self, username: str):
#         self.current_username = username
#         print(f"📂 Current user set to: {username}")

#     async def save_audio(self):
#         if not self.audio_buffer:
#             print("No audio to save")
#             return None

#         os.makedirs("recordings", exist_ok=True)
#         timestamp = int(time.time())
#         filename = f"interview_{timestamp}.wav"
#         local_path = f"recordings/{filename}"

#         with wave.open(local_path, "wb") as wf:
#             wf.setnchannels(1)
#             wf.setsampwidth(2)
#             wf.setframerate(16000)
#             wf.writeframes(self.audio_buffer)

#         print(f"✅ Audio saved locally: {local_path}")

#         if self.current_username and self.s3_handler.s3_client:
#             result = self.s3_handler.upload_audio_recording(
#                 local_file_path=local_path,
#                 username=self.current_username
#             )

#             if result["success"]:
#                 print(f"☁️ Audio uploaded to S3: {result['url']}")
#                 return {
#                     "local_path": local_path,
#                     "s3_url": result["url"],
#                     "s3_key": result["key"],
#                     "filename": result["filename"]
#                 }
#             else:
#                 print(f"❌ S3 upload failed: {result['message']}")
#                 return {"local_path": local_path, "s3_url": None, "error": result["message"]}
#         else:
#             print("⚠️ No username set or S3 not configured, skipping cloud upload")
#             return {"local_path": local_path, "s3_url": None}

#     async def handler(self, websocket, path=None):
#         self.clients.add(websocket)
#         session_key = id(websocket)
#         print("Client connected:", path)

#         if self.on_connect:
#             self.on_connect()

#         try:
#             await websocket.send(json.dumps({"type": "server_message", "text": "Mobile connected successfully"}))

#             async for message in websocket:
#                 # ==========================
#                 # AUDIO BYTES (PCM16)
#                 # ==========================
#                 if isinstance(message, bytes):
#                     if not self.recording:
#                         continue

#                     self.audio_buffer.extend(message)
#                     print(f"🎤 Received audio chunk: {len(message)} bytes (buffer size: {len(self.audio_buffer)} bytes)")

#                     # Process as many CHUNK_BYTES as possible
#                     while len(self.audio_buffer) >= CHUNK_BYTES:
#                         chunk = bytes(self.audio_buffer[:CHUNK_BYTES])

#                         # ✅ Correct: advance by STEP_BYTES (not 0.5 sec forever)
#                         del self.audio_buffer[:STEP_BYTES]

#                         print(f"📦 Processing audio chunk for transcription: {len(chunk)} bytes")

#                         ws = websocket

#                         async def process_live_chunk(chunk_bytes=chunk):
#                             # ✅ prevent race / out-of-order merges
#                             async with self.transcribe_lock:
#                                 loop = asyncio.get_event_loop()
#                                 text = await loop.run_in_executor(
#                                     None, lambda cb=chunk_bytes: transcribe_pcm16_chunk(cb)
#                                 )
#                                 if text:
#                                     print(f"📝 Converted text: {text!r}")

#                                     # ✅ merge into one running transcript
#                                     self.live_transcript = merge_transcripts(self.live_transcript, text)

#                                     # ✅ send merged transcript (client should overwrite)
#                                     await ws.send(json.dumps({
#                                         "type": "candidate_transcript",
#                                         "text": self.live_transcript
#                                     }))

#                         asyncio.create_task(process_live_chunk())

#                 # ==========================
#                 # CONTROL MESSAGES (JSON)
#                 # ==========================
#                 elif isinstance(message, str):
#                     data = json.loads(message)

#                     # ---------- START AUDIO ----------
#                     if data["type"] == "start_audio":
#                         print("🎙️ Start recording")
#                         self.recording = True
#                         self.audio_buffer = bytearray()
#                         self.live_transcript = ""

#                     # ---------- STOP AUDIO ----------
#                     elif data["type"] == "stop_audio":
#                         print("🛑 Stop recording")
#                         self.recording = False

#                         save_result = await self.save_audio()
#                         if save_result:
#                             await websocket.send(json.dumps({
#                                 "type": "audio_saved",
#                                 "local_path": save_result.get("local_path"),
#                                 "s3_url": save_result.get("s3_url"),
#                                 "success": True
#                             }))

#                         if session_key in self.interview_sessions:
#                             remainder_bytes = bytes(self.audio_buffer)
#                             output_txt = os.path.join("recordings", f"transcript_{int(time.time())}.txt")
#                             loop = asyncio.get_event_loop()

#                             def do_transcribe_and_next():
#                                 remainder_text = transcribe_pcm16_chunk(remainder_bytes) if remainder_bytes else ""
#                                 if remainder_text:
#                                     print(f"📝 Converted text (remainder): {remainder_text!r}")

#                                 # ✅ merge: live_transcript + remainder_text
#                                 full_text = self.live_transcript
#                                 if remainder_text:
#                                     full_text = merge_transcripts(full_text, remainder_text)

#                                 with open(output_txt, "w", encoding="utf-8") as f:
#                                     f.write(full_text.strip())

#                                 if not full_text.strip():
#                                     return None, None, full_text.strip()

#                                 sess = self.interview_sessions[session_key]
#                                 record_qa(sess, sess["current_question"], full_text.strip())
#                                 next_q = add_response_and_generate(sess, full_text.strip())
#                                 return full_text.strip(), next_q, full_text.strip()

#                             try:
#                                 transcript, next_question, merged_text = await loop.run_in_executor(None, do_transcribe_and_next)

#                                 # ✅ Send ONE merged transcript (overwrite client)
#                                 if merged_text:
#                                     await websocket.send(json.dumps({
#                                         "type": "candidate_transcript",
#                                         "text": merged_text,
#                                     }))

#                                 if next_question:
#                                     print(f"📥 Data fetched from LLM: {next_question!r}")
#                                     self.interview_sessions[session_key]["current_question"] = next_question

#                                     await websocket.send(json.dumps({
#                                         "type": "interviewer_text",
#                                         "text": next_question,
#                                     }))

#                                     # TTS (mobile plays)
#                                     try:
#                                         mp3_bytes = await loop.run_in_executor(None, lambda t=next_question: synthesize_question_mp3(t))
#                                         await websocket.send(json.dumps({
#                                             "type": "interviewer_audio",
#                                             "audio_base64": base64.b64encode(mp3_bytes).decode("ascii"),
#                                             "text": next_question,
#                                         }))
#                                         print("✅ Sent interviewer_audio for LLM question")
#                                     except Exception as tts_ex:
#                                         print(f"❌ TTS for follow-up question failed: {tts_ex}")

#                                 else:
#                                     # Max questions reached
#                                     closing_text = get_closing()
#                                     await websocket.send(json.dumps({"type": "interviewer_text", "text": closing_text}))

#                                     try:
#                                         mp3_bytes = await loop.run_in_executor(None, lambda: synthesize_closing_mp3(closing_text))
#                                         await websocket.send(json.dumps({
#                                             "type": "interviewer_audio",
#                                             "audio_base64": base64.b64encode(mp3_bytes).decode("ascii"),
#                                             "text": closing_text,
#                                         }))
#                                         print("✅ Sent closing message (TTS)")
#                                     except Exception as tts_ex:
#                                         print(f"❌ TTS for closing failed: {tts_ex}")

#                                     # Save logs
#                                     sess = self.interview_sessions.get(session_key)
#                                     local_log_path = None
#                                     if sess and "conversation_log" in sess:
#                                         sess["conversation_log"]["metadata"]["ended_at"] = datetime.now().isoformat()
#                                         os.makedirs("logs", exist_ok=True)
#                                         log_filename = f"interview_log_{sess['session_id']}.json"
#                                         local_log_path = os.path.join("logs", log_filename)
#                                         with open(local_log_path, "w", encoding="utf-8") as f:
#                                             json.dump(sess["conversation_log"], f, indent=2)
#                                         print(f"💾 Interview log saved locally: {local_log_path}")

#                                         if self.current_username and self.s3_handler.s3_client:
#                                             log_result = self.s3_handler.upload_log_file(
#                                                 local_file_path=local_log_path,
#                                                 username=self.current_username,
#                                                 session_id=sess["session_id"],
#                                             )
#                                             if log_result["success"]:
#                                                 print(f"☁️ Interview log uploaded to S3: {log_result['url']}")
#                                             else:
#                                                 print(f"❌ S3 log upload failed: {log_result['message']}")
#                                         else:
#                                             print("⚠️ No username or S3 config, skipping log upload")

#                                     await websocket.send(json.dumps({"type": "interview_complete"}))
#                                     print("✅ Interview complete (max questions reached)")

#                                     if local_log_path:
#                                         asyncio.create_task(_run_evaluation_and_send(websocket, local_log_path))

#                             except Exception as ex:
#                                 print(f"Interview step error: {ex}")

#                         # reset per turn (important)
#                         self.audio_buffer = bytearray()
#                         self.live_transcript = ""

#                     # ---------- DOCUMENT UPLOAD ----------
#                     elif data["type"] == "document_upload":
#                         doc_type = data.get("doc_type", "resume")
#                         filename = data.get("filename", "document")
#                         content_b64 = data.get("content", "")
#                         if not content_b64:
#                             await websocket.send(json.dumps({"type": "document_upload_result", "success": False, "error": "missing content"}))
#                             continue
#                         try:
#                             content = base64.b64decode(content_b64)
#                             root = os.path.join("documents", "resumes" if doc_type == "resume" else "jds")
#                             os.makedirs(root, exist_ok=True)
#                             name_root, ext = os.path.splitext(filename)
#                             if ext.lower() not in (".pdf", ".docx"):
#                                 ext = ".pdf"
#                             base_name = "".join(c for c in name_root if c.isalnum() or c in "._- ") or "document"
#                             safe_name = f"{base_name}{ext}"
#                             ts = int(time.time())
#                             local_path = os.path.join(root, f"{ts}_{safe_name}")
#                             with open(local_path, "wb") as f:
#                                 f.write(content)
#                             print(f"✅ Document saved: {local_path}")

#                             if doc_type == "resume":
#                                 try:
#                                     script_dir = os.path.dirname(os.path.abspath(__file__))
#                                     resume_md = os.path.join(script_dir, "resume_text.md")
#                                     parse_and_save(local_path, resume_md)
#                                     print("✅ Resume parsed to resume_text.md")
#                                 except Exception as parse_err:
#                                     print(f"Resume parse error: {parse_err}")

#                             s3_url = None
#                             if self.current_username and self.s3_handler.s3_client:
#                                 s3_result = self.s3_handler.upload_document(
#                                     local_file_path=local_path,
#                                     username=self.current_username,
#                                     doc_type=doc_type,
#                                     timestamp=ts,
#                                 )
#                                 if s3_result["success"]:
#                                     s3_url = s3_result["url"]
#                                     print(f"☁️ Document uploaded to S3: {s3_url}")
#                                 else:
#                                     print(f"❌ S3 document upload failed: {s3_result['message']}")

#                             await websocket.send(json.dumps({
#                                 "type": "document_upload_result",
#                                 "success": True,
#                                 "local_path": local_path,
#                                 "s3_url": s3_url,
#                             }))
#                         except Exception as doc_err:
#                             print(f"Document save error: {doc_err}")
#                             await websocket.send(json.dumps({"type": "document_upload_result", "success": False, "error": str(doc_err)}))

#                     # ---------- INTERVIEW SETUP ----------
#                     elif data["type"] == "interview_setup":
#                         role = data.get("role", "Software Engineer")
#                         difficulty = str(data.get("difficulty", "Medium")).upper()
#                         if difficulty not in ("EASY", "MEDIUM", "HARD"):
#                             difficulty = "MEDIUM"
#                         try:
#                             session = create_interview_session(role, difficulty)
#                             self.interview_sessions[session_key] = session

#                             opening = get_opening(role)
#                             session["current_question"] = opening

#                             await websocket.send(json.dumps({"type": "interviewer_text", "text": opening}))

#                             loop = asyncio.get_event_loop()
#                             mp3_bytes = await loop.run_in_executor(None, lambda: synthesize_opening_mp3(opening))
#                             await websocket.send(json.dumps({
#                                 "type": "interviewer_audio",
#                                 "audio_base64": base64.b64encode(mp3_bytes).decode("ascii"),
#                                 "text": opening,
#                             }))
#                         except Exception as ex:
#                             print(f"Interview start error: {ex}")
#                             await websocket.send(json.dumps({"type": "interviewer_text", "text": "Hi, could you briefly introduce yourself?"}))

#                     elif data["type"] == "end_interview":
#                         self.interview_sessions.pop(session_key, None)

#         except Exception as e:
#             print(f"WebSocket handler error: {type(e).__name__}: {e}")

#         finally:
#             print(">>> Handler exiting, removing client")
#             self.interview_sessions.pop(session_key, None)
#             self.clients.discard(websocket)
#             if self.on_disconnect:
#                 self.on_disconnect()

#     async def start(self):
#         if self.server is not None:
#             print("Server already running")
#             return

#         if self.port is None:
#             self.port = get_free_port()

#         ssl_context = get_ssl_context()
#         self.server = await websockets.serve(
#             self.handler,
#             self.host,
#             self.port,
#             ssl=ssl_context,
#             ping_interval=30,
#             ping_timeout=None,
#         )

#         print(f"Secure WebSocket server running on wss://{self.host}:{self.port}")

#     async def stop(self):
#         if self.server is None:
#             return

#         print("Stopping WebSocket server...")
#         self.server.close()
#         await self.server.wait_closed()

#         self.server = None
#         self.port = None

#         print("WebSocket server stopped")
import asyncio
import base64
import json
import os
import re
import socket
import time
import wave
import websockets
from datetime import datetime
from pathlib import Path

from s3_handler import S3Handler
from start_evaluation import run_evaluation, EVALUATIONS_DIR
from ssl_generator import get_ssl_context
from resume_parser import parse_and_save
from interview_engine import (
    create_interview_session,
    get_opening,
    get_closing,
    generate_question,
    add_response_and_generate,
    record_qa,
)

# Import streaming ASR helpers from whisper_stt
from whisper_stt import (
    transcribe_pcm16_chunk,
    merge_transcripts,
    CHUNK_BYTES,
    STEP_BYTES,
)

from text_to_speech import (
    synthesize_opening_mp3,
    synthesize_question_mp3,
    synthesize_closing_mp3,
)


def get_free_port():
    """Find a free port on the host system."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port


async def _run_evaluation_and_send(websocket, local_log_path: str, server=None):
    """Run evaluation, send result to client, and upload evaluation JSON to S3."""
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, lambda: run_evaluation(Path(local_log_path)))
        payload = {"type": "evaluation_result", "success": True, "result": result}
        # Upload evaluation to S3 so dashboard Summary can fetch it
        if server and getattr(server, "current_username", None) and getattr(server, "s3_handler", None) and server.s3_handler.s3_client:
            stem = Path(local_log_path).stem  # e.g. interview_log_20260207_082736
            session_id = stem.replace("interview_log_", "", 1) if stem.startswith("interview_log_") else stem
            eval_path = EVALUATIONS_DIR / f"{stem}.evaluation.json"
            if eval_path.exists():
                up = server.s3_handler.upload_evaluation_file(str(eval_path), server.current_username, session_id)
                if up.get("success"):
                    print(f"☁️ Evaluation uploaded to S3: {up.get('key', '')}")
                else:
                    print(f"❌ S3 evaluation upload failed: {up.get('message', '')}")
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        payload = {"type": "evaluation_result", "success": False, "error": str(e)}
    try:
        await websocket.send(json.dumps(payload))
    except Exception:
        pass


class WebSocketServer:
    """Asynchronous secure WebSocket server for SnapInterview."""
    def __init__(self, host="0.0.0.0", port=None, on_connect=None, on_disconnect=None):
        self.host = host
        self.port = port
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.server = None
        self.clients = set()

        # audio streaming state
        self.recording = False
        self.audio_buffer = bytearray()

        # running transcript across chunks
        self.live_transcript = ""

        # lock to ensure transcript merges happen in order
        self.transcribe_lock = asyncio.Lock()

        self.current_username = None
        self.s3_handler = S3Handler()
        self.interview_sessions = {}

    def set_current_user(self, username: str):
        """Set the username for S3 uploads and logs."""
        self.current_username = username
        print(f"📂 Current user set to: {username}")

    async def save_audio(self):
        """Save the entire audio buffer as a WAV file and upload to S3 if configured."""
        if not self.audio_buffer:
            print("No audio to save")
            return None

        os.makedirs("recordings", exist_ok=True)
        timestamp = int(time.time())
        filename = f"interview_{timestamp}.wav"
        local_path = f"recordings/{filename}"

        with wave.open(local_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(self.audio_buffer)

        print(f"✅ Audio saved locally: {local_path}")

        if self.current_username and self.s3_handler.s3_client:
            result = self.s3_handler.upload_audio_recording(
                local_file_path=local_path,
                username=self.current_username
            )

            if result["success"]:
                print(f"☁️ Audio uploaded to S3: {result['url']}")
                return {
                    "local_path": local_path,
                    "s3_url": result["url"],
                    "s3_key": result["key"],
                    "filename": result["filename"]
                }
            else:
                print(f"❌ S3 upload failed: {result['message']}")
                return {"local_path": local_path, "s3_url": None, "error": result["message"]}
        else:
            print("⚠️ No username set or S3 not configured, skipping cloud upload")
            return {"local_path": local_path, "s3_url": None}

    async def handler(self, websocket, path=None):
        """Handle an individual WebSocket connection."""
        self.clients.add(websocket)
        session_key = id(websocket)
        print("Client connected:", path)

        if self.on_connect:
            self.on_connect()

        try:
            # notify client of successful connection
            await websocket.send(json.dumps({"type": "server_message", "text": "Mobile connected successfully"}))

            async for message in websocket:
                # ------------------- AUDIO BYTES (PCM16) -------------------
                if isinstance(message, bytes):
                    # ignore audio if we're not in recording mode
                    if not self.recording:
                        continue

                    # accumulate raw PCM16 audio bytes
                    self.audio_buffer.extend(message)
                    print(f"🎤 Received audio chunk: {len(message)} bytes (buffer size: {len(self.audio_buffer)} bytes)")

                    # process complete chunks sequentially
                    while len(self.audio_buffer) >= CHUNK_BYTES:
                        # copy out a fixed-size window (4 seconds)
                        chunk = bytes(self.audio_buffer[:CHUNK_BYTES])
                        # advance the buffer by step size (3.5 seconds) to allow 0.5 s overlap
                        del self.audio_buffer[:STEP_BYTES]

                        print(f"📦 Processing audio chunk for transcription: {len(chunk)} bytes")

                        # process the chunk synchronously to avoid scheduling many tasks
                        async with self.transcribe_lock:
                            loop = asyncio.get_event_loop()
                            # run Whisper ASR in executor to avoid blocking the event loop
                            text = await loop.run_in_executor(
                                None, lambda cb=chunk: transcribe_pcm16_chunk(cb)
                            )
                            if text:
                                print(f"📝 Converted text: {text!r}")
                                # merge with running transcript
                                self.live_transcript = merge_transcripts(self.live_transcript, text)
                                # send the updated transcript to the client
                                await websocket.send(json.dumps({
                                    "type": "candidate_transcript",
                                    "text": self.live_transcript
                                }))

                # ------------------- CONTROL MESSAGES (JSON) -------------------
                elif isinstance(message, str):
                    data = json.loads(message)

                    # ---- START AUDIO ----
                    if data.get("type") == "start_audio":
                        print("🎙️ Start recording")
                        self.recording = True
                        self.audio_buffer = bytearray()
                        self.live_transcript = ""

                    # ---- STOP AUDIO ----
                    elif data.get("type") == "stop_audio":
                        print("🛑 Stop recording")
                        self.recording = False

                        # save full audio recording
                        save_result = await self.save_audio()
                        if save_result:
                            await websocket.send(json.dumps({
                                "type": "audio_saved",
                                "local_path": save_result.get("local_path"),
                                "s3_url": save_result.get("s3_url"),
                                "success": True
                            }))

                        # if we're in an interview session, transcribe the remainder and generate next question
                        if session_key in self.interview_sessions:
                            remainder_bytes = bytes(self.audio_buffer)
                            output_txt = os.path.join("recordings", f"transcript_{int(time.time())}.txt")
                            loop = asyncio.get_event_loop()

                            def do_transcribe_and_next():
                                # transcribe any leftover audio
                                remainder_text = transcribe_pcm16_chunk(remainder_bytes) if remainder_bytes else ""
                                if remainder_text:
                                    print(f"📝 Converted text (remainder): {remainder_text!r}")

                                # merge remainder with existing transcript
                                full_text = self.live_transcript
                                if remainder_text:
                                    full_text = merge_transcripts(full_text, remainder_text)

                                # save transcript to file
                                with open(output_txt, "w", encoding="utf-8") as f:
                                    f.write(full_text.strip())

                                if not full_text.strip():
                                    return None, None, full_text.strip()

                                # update interview session
                                sess = self.interview_sessions[session_key]
                                record_qa(sess, sess["current_question"], full_text.strip())
                                next_q = add_response_and_generate(sess, full_text.strip())
                                return full_text.strip(), next_q, full_text.strip()

                            try:
                                transcript, next_question, merged_text = await loop.run_in_executor(None, do_transcribe_and_next)

                                # send final merged transcript to client
                                if merged_text:
                                    await websocket.send(json.dumps({
                                        "type": "candidate_transcript",
                                        "text": merged_text,
                                    }))

                                if next_question:
                                    print(f"📥 Data fetched from LLM: {next_question!r}")
                                    self.interview_sessions[session_key]["current_question"] = next_question

                                    await websocket.send(json.dumps({
                                        "type": "interviewer_text",
                                        "text": next_question,
                                    }))

                                    # synthesize question audio
                                    try:
                                        mp3_bytes = await loop.run_in_executor(None, lambda t=next_question: synthesize_question_mp3(t))
                                        await websocket.send(json.dumps({
                                            "type": "interviewer_audio",
                                            "audio_base64": base64.b64encode(mp3_bytes).decode("ascii"),
                                            "text": next_question,
                                        }))
                                        print("✅ Sent interviewer_audio for LLM question")
                                    except Exception as tts_ex:
                                        print(f"❌ TTS for follow-up question failed: {tts_ex}")

                                else:
                                    # no next question: send closing message
                                    closing_text = get_closing()
                                    await websocket.send(json.dumps({"type": "interviewer_text", "text": closing_text}))

                                    try:
                                        mp3_bytes = await loop.run_in_executor(None, lambda: synthesize_closing_mp3(closing_text))
                                        await websocket.send(json.dumps({
                                            "type": "interviewer_audio",
                                            "audio_base64": base64.b64encode(mp3_bytes).decode("ascii"),
                                            "text": closing_text,
                                        }))
                                        print("✅ Sent closing message (TTS)")
                                    except Exception as tts_ex:
                                        print(f"❌ TTS for closing failed: {tts_ex}")

                                    # save conversation log to file and S3
                                    sess = self.interview_sessions.get(session_key)
                                    local_log_path = None
                                    if sess and "conversation_log" in sess:
                                        sess["conversation_log"]["metadata"]["ended_at"] = datetime.now().isoformat()
                                        os.makedirs("logs", exist_ok=True)
                                        log_filename = f"interview_log_{sess['session_id']}.json"
                                        local_log_path = os.path.join("logs", log_filename)
                                        with open(local_log_path, "w", encoding="utf-8") as f:
                                            json.dump(sess["conversation_log"], f, indent=2)
                                        print(f"💾 Interview log saved locally: {local_log_path}")

                                        if self.current_username and self.s3_handler.s3_client:
                                            log_result = self.s3_handler.upload_log_file(
                                                local_file_path=local_log_path,
                                                username=self.current_username,
                                                session_id=sess["session_id"],
                                            )
                                            if log_result["success"]:
                                                print(f"☁️ Interview log uploaded to S3: {log_result['url']}")
                                            else:
                                                print(f"❌ S3 log upload failed: {log_result['message']}")
                                        else:
                                            print("⚠️ No username or S3 config, skipping log upload")

                                    # notify client that interview is complete
                                    await websocket.send(json.dumps({"type": "interview_complete"}))
                                    print("✅ Interview complete (max questions reached)")

                                    # start evaluation in background
                                    if local_log_path:
                                        asyncio.create_task(_run_evaluation_and_send(websocket, local_log_path, server=self))

                            except Exception as ex:
                                print(f"Interview step error: {ex}")

                        # reset audio state for next turn
                        self.audio_buffer = bytearray()
                        self.live_transcript = ""

                    # ---- DOCUMENT UPLOAD ----
                    elif data.get("type") == "document_upload":
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
                                    print("✅ Resume parsed to resume_text.md")
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

                    # ---- INTERVIEW SETUP ----
                    elif data.get("type") == "interview_setup":
                        role = data.get("role", "Software Engineer")
                        difficulty = str(data.get("difficulty", "Medium")).upper()
                        if difficulty not in ("EASY", "MEDIUM", "HARD"):
                            difficulty = "MEDIUM"
                        try:
                            session = create_interview_session(role, difficulty)
                            self.interview_sessions[session_key] = session

                            opening = get_opening(role)
                            session["current_question"] = opening

                            # send initial question text
                            await websocket.send(json.dumps({"type": "interviewer_text", "text": opening}))

                            # synthesize audio for the opening question
                            loop = asyncio.get_event_loop()
                            mp3_bytes = await loop.run_in_executor(None, lambda: synthesize_opening_mp3(opening))
                            await websocket.send(json.dumps({
                                "type": "interviewer_audio",
                                "audio_base64": base64.b64encode(mp3_bytes).decode("ascii"),
                                "text": opening,
                            }))
                        except Exception as ex:
                            print(f"Interview start error: {ex}")
                            err_str = str(ex).lower()
                            if "quota" in err_str or "credits" in err_str or "401" in err_str:
                                msg = (
                                    "Voice service quota exceeded. The interview needs more ElevenLabs credits than you have. "
                                    "Add credits in your ElevenLabs account or try again later."
                                )
                                if "remaining" in err_str and "required" in err_str:
                                    try:
                                        m = re.search(r"(\d+)\s*credits?\s*remaining", err_str, re.I)
                                        n = re.search(r"(\d+)\s*credits?\s*(?:are\s+)?required", err_str, re.I)
                                        if m and n:
                                            msg = (
                                                f"Voice quota exceeded: you have {m.group(1)} credits remaining, "
                                                f"but this request needs {n.group(1)}. Add credits at ElevenLabs or try again later."
                                            )
                                    except Exception:
                                        pass
                            else:
                                msg = "Could not start the interview. Please check your connection and try again."
                            await websocket.send(json.dumps({
                                "type": "interview_error",
                                "error": msg,
                                "quota_exceeded": "quota" in err_str or "credits" in err_str,
                            }))

                    # ---- END INTERVIEW ----
                    elif data.get("type") == "end_interview":
                        self.interview_sessions.pop(session_key, None)

        except Exception as e:
            # handle unexpected errors
            print(f"WebSocket handler error: {type(e).__name__}: {e}")

        finally:
            # clean up when client disconnects
            print(">>> Handler exiting, removing client")
            self.interview_sessions.pop(session_key, None)
            self.clients.discard(websocket)
            if self.on_disconnect:
                self.on_disconnect()

    async def start(self):
        """Start the WebSocket server on the configured host and port."""
        if self.server is not None:
            print("Server already running")
            return

        # assign a free port if none provided
        if self.port is None:
            self.port = get_free_port()

        ssl_context = get_ssl_context()
        # configure keepalive settings to avoid ping timeouts during long transcriptions
        self.server = await websockets.serve(
            self.handler,
            self.host,
            self.port,
            ssl=ssl_context,
            ping_interval=30,
            ping_timeout=None,
        )

        print(f"Secure WebSocket server running on wss://{self.host}:{self.port}")

    async def stop(self):
        """Stop the WebSocket server and clean up resources."""
        if self.server is None:
            return

        print("Stopping WebSocket server...")
        self.server.close()
        await self.server.wait_closed()

        self.server = None
        self.port = None

        print("WebSocket server stopped")