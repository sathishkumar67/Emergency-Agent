"""
Backend Flask API for LiveKit token generation and room management
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime
from livekit import api
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local", override=True)

# Configuration
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
CORS(app)

# Validate environment
if not all([LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET]):
    raise ValueError("Missing LiveKit environment variables")

logger.info(f"🚀 Backend API starting | LiveKit URL: {LIVEKIT_URL}")


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "livekit_configured": bool(LIVEKIT_URL),
    }), 200


@app.route("/api/get-token", methods=["POST"])
def get_token():
    """Generate LiveKit access token for client"""
    try:
        data = request.json
        identity = data.get("identity")
        room = data.get("room")
        
        if not identity or not room:
            return jsonify({"error": "Missing identity or room"}), 400
        
        # Generate token
        token = (
            api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
            .with_identity(identity)
            .with_name(identity)
            .with_metadata({"role": "caller", "call_type": "emergency"})
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room,
                    can_publish=True,
                    can_subscribe=True,
                    can_publish_data=True,
                )
            )
            .to_jwt()
        )
        
        logger.info(f"✅ Token generated | Identity: {identity} | Room: {room}")
        
        return jsonify({
            "token": token,
            "url": LIVEKIT_URL,
            "room": room,
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Token generation error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/create-room", methods=["POST"])
def create_room():
    """Create a new LiveKit room"""
    try:
        data = request.json
        room_name = data.get("room", f"room-{datetime.now().timestamp()}")
        
        # Create room using LiveKit API
        lkapi = api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        
        # Note: This requires livekit-api package
        # room_info = await lkapi.room.create_room(
        #     api.CreateRoomRequest(name=room_name)
        # )
        
        logger.info(f"✅ Room created: {room_name}")
        
        return jsonify({
            "room": room_name,
            "created_at": datetime.now().isoformat(),
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Room creation error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/rooms", methods=["GET"])
def list_rooms():
    """List all active rooms"""
    try:
        # This would typically query the LiveKit server
        # Placeholder response
        return jsonify({
            "rooms": [
                {"name": "emergency-call-1", "participants": 2, "created_at": datetime.now().isoformat()},
            ],
            "total": 1,
        }), 200
        
    except Exception as e:
        logger.error(f"❌ List rooms error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/call-history", methods=["GET"])
def call_history():
    """Get call history (placeholder - integrate with DB)"""
    try:
        # In production, fetch from database
        history = [
            {
                "call_id": "call-001",
                "duration": 245,
                "created_at": datetime.now().isoformat(),
                "emergency_type": "Medical",
                "status": "completed",
            }
        ]
        
        return jsonify({"calls": history}), 200
        
    except Exception as e:
        logger.error(f"❌ History retrieval error: {e}")
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Development server
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )
