# Quick Start Guide - 15 Minutes to Running

## Prerequisites (Have Ready)
- [Groq API Key](https://console.groq.com) - free, no credit card
- [LiveKit Cloud Account](https://console.livekit.cloud) - free tier available
- Python 3.10+ installed
- Node.js 18+ installed
- Git installed

## 5-Minute Setup

### Step 1: Get API Keys
```bash
# 1. Get Groq API Key
#    Go to https://console.groq.com → API Keys → Create Key
#    Copy the key

# 2. Get LiveKit Credentials
#    Go to https://console.livekit.cloud → New Project
#    Copy: URL, API Key, API Secret
```

### Step 2: Clone & Configure
```bash
# Create project directory
mkdir emergency-dispatcher && cd emergency-dispatcher

# Create backend directory
mkdir backend && cd backend

# Copy all backend files:
# - agent-production.py
# - backend-api.py
# - requirements.txt
# - .env.example → rename to .env.local

# Fill in .env.local with your keys
cat > .env.local << 'EOF'
LIVEKIT_URL=https://your-project.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
GROQ_API_KEY=gsk_your_groq_key
EOF

# Go to frontend directory
cd ../
mkdir frontend && cd frontend

# Copy all frontend files:
# - App.jsx
# - App.css
# - package.json
# - vite.config.js
# - src/main.jsx
# - public/index.html
```

### Step 3: Install Dependencies (5 minutes)
```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

### Step 4: Run Everything (3 terminals)

#### Terminal 1: Backend API
```bash
cd backend
source venv/bin/activate
python backend-api.py
# Should show: * Running on http://0.0.0.0:5000
```

#### Terminal 2: LiveKit Agent
```bash
cd backend
source venv/bin/activate
python agent-production.py dev
# Should show: 🚀 Starting Emergency Dispatcher Agent
```

#### Terminal 3: Frontend
```bash
cd frontend
npm run dev
# Should show: ➜  Local:   http://localhost:5173
```

### Step 5: Test It!
1. Open http://localhost:5173 in browser
2. Click "Start Call"
3. Allow microphone when prompted
4. Say: "I need help, there's been an accident"
5. Listen to AI respond via speakers
6. See transcript update in real-time

## File Structure Created
```
emergency-dispatcher/
├── backend/
│   ├── venv/                      (created by venv)
│   ├── agent-production.py        ✅ Main agent logic
│   ├── backend-api.py             ✅ Token generation API
│   ├── requirements.txt           ✅ Python packages
│   ├── .env.local                 ✅ Your credentials
│   └── .env.example               ✅ Template
├── frontend/
│   ├── node_modules/              (created by npm)
│   ├── src/
│   │   ├── App.jsx                ✅ Main component
│   │   ├── App.css                ✅ Styling
│   │   └── main.jsx               ✅ Entry point
│   ├── public/
│   │   └── index.html             ✅ HTML template
│   ├── package.json               ✅ Dependencies
│   ├── vite.config.js             ✅ Build config
│   └── .gitignore                 ✅ Git ignore
└── README.md
```

## Key Features Working

✅ **Speech-to-Text**: Groq Whisper converts your speech to text in real-time
✅ **AI Response**: LLaMA 3.3 generates emergency dispatcher responses
✅ **Text-to-Speech**: Groq TTS speaks responses aloud
✅ **Live Transcript**: See conversation in real-time
✅ **Call Duration**: Track how long the call has been active
✅ **Room Management**: Multiple calls in separate rooms
✅ **WebRTC Audio**: Crystal-clear P2P audio routing

## What's Happening Behind the Scenes

```
You speak
    ↓
Browser captures audio
    ↓
Sends to LiveKit via WebRTC
    ↓
Agent receives audio
    ↓
Groq Whisper converts to text
    ↓
Groq LLaMA generates response
    ↓
Groq TTS converts response to speech
    ↓
Sends audio back to LiveKit
    ↓
Browser plays audio
    ↓
You hear the response
```

## Common Issues & Fixes

### "Connection refused" on http://localhost:5000
**Fix**: Backend API not running
```bash
cd backend
python backend-api.py
```

### "Agent not responding"
**Fix**: Agent process not running
```bash
cd backend
python agent-production.py dev
```

### "No audio input"
**Fix**: Browser microphone permission not granted
- Click lock icon in address bar
- Allow microphone access
- Refresh page

### "Groq API error"
**Fix**: Invalid API key
- Verify GROQ_API_KEY in .env.local
- Check it starts with `gsk_`
- Get new key from console.groq.com

### "LiveKit connection failed"
**Fix**: Invalid LiveKit credentials
- Verify LIVEKIT_URL is exact (with https://)
- Check API_KEY and API_SECRET are correct
- Get fresh credentials from console.livekit.cloud

## Next Steps

### For Development
- Modify `EMERGENCY_SYSTEM_PROMPT` in `agent-production.py` for different behaviors
- Add database integration to store calls
- Implement human operator handoff

### For Production
- Deploy to cloud (Heroku, AWS, GCP)
- Set up monitoring & logging
- Add rate limiting & authentication
- Enable HTTPS
- Scale with Docker & Kubernetes

### For Enhancement
- Add sentiment analysis for escalation
- Implement call recording
- Create admin dashboard
- Add multi-language support
- Integrate with CAD systems

## Support Resources

- **LiveKit Docs**: https://docs.livekit.io
- **Groq API Docs**: https://console.groq.com/docs/quickstart
- **LiveKit Agent Framework**: https://github.com/livekit/agents
- **Troubleshooting**: https://docs.livekit.io/home/troubleshooting

## Your First Custom Enhancement

Try changing the system prompt in `agent-production.py`:

```python
EMERGENCY_SYSTEM_PROMPT = """You are a customer service agent helping with billing inquiries...
1. Ask for account number
2. Verify caller information
3. Help with their issue
4. Offer solutions
5. Thank them for calling
"""
```

Redeploy: `python agent-production.py dev`

That's it! You now have a fully functional AI voice agent system. 🚀
