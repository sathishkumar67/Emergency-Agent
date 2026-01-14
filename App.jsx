import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Phone, PhoneOff, Volume2, Loader } from 'lucide-react';
import './App.css';

const App = () => {
  // Connection state
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState('');
  
  // Audio state
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(70);
  
  // Call state
  const [callDuration, setCallDuration] = useState(0);
  const [roomName, setRoomName] = useState('emergency-call-' + Date.now());
  
  // Transcript & messages
  const [messages, setMessages] = useState([]);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [agentSpeaking, setAgentSpeaking] = useState(false);
  
  // LiveKit references
  const room = useRef(null);
  const localParticipant = useRef(null);
  const audioContext = useRef(null);
  
  // Timer for call duration
  useEffect(() => {
    if (!isConnected) return;
    
    const interval = setInterval(() => {
      setCallDuration(prev => prev + 1);
    }, 1000);
    
    return () => clearInterval(interval);
  }, [isConnected]);

  // Format call duration as MM:SS
  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  // Connect to LiveKit room
  const handleConnect = async () => {
    setIsConnecting(true);
    setError('');
    
    try {
      // Get token from your backend
      const response = await fetch('/api/get-token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          identity: 'caller-' + Date.now(),
          room: roomName,
        }),
      });
      
      if (!response.ok) throw new Error('Failed to get token');
      
      const { token } = await response.json();
      
      // Import LiveKit dynamically
      const { LiveClient, Room, RoomEvent, ParticipantEvent } = await import('livekit-client');
      
      // Create room
      const newRoom = new Room();
      room.current = newRoom;
      
      // Event handlers
      newRoom.on(RoomEvent.ParticipantConnected, (participant) => {
        console.log('Participant connected:', participant.name);
      });
      
      newRoom.on(RoomEvent.ParticipantDisconnected, () => {
        console.log('Participant disconnected');
      });
      
      newRoom.on(RoomEvent.TrackSubscribed, (track, pub, participant) => {
        if (track.kind === 'audio') {
          // Audio track from agent
          const audio = document.getElementById('agent-audio');
          if (audio) {
            audio.srcObject = new MediaStream([track]);
          }
        }
      });
      
      // Connect to room
      const url = process.env.REACT_APP_LIVEKIT_URL || 'ws://localhost:7880';
      await newRoom.connect(url, token);
      
      // Publish local audio
      const audioTrack = await navigator.mediaDevices.getUserMedia({ audio: true });
      await newRoom.localParticipant.publishTrack(audioTrack.getTracks()[0]);
      
      setIsConnected(true);
      setMessages([{ type: 'system', text: 'Connected to Emergency Services' }]);
      
    } catch (err) {
      console.error('Connection error:', err);
      setError(err.message);
    } finally {
      setIsConnecting(false);
    }
  };

  // Disconnect from room
  const handleDisconnect = async () => {
    try {
      if (room.current) {
        await room.current.disconnect();
      }
      setIsConnected(false);
      setCallDuration(0);
      setMessages([]);
      setCurrentTranscript('');
    } catch (err) {
      console.error('Disconnect error:', err);
    }
  };

  // Toggle mute
  const handleMuteToggle = async () => {
    if (room.current) {
      const audioTracks = room.current.localParticipant.audioTracks;
      for (const [, pub] of audioTracks) {
        if (pub.track) {
          pub.track.enabled = isMuted;
        }
      }
      setIsMuted(!isMuted);
    }
  };

  // Handle volume change
  const handleVolumeChange = (e) => {
    const newVolume = parseInt(e.target.value);
    setVolume(newVolume);
    
    const audio = document.getElementById('agent-audio');
    if (audio) {
      audio.volume = newVolume / 100;
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <Phone className="logo-icon" />
            <h1>Emergency Dispatcher AI</h1>
          </div>
          <div className="header-status">
            {isConnected && (
              <div className="status-badge connected">
                <span className="status-dot"></span>
                Connected • {formatDuration(callDuration)}
              </div>
            )}
            {!isConnected && (
              <div className="status-badge disconnected">
                <span className="status-dot"></span>
                Not Connected
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="call-interface">
          {/* Messages/Transcript Panel */}
          <div className="transcript-panel">
            <div className="transcript-header">
              <h2>Call Transcript</h2>
              <span className="message-count">{messages.length} messages</span>
            </div>
            
            <div className="transcript-messages">
              {messages.map((msg, idx) => (
                <div key={idx} className={`message message-${msg.type}`}>
                  <span className="message-label">
                    {msg.type === 'system' && '🔔'}
                    {msg.type === 'agent' && '🤖'}
                    {msg.type === 'user' && '👤'}
                  </span>
                  <span className="message-text">{msg.text}</span>
                </div>
              ))}
              
              {currentTranscript && (
                <div className="message message-live">
                  <span className="message-label">🎤</span>
                  <span className="message-text">
                    {currentTranscript}
                    <span className="typing-indicator">...</span>
                  </span>
                </div>
              )}
              
              {agentSpeaking && (
                <div className="message message-agent-speaking">
                  <span className="message-label">🤖</span>
                  <span className="message-text">
                    <span className="speaking-indicator">
                      <span></span><span></span><span></span>
                    </span>
                    Agent speaking...
                  </span>
                </div>
              )}
            </div>

            {error && (
              <div className="error-banner">
                <span>⚠️ {error}</span>
              </div>
            )}
          </div>

          {/* Control Panel */}
          <div className="control-panel">
            <div className="room-selector">
              <label htmlFor="room-input">Room Name:</label>
              <input
                id="room-input"
                type="text"
                value={roomName}
                onChange={(e) => setRoomName(e.target.value)}
                disabled={isConnected}
                placeholder="emergency-call-xxx"
              />
            </div>

            {/* Call Controls */}
            <div className="call-controls">
              {!isConnected ? (
                <button
                  className="btn btn-primary btn-lg"
                  onClick={handleConnect}
                  disabled={isConnecting}
                >
                  {isConnecting ? (
                    <>
                      <Loader className="icon-spin" size={20} />
                      Connecting...
                    </>
                  ) : (
                    <>
                      <Phone size={20} />
                      Start Call
                    </>
                  )}
                </button>
              ) : (
                <button
                  className="btn btn-danger btn-lg"
                  onClick={handleDisconnect}
                >
                  <PhoneOff size={20} />
                  End Call
                </button>
              )}
            </div>

            {/* Audio Controls */}
            {isConnected && (
              <div className="audio-controls">
                <button
                  className={`btn btn-secondary ${isMuted ? 'muted' : ''}`}
                  onClick={handleMuteToggle}
                  title={isMuted ? 'Unmute' : 'Mute'}
                >
                  {isMuted ? <MicOff size={20} /> : <Mic size={20} />}
                  {isMuted ? 'Muted' : 'Unmute'}
                </button>

                <div className="volume-control">
                  <Volume2 size={18} />
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={volume}
                    onChange={handleVolumeChange}
                    className="volume-slider"
                  />
                  <span className="volume-value">{volume}%</span>
                </div>
              </div>
            )}

            {/* Call Info */}
            {isConnected && (
              <div className="call-info">
                <div className="info-item">
                  <span className="label">Duration:</span>
                  <span className="value">{formatDuration(callDuration)}</span>
                </div>
                <div className="info-item">
                  <span className="label">Status:</span>
                  <span className="value">Active</span>
                </div>
                <div className="info-item">
                  <span className="label">Room:</span>
                  <span className="value">{roomName}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Hidden audio elements */}
      <audio id="agent-audio" autoPlay={true} />
    </div>
  );
};

export default App;
