# 🎤 SnapInterview

<div align="center">

**Your AI Interview Coach That Never Needs WiFi**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flutter](https://img.shields.io/badge/Flutter-3.0%2B-02569B.svg)](https://flutter.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Offline](https://img.shields.io/badge/100%25-Offline-success.svg)]()

*Practice interviews anywhere, anytime—no cloud, no APIs, no privacy concerns.*

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [Demo](#-demo)

</div>

---

## 🌟 What is SnapInterview?

SnapInterview is a **fully offline, AI-powered mock interview platform** that brings the interview room to your device. Using local speech recognition, on-device LLMs, and intelligent resume parsing, it delivers a realistic interview experience without sending a single byte to the cloud.

### Why SnapInterview?

- 🔒 **100% Private** - Your data never leaves your device
- ⚡ **Lightning Fast** - No network latency, instant responses
- 🎯 **Personalized** - Questions tailored to your resume
- 📱 **Cross-Platform** - Desktop server + Mobile client
- 🌐 **Always Available** - Works on planes, trains, or your basement

---

## ✨ Features

### 🎙️ Voice-First Interview Experience
- Real-time speech-to-text using Whisper
- Natural conversation flow
- Optional text-to-speech for interviewer responses

### 🧠 Intelligent Question Generation
- **Resume-aware questioning** - Parses your PDF/DOCX resume
- **Adaptive difficulty** - Adjusts based on your answers
- **Dynamic follow-ups** - Probes deeper on interesting responses
- **Multi-domain support** - Technical, behavioral, and situational questions

### 🔐 Privacy by Design
```
┌─────────────┐
│ Your Device │ ← Everything happens here
└─────────────┘
      ↓
   No cloud ☁️✖️
   No APIs 🌐✖️
   No tracking 👁️✖️
```

### 📱 Dual-Device Architecture
- **Desktop** - Runs the AI engine (Python server)
- **Mobile** - Interview interface (Flutter app)
- **Connection** - Local WiFi via QR code pairing

---

## 🚀 Quick Start

### Prerequisites
```bash
✓ Python 3.10 or 3.11
✓ 8GB RAM (16GB recommended)
✓ Microphone
✓ ~4GB disk space for models
```

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/Joyshah62/SnapInterview.git
cd SnapInterview

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the server
python app.py
```
---

## 📱 Mobile App Setup
```bash
cd snapinterview_mobile
flutter pub get
flutter run  # Or build APK: flutter build apk
```

**Connect to desktop:**
1. Start Python server on desktop
2. Open mobile app
3. Scan QR code displayed on desktop
4. Begin interview!

---

## 🎯 How to Use

### Starting an Interview
```python
1. Launch the server → python app.py
2. Upload your resume (optional but recommended)
3. Select:
   • Target Role (e.g., "Software Engineer")
   • Difficulty (Easy / Medium / Hard)
4. Hit "Start Interview"
5. Speak naturally when prompted
```

### Sample Interview Flow
```
🤖 Interviewer: "Tell me about a challenging project you worked on."

🎤 You: "I built a distributed database with horizontal fragmentation..."

🤖 Interviewer: "Interesting! How did you handle data consistency 
                across nodes?"

🎤 You: [Your answer triggers adaptive follow-up]

🤖 Interviewer: "Can you walk me through your synchronization strategy?"
```

---

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────┐
│                  MOBILE APP                      │
│            (Flutter - Interview UI)              │
└───────────────────┬─────────────────────────────┘
                    │ WebSocket
                    ↓
┌─────────────────────────────────────────────────┐
│              PYTHON SERVER (Desktop)             │
├─────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌─────────────┐             │
│  │   Whisper    │→ │ Resume      │             │
│  │   (STT)      │  │ Parser      │             │
│  └──────────────┘  └─────────────┘             │
│         ↓                  ↓                     │
│  ┌─────────────────────────────────────┐        │
│  │     LLaMA 3.2 3B Instruct          │        │
│  │     (llama.cpp inference)           │        │
│  └─────────────────────────────────────┘        │
│         ↓                                        │
│  ┌──────────────┐                               │
│  │   TTS        │ (Optional)                    │
│  │   (piper)    │                               │
│  └──────────────┘                               │
└─────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM** | LLaMA 3.2 3B (GGUF) | Question generation & reasoning |
| **STT** | Whisper (base.en) | Speech-to-text transcription |
| **TTS** | Piper (optional) | Text-to-speech output |
| **Backend** | Python + Flask | Server & orchestration |
| **Mobile** | Flutter | Cross-platform UI |
| **Inference** | llama.cpp | Optimized local LLM execution |


## 🔧 Configuration

### Customize Interview Settings

Edit `config.yaml`:
```yaml
interview:
  default_duration: 30  # minutes
  questions_per_session: 8
  difficulty_adaptation: true
  
llm:
  model_path: "models/Llama-3.2-3B-Instruct-Q4_K_M.gguf"
  context_length: 4096
  temperature: 0.7
  
whisper:
  model: "base.en"
  language: "en"
```

---

## 🛣️ Roadmap

- [x] Core interview engine
- [x] Resume parsing
- [x] Mobile app
- [x] Interview analytics dashboard
- [ ] Multi-language support
- [ ] Industry-specific question banks
- [ ] Mock group interviews
- [ ] Interview recording & playback

---

## Team

Built with ❤️ by:

| Hitanshu Oza | Rishabh Shah| Joy Shah | Om Patel | 
|:---:|:---:|:---:|:---:|
| hro24@scarletmail.rutgers.edu | rs2780@scarletmail.rutgers.edu |joy.shah@rutgers.edu | op187@scarletmail.rutgers.edu | 

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Fast LLM inference
- [Whisper](https://github.com/openai/whisper) - Speech recognition
- [Flutter](https://flutter.dev/) - Beautiful mobile UI
- Meta AI - LLaMA model family


