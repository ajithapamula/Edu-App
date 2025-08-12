// =============================================================================
// ULTRA-FAST DAILY STANDUP API - NO FALLBACKS, REAL RESPONSES ONLY
// =============================================================================

import { assessmentApiRequest } from './index2';

// Ultra-Fast Voice Activity Detection with 800ms silence
class UltraFastVoiceDetector {
  constructor() {
    this.isListening = false;
    this.silenceThreshold = 0.015; // Slightly higher for cleaner detection
    this.silenceDelay = 150; // Reduced from 800ms for faster response
    this.maxRecordingTime = 30000; // 25 seconds max
    this.audioContext = null;
    this.analyser = null;
    this.dataArray = null;
    this.silenceTimer = null;
    this.recordingTimer = null;
    this.onSilenceDetected = null;
    this.onSpeechDetected = null;
    this.speechStarted = false;
  }

  async initialize(stream) {
    try {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const source = this.audioContext.createMediaStreamSource(stream);
      this.analyser = this.audioContext.createAnalyser();
      
      this.analyser.fftSize = 512; // Optimized for faster processing
      this.analyser.smoothingTimeConstant = 0.2; // Faster response
      
      source.connect(this.analyser);
      this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
      
      console.log('🎙️ Ultra-Fast Voice Activity Detector initialized');
      return true;
    } catch (error) {
      console.error('❌ VAD initialization failed:', error);
      throw new Error(`Voice detection setup failed: ${error.message}`);
    }
  }

  startListening() {
    if (this.isListening) return;
    
    this.isListening = true;
    this.speechStarted = false;
    console.log('👂 Started ultra-fast voice detection');
    this.detectVoiceActivity();
    
    // Auto-stop after max recording time
    this.recordingTimer = setTimeout(() => {
      console.log('⏰ Max recording time reached');
      this.stopListening();
    }, this.maxRecordingTime);
  }

  detectVoiceActivity() {
    if (!this.isListening || !this.analyser) return;

    this.analyser.getByteFrequencyData(this.dataArray);
    
    // Optimized volume calculation
    let sum = 0;
    for (let i = 0; i < this.dataArray.length; i++) {
      sum += this.dataArray[i];
    }
    const average = sum / this.dataArray.length;
    const volume = average / 255;

    if (volume > this.silenceThreshold) {
      // Speech detected
      if (!this.speechStarted) {
        this.speechStarted = true;
        console.log('🗣️ Speech START detected');
      }
      
      if (this.silenceTimer) {
        clearTimeout(this.silenceTimer);
        this.silenceTimer = null;
      }
      
      if (this.onSpeechDetected) {
        this.onSpeechDetected(volume);
      }
    } else {
      // Silence detected
      if (this.speechStarted && !this.silenceTimer) {
        this.silenceTimer = setTimeout(() => {
          console.log(`🤫 Silence detected for ${this.silenceDelay}ms, stopping recording`);
          this.stopListening();
        }, this.silenceDelay);
      }
    }

    // Continue monitoring with optimized frame rate
    requestAnimationFrame(() => this.detectVoiceActivity());
  }

  stopListening() {
    if (!this.isListening) return;
    
    this.isListening = false;
    this.speechStarted = false;
    
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }
    
    if (this.recordingTimer) {
      clearTimeout(this.recordingTimer);
      this.recordingTimer = null;
    }
    
    if (this.onSilenceDetected) {
      this.onSilenceDetected();
    }
    
    console.log('🛑 Ultra-fast voice detection stopped');
  }

  cleanup() {
    this.stopListening();
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
  }
}

// Ultra-Fast Audio Manager with Optimized Pipeline
class UltraFastAudioManager {
  constructor() {
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.stream = null;
    this.isRecording = false;
    this.vad = new UltraFastVoiceDetector();
    this.onRecordingComplete = null;
    this.onSpeechStart = null;
    this.audioQueue = [];
    this.isPlayingAudio = false;
    this.currentAudio = null;
  }

  async startListening() {
    try {
      console.log('🎤 Starting ultra-fast voice conversation...');
      
      // Get microphone access with optimized settings
      this.stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000,
          channelCount: 1 // Mono for faster processing
        } 
      });
      
      // Initialize ultra-fast voice activity detection
      const vadInitialized = await this.vad.initialize(this.stream);
      if (!vadInitialized) {
        throw new Error('Ultra-fast voice activity detection failed to initialize');
      }
      
      // Setup media recorder with optimized settings
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
        ? 'audio/webm;codecs=opus' 
        : 'audio/webm';
      
      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: mimeType,
        audioBitsPerSecond: 16000 // Lower bitrate for faster processing
      });
      
      this.audioChunks = [];
      
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };
      
      this.mediaRecorder.onstop = () => {
        const audioBlob = new Blob(this.audioChunks, { type: mimeType });
        this.audioChunks = [];
        this.isRecording = false;
        
        console.log('📦 Audio recording completed, size:', audioBlob.size);
        
        if (this.onRecordingComplete) {
          this.onRecordingComplete(audioBlob);
        }
      };
      
      // Setup ultra-fast voice activity detection callbacks
      this.vad.onSpeechDetected = (volume) => {
        if (!this.isRecording && !this.isPlayingAudio) {
          console.log('🗣️ Speech detected, starting recording IMMEDIATELY...');
          this.startRecording();
          
          if (this.onSpeechStart) {
            this.onSpeechStart();
          }
        }
      };
      
      this.vad.onSilenceDetected = () => {
        if (this.isRecording) {
          console.log('🤫 Silence detected, stopping recording IMMEDIATELY...');
          this.stopRecording();
        }
      };
      
      // Start ultra-fast voice activity detection
      this.vad.startListening();
      
      console.log('✅ Ultra-fast conversation ready - 800ms silence detection active');
      
    } catch (error) {
      console.error('❌ Failed to start ultra-fast listening:', error);
      throw new Error(`Microphone setup failed: ${error.message}`);
    }
  }

  startRecording() {
    if (this.isRecording || !this.mediaRecorder) return;
    
    try {
      this.mediaRecorder.start(100); // Record in 100ms chunks for responsiveness
      this.isRecording = true;
      console.log('🔴 Ultra-fast recording started');
    } catch (error) {
      console.error('❌ Recording start failed:', error);
      throw new Error(`Recording failed: ${error.message}`);
    }
  }

  stopRecording() {
    if (!this.isRecording || !this.mediaRecorder) return;
    
    try {
      this.mediaRecorder.stop();
      console.log('⏹️ Ultra-fast recording stopped');
    } catch (error) {
      console.error('❌ Recording stop failed:', error);
    }
  }

  async playAudioBuffer(audioBuffer) {
    return new Promise((resolve, reject) => {
      try {
        this.isPlayingAudio = true;
        
        const audioBlob = new Blob([audioBuffer], { type: 'audio/wav' });
        const audioUrl = URL.createObjectURL(audioBlob);
        this.currentAudio = new Audio(audioUrl);
        
        // Optimized playback settings
        this.currentAudio.playbackRate = 1.15; // Slightly faster for efficiency
        this.currentAudio.preload = 'auto';
        
        this.currentAudio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          this.isPlayingAudio = false;
          this.currentAudio = null;
          console.log('🎵 Audio chunk finished playing');
          resolve();
        };
        
        this.currentAudio.onerror = (error) => {
          URL.revokeObjectURL(audioUrl);
          this.isPlayingAudio = false;
          this.currentAudio = null;
          console.error('❌ Audio playback failed:', error);
          reject(new Error(`Audio playback failed: ${error.message}`));
        };
        
        this.currentAudio.play().then(() => {
          console.log('🎵 Playing AI response chunk...');
        }).catch(reject);
        
      } catch (error) {
        this.isPlayingAudio = false;
        this.currentAudio = null;
        reject(new Error(`Audio buffer playback failed: ${error.message}`));
      }
    });
  }

  async playAudioStream(audioChunks) {
    // Play audio chunks sequentially for seamless experience
    for (const chunk of audioChunks) {
      try {
        await this.playAudioBuffer(chunk);
      } catch (error) {
        console.error('❌ Audio chunk playback failed:', error);
        throw error;
      }
    }
  }

  stopAllAudio() {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      this.currentAudio = null;
    }
    this.isPlayingAudio = false;
  }

  stopListening() {
    this.vad.cleanup();
    
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    
    this.stopAllAudio();
    this.isRecording = false;
    
    console.log('🛑 Ultra-fast audio manager stopped');
  }
}

// Ultra-Fast WebSocket Manager - NO FALLBACKS, FAIL FAST
class UltraFastWebSocketManager {
  constructor() {
    this.websocket = null;
    this.eventHandlers = {};
    this.isConnected = false;
    this.sessionId = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 0; // NO AUTO-RECONNECT IN DEVELOPMENT
  }

  setEventHandlers(handlers) {
    this.eventHandlers = handlers;
  }

  async connect(sessionId) {
    this.sessionId = sessionId;
    
    try {
      const wsUrl = `wss://192.168.48.201:8070/daily_standup/ws/${sessionId}`;
      console.log('🔌 Connecting to ultra-fast WebSocket:', wsUrl);
      
      this.websocket = new WebSocket(wsUrl);
      
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          this.websocket.close();
          reject(new Error(`WebSocket connection timeout after 10 seconds`));
        }, 10000);

        this.websocket.onopen = () => {
          clearTimeout(timeout);
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.setupEventHandlers();
          console.log('✅ Ultra-fast WebSocket connected successfully');
          resolve();
        };

        this.websocket.onerror = (error) => {
          clearTimeout(timeout);
          console.error('❌ WebSocket connection failed:', error);
          reject(new Error(`WebSocket connection failed - Backend not running on wss://192.168.48.201:8070`));
        };

        this.websocket.onclose = (event) => {
          clearTimeout(timeout);
          if (event.code !== 1000) {
            reject(new Error(`WebSocket closed during connection: Code ${event.code}, Reason: ${event.reason}`));
          }
        };
      });
      
    } catch (error) {
      console.error('❌ WebSocket setup failed:', error);
      throw new Error(`Connection setup failed: ${error.message}`);
    }
  }

  setupEventHandlers() {
    if (!this.websocket) return;

    this.websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('📨 Received message type:', data.type);
        
        if (this.eventHandlers.onMessage) {
          this.eventHandlers.onMessage(data);
        }
        
      } catch (error) {
        console.error('❌ Message parsing error:', error);
        throw new Error(`Failed to parse WebSocket message: ${error.message}`);
      }
    };
    
    this.websocket.onerror = (error) => {
      console.error('❌ WebSocket runtime error:', error);
      this.isConnected = false;
      
      if (this.eventHandlers.onError) {
        this.eventHandlers.onError(new Error(`WebSocket runtime error: ${error.message || 'Unknown error'}`));
      }
    };
    
    this.websocket.onclose = (event) => {
      console.log('🔌 WebSocket closed:', event.code, event.reason);
      this.isConnected = false;
      
      if (this.eventHandlers.onClose) {
        this.eventHandlers.onClose(event);
      }
    };
  }

  sendAudioData(audioBlob) {
    if (!this.isConnected || !this.websocket) {
      throw new Error('WebSocket not connected - cannot send audio data');
    }

    const reader = new FileReader();
    reader.onload = () => {
      try {
        const base64Audio = reader.result.split(',')[1];
        const message = {
          type: 'audio_data',
          audio: base64Audio
        };
        this.websocket.send(JSON.stringify(message));
        console.log('📤 Audio data sent to backend via WebSocket');
      } catch (error) {
        console.error('❌ Failed to send audio data:', error);
        throw new Error(`Audio transmission failed: ${error.message}`);
      }
    };
    
    reader.onerror = (error) => {
      console.error('❌ FileReader error:', error);
      throw new Error(`Audio encoding failed: ${error.message}`);
    };
    
    reader.readAsDataURL(audioBlob);
  }

  sendPing() {
    if (this.isConnected && this.websocket) {
      try {
        this.websocket.send(JSON.stringify({ type: 'ping' }));
      } catch (error) {
        console.error('❌ Ping failed:', error);
      }
    }
  }

  disconnect() {
    if (this.websocket) {
      this.websocket.close(1000, 'Normal closure');
      this.websocket = null;
    }
    this.isConnected = false;
    console.log('🔌 WebSocket disconnected');
  }
}

// Main Ultra-Fast API Service - NO FALLBACKS, REAL ERRORS ONLY
class realisticStandupAPIService {
  constructor() {
    this.wsManager = new UltraFastWebSocketManager();
    this.audioManager = new UltraFastAudioManager();
    this.currentSessionId = null;
    this.conversationState = 'idle'; // idle, listening, speaking, processing, complete
    this.audioChunksBuffer = [];
    this.pingInterval = null;
  }

  async startStandup() {
    try {
      console.log('🚀 Starting ultra-fast standup conversation...');
      
      // Get session from backend - NO FALLBACKS
      const response = await assessmentApiRequest('/daily_standup/start_test', {
        method: 'GET'
      });
      
      if (!response) {
        throw new Error('Backend returned empty response - check if server is running');
      }
      
      if (!response.session_id) {
        throw new Error(`Backend response missing session_id: ${JSON.stringify(response)}`);
      }
      
      this.currentSessionId = response.session_id;
      console.log('✅ Session created with ID:', this.currentSessionId);
      
      // Connect WebSocket using session_id (NOT test_id)
      await this.wsManager.connect(this.currentSessionId);
      
      // Setup WebSocket event handlers
      this.wsManager.setEventHandlers({
        onMessage: (data) => this.handleServerMessage(data),
        onError: (error) => this.handleConnectionError(error),
        onClose: (event) => this.handleConnectionClose(event)
      });
      
      // Setup automatic voice recording
      this.audioManager.onRecordingComplete = (audioBlob) => {
        this.handleAudioRecorded(audioBlob);
      };
      
      this.audioManager.onSpeechStart = () => {
        this.conversationState = 'listening';
        console.log('👂 User started speaking...');
      };
      
      // Start ultra-fast listening for user voice
      await this.audioManager.startListening();
      
      // Setup periodic ping to keep connection alive
      this.pingInterval = setInterval(() => {
        this.wsManager.sendPing();
      }, 30000); // Ping every 30 seconds
      
      console.log('✅ Ultra-fast conversation ready - speak naturally!');
      
      return {
        test_id: response.test_id,
        session_id: this.currentSessionId,
        status: 'ready',
        summary_chunks: response.summary_chunks || 0
      };
      
    } catch (error) {
      console.error('❌ Startup failed:', error);
      throw error; // NO FALLBACKS - Let the error bubble up for debugging
    }
  }

  handleServerMessage(data) {
    try {
      switch (data.type) {
        case 'ai_response':
          console.log('🤖 AI Response:', data.text);
          this.conversationState = 'speaking';
          this.audioChunksBuffer = [];
          break;
          
        case 'audio_chunk':
          // Collect audio chunks for seamless playback
          if (data.audio) {
            try {
              const binaryData = new Uint8Array(
                data.audio.match(/.{1,2}/g).map(byte => parseInt(byte, 16))
              );
              this.audioChunksBuffer.push(binaryData);
            } catch (error) {
              console.error('❌ Audio chunk processing failed:', error);
              throw new Error(`Audio chunk decode failed: ${error.message}`);
            }
          }
          break;
          
        case 'audio_end':
          console.log('🎵 AI finished speaking, playing response...');
          this.playAIResponseFast();
          break;
          
        case 'conversation_end':
          console.log('🏁 Conversation completed');
          this.handleConversationEnd(data);
          break;
          
        case 'clarification':
          console.log('❓ AI needs clarification:', data.text);
          this.conversationState = 'speaking';
          this.audioChunksBuffer = [];
          break;
          
        case 'error':
          console.error('❌ Server error:', data.text);
          throw new Error(`Backend error: ${data.text}`);
          
        case 'pong':
          // Heartbeat response
          break;
          
        default:
          console.warn('⚠️ Unknown message type:', data.type);
      }
    } catch (error) {
      console.error('❌ Message handling failed:', error);
      throw error;
    }
  }

  async playAIResponseFast() {
    try {
      this.conversationState = 'speaking';
      
      // Stop voice detection while AI is speaking
      this.audioManager.vad.stopListening();
      
      // Play all collected audio chunks FAST
      if (this.audioChunksBuffer.length > 0) {
        await this.audioManager.playAudioStream(this.audioChunksBuffer);
      } else {
        console.warn('⚠️ No audio chunks received from backend');
      }
      
      // IMMEDIATELY restart voice detection - NO DELAY!
      this.conversationState = 'idle';
      console.log('✅ AI finished, restarting ultra-fast voice detection NOW');
      
      // Restart voice detection immediately
      setTimeout(() => {
        if (this.conversationState !== 'complete') {
          this.audioManager.vad.startListening();
        }
      }, 100); // Minimal 100ms delay for audio cleanup
      
    } catch (error) {
      console.error('❌ Audio playback failed:', error);
      this.conversationState = 'idle';
      // Still restart voice detection even on error
      setTimeout(() => {
        if (this.conversationState !== 'complete') {
          this.audioManager.vad.startListening();
        }
      }, 100);
      throw error;
    }
  }

  async handleAudioRecorded(audioBlob) {
    try {
      this.conversationState = 'processing';
      console.log('📤 Sending audio to AI backend...');
      
      // IMMEDIATELY stop voice detection while processing
      this.audioManager.vad.stopListening();
      
      // Validate audio size
      if (audioBlob.size < 500) {
        throw new Error(`Audio blob too small: ${audioBlob.size} bytes`);
      }
      
      // Send audio to server via WebSocket
      this.wsManager.sendAudioData(audioBlob);
      
    } catch (error) {
      console.error('❌ Failed to send audio:', error);
      this.conversationState = 'idle';
      // Restart voice detection on error
      setTimeout(() => {
        this.audioManager.vad.startListening();
      }, 100);
      throw error;
    }
  }

  handleConnectionError(error) {
    console.error('❌ Connection error:', error);
    this.cleanup();
    throw new Error(`Connection lost: ${error.message}`);
  }

  handleConnectionClose(event) {
    if (event.code !== 1000) {
      console.error('❌ Connection closed unexpectedly:', event.code, event.reason);
      this.cleanup();
      throw new Error(`Connection closed unexpectedly: Code ${event.code}, Reason: ${event.reason}`);
    }
    console.log('✅ Connection closed normally');
  }

  handleConversationEnd(data) {
    this.conversationState = 'complete';
    console.log('✅ Standup completed successfully');
    
    // Stop listening
    this.audioManager.stopListening();
    
    // Clear ping interval
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
    
    // Return completion data
    return {
      evaluation: data.evaluation,
      score: data.score,
      summary: data.text
    };
  }

  getConversationState() {
    return this.conversationState;
  }

  cleanup() {
    this.audioManager.stopListening();
    this.wsManager.disconnect();
    
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
    
    this.conversationState = 'idle';
    console.log('🧹 Service cleanup completed');
  }

  disconnect() {
    this.cleanup();
  }
}

// Create singleton instance
const realisticStandupAPI = new realisticStandupAPIService();

// Export for compatibility
export const standupCallAPI = realisticStandupAPI;
export const dailyStandupAPI = realisticStandupAPI;
export default realisticStandupAPI;