"""
Production-Ready LiveKit Agent with Groq Integration
Uses LiveKit Groq plugins for STT, LLM, and TTS
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import (
    JobContext,
    llm,
    UserMessage,
    VoicePipelineAgent,
    metrics,
)
from livekit.plugins import silero, groq
from livekit.agents.pipeline import VoicePipelineAgent, AgentCallContext

# Load environment variables
load_dotenv(".env.local", override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Environment variables
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Configuration
AGENT_NAME = os.getenv("AGENT_NAME", "EmergencyAgent")


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
- Acknowledge what caller says before asking next question

Example flow:
Caller: "There's been an accident"
Agent: "Okay, I understand. Where is the accident located?"
Caller: "On Main Street and 5th"
Agent: "That's Main Street and 5th Avenue. How many people are injured?"

Remember: Your goal is to save lives through clear communication and gathering essential information."""


class EmergencyCallHandler:
    """Handles emergency call logic and context"""
    
    def __init__(self, ctx: JobContext):
        self.ctx = ctx
        self.start_time = datetime.now()
        self.messages_exchanged = 0
        self.emergency_type = None
        self.location = None
        self.casualties = 0
        self.is_escalated = False
    
    async def log_call_event(self, event_type: str, data: dict):
        """Log call events for monitoring"""
        logger.info(f"[CALL-EVENT] {event_type}: {data}")
    
    async def on_agent_response(self, text: str):
        """Handle agent responses"""
        self.messages_exchanged += 1
        await self.log_call_event("agent_response", {
            "message_count": self.messages_exchanged,
            "text_length": len(text)
        })
    
    async def on_caller_message(self, text: str):
        """Handle caller messages"""
        # Parse for emergency indicators
        if any(keyword in text.lower() for keyword in ["heart", "chest pain", "can't breathe", "choking"]):
            self.emergency_type = "CRITICAL_MEDICAL"
            self.is_escalated = True
            await self.log_call_event("escalation", {"type": self.emergency_type})
        
        await self.log_call_event("caller_message", {
            "text_length": len(text),
            "escalated": self.is_escalated
        })


async def prewarm(proc: JobContext):
    """Pre-warm components before room connection"""
    logger.info("Pre-warming VAD and other components...")
    await silero.VAD.load()
    logger.info("Pre-warm complete")


async def entrypoint(ctx: JobContext):
    """Main agent entrypoint"""
    
    logger.info(f"🚨 Emergency Agent starting | Room: {ctx.room.name}")
    
    # Initialize call handler
    call_handler = EmergencyCallHandler(ctx)
    
    # Initialize Groq components using LiveKit plugins
    try:
        # STT: Groq Whisper
        initial_ctx = llm.ChatContext().add_system(EMERGENCY_SYSTEM_PROMPT)
        
        agent = VoicePipelineAgent(
            vad=silero.VAD.load(),
            stt=groq.STT(),  # Uses GROQ_API_KEY env var
            llm=groq.LLM(
                model="llama-3.3-70b-versatile",
                system_prompt=EMERGENCY_SYSTEM_PROMPT,
            ),
            tts=groq.TTS(voice="nova"),  # Uses GROQ_API_KEY env var
            name=AGENT_NAME,
        )
        
        # Store call context
        call_ctx = ctx
        
        logger.info("✅ Agent components initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize agent: {e}")
        raise
    
    # Set up call event handlers
    @agent.on_message
    async def on_message(msg: llm.ChatMessage):
        """Handle LLM responses"""
        if msg.role == "assistant":
            await call_handler.on_agent_response(msg.content)
    
    @agent.on_human_message
    async def on_human_message(msg: UserMessage):
        """Handle caller messages"""
        if msg.text:
            await call_handler.on_caller_message(msg.text)
    
    # Initial greeting
    initial_greeting = "Emergency Services. What is your emergency? Please describe what's happening."
    logger.info(f"Agent greeting: {initial_greeting}")
    
    try:
        await agent.say(initial_greeting, add_to_chat_ctx=False)
    except Exception as e:
        logger.error(f"Failed to play initial greeting: {e}")
    
    # Log call start
    await call_handler.log_call_event("call_start", {
        "room": ctx.room.name,
        "agent": AGENT_NAME,
        "time": datetime.now().isoformat(),
    })
    
    # Start the agent conversation loop
    logger.info("Starting agent conversation loop...")
    await agent.start(ctx.room, ctx.participant)
    
    # Log call end
    duration = (datetime.now() - call_handler.start_time).total_seconds()
    await call_handler.log_call_event("call_end", {
        "duration_seconds": duration,
        "messages_exchanged": call_handler.messages_exchanged,
        "escalated": call_handler.is_escalated,
        "emergency_type": call_handler.emergency_type,
    })
    
    logger.info(f"🏁 Agent session ended | Duration: {duration}s | Messages: {call_handler.messages_exchanged}")


def setup():
    """Setup agent configuration"""
    return agents.JobContext(
        name="EmergencyDispatcher",
        description="AI-powered emergency dispatcher with Groq integration",
        entrypoint=entrypoint,
        prewarm=prewarm,
    )


if __name__ == "__main__":
    logger.info("🚀 Starting Emergency Dispatcher Agent")
    logger.info(f"LiveKit URL: {LIVEKIT_URL}")
    logger.info(f"Agent: {AGENT_NAME}")
    
    # Run agent
    agents.run_app(setup())
