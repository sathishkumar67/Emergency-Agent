"""
LiveKit Agent with Groq Integration
Emergency call-taking AI system with speech-to-text, LLM, and text-to-speech
"""

import os
import asyncio
import logging
from typing import Optional
from dotenv import load_dotenv

# LiveKit imports
from livekit import agents
from livekit.agents import (
    JobContext,
    llm,
    UserMessage,
    VoicePipelineAgent,
)
from livekit.plugins import silero, openai

# Groq imports
from groq import AsyncGroq

# Load environment variables
load_dotenv(".env.local", override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


class GroqSTT(agents.STT):
    """Speech-to-Text using Groq Whisper"""
    
    def __init__(self, *, api_key: str):
        self.client = AsyncGroq(api_key=api_key)
        self.recognition_started = False
    
    async def arecognize(self, buffer: agents.AudioBuffer) -> Optional[agents.STTSegment]:
        """Convert audio buffer to text"""
        try:
            # Get audio data
            frames = buffer.get_frames()
            if not frames:
                return None
            
            # Convert frames to audio bytes (PCM 16-bit, 16kHz)
            audio_bytes = b"".join(frame.data for frame in frames)
            
            if len(audio_bytes) < 100:  # Skip very short audio
                return None
            
            # Call Groq Whisper API
            transcript = await self.client.audio.transcriptions.create(
                file=("audio.wav", audio_bytes, "audio/wav"),
                model="whisper-large-v3",
                language="en",  # Change to support other languages
            )
            
            if transcript.text:
                return agents.STTSegment(
                    text=transcript.text,
                    confidence=0.9,  # Groq doesn't provide confidence
                    is_final=True,
                )
            return None
            
        except Exception as e:
            logger.error(f"STT error: {e}")
            return None


class GroqTTS(agents.TTS):
    """Text-to-Speech using Groq"""
    
    def __init__(self, *, api_key: str, voice: str = "nova"):
        self.client = AsyncGroq(api_key=api_key)
        self.voice = voice
    
    async def asynthesizes(self, segments, **kwargs) -> agents.AudioBuffer:
        """Convert text segments to speech"""
        try:
            full_text = "".join(seg.text if hasattr(seg, 'text') else str(seg) 
                               for seg in segments)
            
            if not full_text.strip():
                return agents.AudioBuffer(
                    sample_rate=24000,
                    num_channels=1,
                )
            
            # Call Groq TTS API
            response = await self.client.audio.speech.create(
                model="whisper-large-v3",  # Groq might have specific model
                text=full_text,
                voice=self.voice,
            )
            
            # Return audio buffer
            return agents.AudioBuffer(
                data=response.content,
                sample_rate=24000,
                num_channels=1,
            )
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return agents.AudioBuffer(sample_rate=24000, num_channels=1)


class EmergencyAgentLLM(llm.LLM):
    """LLM using Groq for emergency response"""
    
    def __init__(self, *, api_key: str):
        self.client = AsyncGroq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
    
    async def achat(self, messages: list, **kwargs) -> llm.LLMMessage:
        """Generate response using Groq"""
        try:
            # Convert to Groq message format
            groq_messages = [
                {
                    "role": msg.role,
                    "content": msg.content if isinstance(msg, UserMessage) else str(msg),
                }
                for msg in messages
            ]
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=groq_messages,
                temperature=0.3,  # Lower temp for emergency consistency
                max_tokens=200,
                top_p=0.9,
            )
            
            content = response.choices[0].message.content
            return llm.LLMMessage(role="assistant", content=content)
            
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return llm.LLMMessage(
                role="assistant",
                content="I'm having trouble processing that. Can you repeat?"
            )


# System prompt for emergency response
EMERGENCY_SYSTEM_PROMPT = """You are an intelligent emergency dispatcher AI assistant. Your role is to:

1. Receive calls from people in distress
2. Quickly understand their emergency situation
3. Provide calm, clear instructions
4. Gather critical information (location, number of people, injuries, etc.)
5. Brief responders with essential details

Key behaviors:
- Stay calm and professional
- Ask clear, sequential questions
- Repeat critical information back for confirmation
- Give priority to life-threatening situations
- Speak slowly and clearly
- Keep responses concise (max 2 sentences)
- Never make assumptions - always ask
- If location is unclear, make it priority #1

Remember: Your goal is to save lives through clear communication."""


async def prewarm(proc: JobContext):
    """Pre-warm up the agent before room connection"""
    await silero.VAD.load()


async def entrypoint(ctx: JobContext):
    """Main agent entrypoint"""
    
    logger.info(f"Agent joining room: {ctx.room.name}")
    
    # Initialize Groq-based components
    stt = GroqSTT(api_key=GROQ_API_KEY)
    tts = GroqTTS(api_key=GROQ_API_KEY, voice="nova")
    llm_model = EmergencyAgentLLM(api_key=GROQ_API_KEY)
    
    # Create VoicePipelineAgent
    agent = VoicePipelineAgent(
        vad=silero.VAD.load(),
        stt=stt,
        llm=llm_model,
        tts=tts,
    )
    
    # Set system prompt
    agent.metadata = {
        "system_prompt": EMERGENCY_SYSTEM_PROMPT,
        "call_type": "emergency",
        "start_time": ctx.room.metadata,
    }
    
    # Initial greeting
    initial_message = "Emergency Services. What is your emergency?"
    await agent.say(initial_message)
    
    # Start conversation loop
    await agent.start(ctx.room, ctx.participant)
    
    logger.info(f"Agent session ended for {ctx.participant.name}")


# RunConfig for agent dispatch
def setup():
    """Setup agent configuration"""
    return agents.JobContext(
        name="EmergencyAgent",
        description="Emergency dispatcher AI",
        entrypoint=entrypoint,
        prewarm=prewarm,
    )


if __name__ == "__main__":
    # Run agent
    agents.run_app(setup())
