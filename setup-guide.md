# LiveKit AI Agent with Groq - Complete Setup Guide

## Project Structure
```
livekit-groq-agent/
├── backend/
│   ├── agent.py                 # LiveKit Agent with Groq
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example             # Environment template
│   └── services/
│       ├── groq_service.py      # Groq API wrapper
│       └── emergency_handler.py # Business logic
├── frontend/
│   ├── package.json
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.jsx              # Main React component
│   │   ├── components/
│   │   │   ├── CallInterface.jsx
│   │   │   └── TranscriptPanel.jsx
│   │   └── styles/
│   │       └── App.css
│   └── vite.config.js
├── docker-compose.yml           # Optional: Local LiveKit server
└── README.md
```

## Prerequisites
- Python 3.10+
- Node.js 18+
- LiveKit Cloud account (or self-hosted)
- Groq API key
- npm/yarn for frontend

## Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Copy .env template and fill in credentials
cp .env.example .env.local
```

**Fill in `.env.local`:**
```
LIVEKIT_URL=https://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
GROQ_API_KEY=your_groq_api_key
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

The frontend will start at `http://localhost:5173`

### 3. Run Agent
```bash
cd backend
python agent.py dev
# or for console testing:
python agent.py console
```

## Key Components

### Backend Pipeline
- **STT**: Groq Whisper (speech-to-text)
- **LLM**: Groq LLaMA 3.3 (70B) for responses
- **TTS**: Groq Text-to-Speech (text-to-voice)
- **VAD**: Silero VAD (voice activity detection)

### Frontend Features
- Real-time audio input/output
- Live transcripts
- Call duration & status tracking
- Emergency case context
- Participant management

## Deployment

### Development
```bash
# Terminal 1: Agent
python agent.py dev

# Terminal 2: Frontend
npm run dev
```

### Production with Docker
```bash
docker-compose up
# Accessible at https://localhost (with self-signed cert)
```

## Environment Variables Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| LIVEKIT_URL | LiveKit server URL | https://project.livekit.cloud |
| LIVEKIT_API_KEY | Server API authentication | api_key_... |
| LIVEKIT_API_SECRET | Server API secret | secret_... |
| GROQ_API_KEY | Groq API authentication | gsk_... |
| AGENT_NAME | Agent participant name | EmergencyAgent |
| ROOM_NAME | (Optional) Pre-defined room | emergency-room-1 |

## Troubleshooting

**Agent not connecting?**
- Verify LIVEKIT_URL, API_KEY, API_SECRET are correct
- Check `python agent.py download-files` for model downloads
- Ensure agent server is running before connecting frontend

**No audio output?**
- Check Groq API key is valid
- Verify microphone permissions in browser
- Check browser console for WebRTC errors

**Transcription not showing?**
- Enable VAD with `print_transcriptions=True` in agent setup
- Check Groq Whisper model is available

## Next Steps
1. Customize system prompt in `agent.py` for your use case
2. Add database integration for call logging
3. Implement call transfer to human operators
4. Add sentiment analysis for escalation
5. Set up monitoring/logging
