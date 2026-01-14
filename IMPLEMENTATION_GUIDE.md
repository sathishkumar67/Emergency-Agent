# Complete Implementation Guide - Emergency Dispatcher with LiveKit & Groq

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CALLER (Browser/Phone)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ WebRTC/SIP
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    LIVEKIT SERVER                            │
│  - Room management                                          │
│  - Media routing (WebRTC)                                   │
│  - Participant coordination                                 │
└──────────────┬──────────────────────────┬──────────────────┘
               │                          │
         WebRTC│                          │
               ↓                          ↓
    ┌──────────────────┐        ┌──────────────────┐
    │  REACT FRONTEND  │        │ PYTHON AGENT     │
    │  (Browser UI)    │        │ with Groq        │
    └──────────────────┘        │ - STT            │
                                │ - LLM            │
                                │ - TTS            │
                                └──────┬───────────┘
                                       │ HTTPS
                                       ↓
                            ┌──────────────────┐
                            │   GROQ APIs      │
                            │ - Whisper (STT)  │
                            │ - LLaMA (LLM)    │
                            │ - TTS            │
                            └──────────────────┘
```

## Step 1: Setup Groq Access

### 1.1 Get Groq API Key
1. Go to https://console.groq.com
2. Sign up or log in
3. Navigate to API Keys section
4. Create new API key
5. Copy key to `.env.local` as `GROQ_API_KEY`

### 1.2 Available Groq Models
```
STT (Speech-to-Text):
  - whisper-large-v3  (Default, most accurate)

LLM (Language Model):
  - llama-3.3-70b-versatile  (70B, faster reasoning)
  - llama-3.3-70b-specdec
  - mixtral-8x7b-32768
  
TTS (Text-to-Speech):
  - distil-whisper-en  (Fast, English)
```

## Step 2: Setup LiveKit Cloud

### 2.1 Create LiveKit Project
1. Go to https://console.livekit.cloud
2. Sign up (free tier available)
3. Create new project
4. Copy credentials:
   - `LIVEKIT_URL` (e.g., `https://project-xxx.livekit.cloud`)
   - `LIVEKIT_API_KEY`
   - `LIVEKIT_API_SECRET`

### 2.2 Configuration Settings
```bash
# Copy example to real env
cp backend/.env.example backend/.env.local

# Fill in the following:
LIVEKIT_URL=https://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
GROQ_API_KEY=gsk_xxxxxxx
```

## Step 3: Backend Setup

### 3.1 Install Dependencies
```bash
cd backend
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 3.2 Run Agent
```bash
# Development mode (with hot reload)
python agent-production.py dev

# Or in terminal console
python agent-production.py console

# Production mode
python agent-production.py start
```

### 3.3 Run Backend API (Separate Terminal)
```bash
python backend-api.py

# Should start on http://localhost:5000
# Health check: curl http://localhost:5000/health
```

## Step 4: Frontend Setup

### 4.1 Install Dependencies
```bash
cd frontend
npm install
# or
yarn install
```

### 4.2 Create Vite Configuration
```javascript
// frontend/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      }
    }
  }
})
```

### 4.3 Create index.html
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Emergency Dispatcher</title>
</head>
<body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
</body>
</html>
```

### 4.4 Create main.jsx
```javascript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

### 4.5 Run Frontend
```bash
npm run dev

# Opens at http://localhost:5173
```

## Step 5: Complete Workflow

### 5.1 Development Testing
```bash
# Terminal 1: Backend API
cd backend
source venv/bin/activate
python backend-api.py

# Terminal 2: LiveKit Agent
python agent-production.py dev

# Terminal 3: Frontend
cd frontend
npm run dev

# Then open: http://localhost:5173
```

### 5.2 Using the Application
1. Open http://localhost:5173 in browser
2. Click "Start Call"
3. Allow microphone access when prompted
4. Speak to the emergency dispatcher AI
5. View real-time transcripts
6. End call when done

## Step 6: Deployment Options

### 6.1 Docker Deployment

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "agent-production.py", "start"]
```

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
```

### 6.2 Docker Compose
```yaml
version: '3.8'

services:
  backend-api:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - LIVEKIT_URL=${LIVEKIT_URL}
      - LIVEKIT_API_KEY=${LIVEKIT_API_KEY}
      - LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}
      - GROQ_API_KEY=${GROQ_API_KEY}
    volumes:
      - ./backend:/app

  agent:
    build: ./backend
    environment:
      - LIVEKIT_URL=${LIVEKIT_URL}
      - LIVEKIT_API_KEY=${LIVEKIT_API_KEY}
      - LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}
      - GROQ_API_KEY=${GROQ_API_KEY}
    depends_on:
      - livekit
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_LIVEKIT_URL=${LIVEKIT_URL}

  livekit:
    image: livekit/livekit-server:latest
    ports:
      - "7880:7880"
      - "7882:7882"
    environment:
      - RTC_PORT_RANGE_START=50000
      - RTC_PORT_RANGE_END=60000
    volumes:
      - ./livekit.yaml:/etc/livekit.yaml
```

### 6.3 Deploy to Cloud

#### Heroku
```bash
# Create Procfile
echo "web: python backend-api.py" > Procfile

# Deploy
heroku create emergency-dispatcher
git push heroku main
```

#### AWS/GCP/Azure
- Use container registry (ECR, GCR, ACR)
- Deploy with Kubernetes or App Service
- Set environment variables in deployment config

## Step 7: System Prompt Customization

Edit `agent-production.py` to customize the AI behavior:

```python
EMERGENCY_SYSTEM_PROMPT = """You are an emergency dispatcher...

Key behaviors:
- Ask for location first
- Identify emergency type
- Ask for number of people involved
- Provide clear instructions
- Escalate if needed
"""
```

## Step 8: Integration Points

### 8.1 Add Database Integration
```python
# Store calls in database
import sqlite3

conn = sqlite3.connect('emergency_calls.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS calls (
        id TEXT PRIMARY KEY,
        caller_id TEXT,
        room_id TEXT,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        duration INT,
        emergency_type TEXT,
        transcript TEXT
    )
''')
```

### 8.2 Add Email/SMS Notifications
```python
import smtplib

def send_alert(phone_number, message):
    # Use Twilio or similar
    pass
```

### 8.3 Add Analytics
```python
# Track metrics
call_metrics = {
    'total_calls': 0,
    'avg_duration': 0,
    'emergency_types': {},
    'response_time': 0,
}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Agent not connecting | Check LIVEKIT_URL, API credentials |
| No audio input | Check browser microphone permissions |
| Groq API errors | Verify GROQ_API_KEY is valid |
| CORS errors | Ensure backend API CORS is configured |
| Transcription not showing | Enable debug logging, check STT model |
| Agent not responding | Check LLM model availability in Groq |

## Performance Optimization

### Backend
- Use async/await for I/O operations
- Cache VAD model
- Batch API requests to Groq
- Use connection pooling

### Frontend
- Lazy load components
- Optimize WebRTC settings
- Reduce codec overhead
- Add reconnection logic

## Security Considerations

1. **API Keys**: Store in environment variables, never commit
2. **HTTPS**: Use HTTPS in production
3. **Authentication**: Add user authentication layer
4. **Rate Limiting**: Implement rate limits on API endpoints
5. **Input Validation**: Validate all user inputs
6. **Call Recording**: Ensure legal compliance for recording

## Testing

```bash
# Run agent in console mode
python agent-production.py console

# Test API endpoints
curl -X POST http://localhost:5000/api/get-token \
  -H "Content-Type: application/json" \
  -d '{"identity":"test-user","room":"test-room"}'

# Monitor logs
tail -f emergency_dispatcher.log
```

## Next Steps

1. ✅ Deploy to production LiveKit server
2. ✅ Add SIP integration for phone calls
3. ✅ Integrate with emergency database
4. ✅ Add human operator takeover
5. ✅ Implement call recording & playback
6. ✅ Add sentiment analysis for escalation
7. ✅ Create admin dashboard for call monitoring
8. ✅ Set up monitoring & alerting
