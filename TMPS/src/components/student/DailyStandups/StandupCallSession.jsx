import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Alert,
  Card,
  CardContent,
  IconButton,
  Button,
  Avatar,
  LinearProgress,
  Chip,
  Fade,
  useTheme,
  alpha,
  styled,
  keyframes
} from '@mui/material';
import {
  Mic,
  VolumeUp,
  ArrowBack,
  CheckCircle,
  RadioButtonChecked,
  Timer,
  PlayArrow,
  Warning,
  RecordVoiceOver,
  Error as ErrorIcon,
  Speed
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { standupCallAPI } from '../../../services/API/studentstandup';

// ==================== ULTRA-FAST STYLED COMPONENTS ====================

const ultraFastPulse = keyframes`
  0% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.8);
  }
  70% {
    transform: scale(1.03);
    box-shadow: 0 0 0 15px rgba(76, 175, 80, 0);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(76, 175, 80, 0);
  }
`;

const fastSpeaking = keyframes`
  0%, 100% { 
    opacity: 1; 
    transform: scale(1);
  }
  50% { 
    opacity: 0.85; 
    transform: scale(1.08);
  }
`;

const ultraFastListening = keyframes`
  0%, 100% { 
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(244, 67, 54, 0.6);
  }
  50% { 
    transform: scale(1.015);
    box-shadow: 0 0 0 12px rgba(244, 67, 54, 0);
  }
`;

const MainAvatar = styled(Avatar)(({ theme, status }) => ({
  width: 200,
  height: 200,
  margin: '0 auto',
  marginBottom: theme.spacing(3),
  fontSize: '5rem',
  boxShadow: theme.shadows[16],
  border: `4px solid ${alpha(theme.palette.background.paper, 0.8)}`,
  transition: 'all 0.2s ease-in-out', // Faster transitions
  ...(status === 'listening' && {
    animation: `${ultraFastListening} 1.5s infinite`,
    backgroundColor: theme.palette.error.main,
    borderColor: theme.palette.error.light,
  }),
  ...(status === 'speaking' && {
    animation: `${fastSpeaking} 1.2s infinite`,
    backgroundColor: theme.palette.info.main,
    borderColor: theme.palette.info.light,
  }),
  ...(status === 'idle' && {
    animation: `${ultraFastPulse} 2s infinite`,
    backgroundColor: theme.palette.success.main,
    borderColor: theme.palette.success.light,
  }),
  ...(status === 'complete' && {
    backgroundColor: theme.palette.primary.main,
    borderColor: theme.palette.primary.light,
  }),
  ...(status === 'error' && {
    backgroundColor: theme.palette.error.main,
    borderColor: theme.palette.error.dark,
  }),
}));

const StatusCard = styled(Card, {
  shouldForwardProp: (prop) => prop !== 'isActive',
})(({ theme, isActive }) => ({
  borderRadius: 20,
  overflow: 'hidden',
  background: isActive 
    ? `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})` 
    : `linear-gradient(135deg, ${alpha(theme.palette.grey[100], 0.8)}, ${alpha(theme.palette.grey[50], 0.8)})`,
  border: isActive 
    ? `2px solid ${theme.palette.primary.main}` 
    : `1px solid ${alpha(theme.palette.grey[300], 0.5)}`,
  boxShadow: isActive ? theme.shadows[8] : theme.shadows[2],
  transition: 'all 0.2s ease-in-out', // Faster transitions
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: theme.shadows[12]
  }
}));

// ==================== ULTRA-FAST MAIN COMPONENT ====================

const StandupCallSession = () => {
  const { testId } = useParams();
  const navigate = useNavigate();
  const theme = useTheme();
  
  // ==================== ULTRA-FAST STATE MANAGEMENT ====================
  
  const [sessionState, setSessionState] = useState('initializing'); 
  const [error, setError] = useState(null);
  const [currentMessage, setCurrentMessage] = useState('');
  const [sessionDuration, setSessionDuration] = useState(0);
  const [conversationCount, setConversationCount] = useState(0);
  const [realSessionId, setRealSessionId] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [summaryChunks, setSummaryChunks] = useState(0);
  const [processingTime, setProcessingTime] = useState(0);
  
  // ==================== ULTRA-FAST REFS ====================
  
  const sessionStartTime = useRef(null);
  const durationTimerRef = useRef(null);
  const isInitialized = useRef(false);
  const processingStartTime = useRef(null);
  
  // ==================== ULTRA-FAST EFFECTS ====================
  
  useEffect(() => {
    if (!isInitialized.current) {
      isInitialized.current = true;
      initializeUltraFastSession();
    }
    
    return () => {
      cleanup();
    };
  }, []);
  
  useEffect(() => {
    if (sessionState === 'connecting' && !durationTimerRef.current) {
      sessionStartTime.current = Date.now();
      durationTimerRef.current = setInterval(() => {
        setSessionDuration(Math.floor((Date.now() - sessionStartTime.current) / 1000));
      }, 1000);
    }
  }, [sessionState]);
  
  // ==================== ULTRA-FAST MAIN FUNCTIONS ====================
  
  const initializeUltraFastSession = async () => {
    try {
      setSessionState('initializing');
      setError(null);
      setCurrentMessage('Initializing ultra-fast session...');
      
      console.log('🚀 Initializing ultra-fast standup session...');
      
      // NO ARTIFICIAL DELAYS - Initialize immediately
      setSessionState('ready');
      setCurrentMessage('Ready to start ultra-fast conversation');
      
    } catch (error) {
      console.error('❌ Session initialization error:', error);
      setError(error.message);
      setSessionState('error');
    }
  };
  
  const startUltraFastConversation = async () => {
    try {
      setSessionState('connecting');
      setError(null);
      setCurrentMessage('Connecting to ultra-fast AI backend...');
      
      console.log('🚀 Starting ultra-fast conversation...');
      
      // Start the standup with ultra-fast backend
      const response = await standupCallAPI.startStandup();
      
      if (!response) {
        throw new Error('No response from backend - check if server is running');
      }
      
      if (!response.session_id) {
        throw new Error(`Backend response missing session_id: ${JSON.stringify(response)}`);
      }
      
      setRealSessionId(response.session_id);
      setSummaryChunks(response.summary_chunks || 0);
      setIsConnected(true);
      setSessionState('idle');
      setCurrentMessage('Connected! AI will speak automatically...');
      setConversationCount(0);
      
      console.log('✅ Ultra-fast conversation started:', {
        testId: response.test_id,
        sessionId: response.session_id,
        summaryChunks: response.summary_chunks
      });
      
    } catch (error) {
      console.error('❌ Error starting ultra-fast conversation:', error);
      setError(`Backend connection failed: ${error.message}`);
      setSessionState('error');
    }
  };
  
  // ==================== ULTRA-FAST WEBSOCKET HANDLERS ====================
  
  const handleWebSocketMessage = (data) => {
    console.log('📨 WebSocket message:', data.type, data.status);
    
    // Track processing time for performance monitoring
    if (data.type === 'ai_response' && processingStartTime.current) {
      const elapsed = Date.now() - processingStartTime.current;
      setProcessingTime(elapsed);
      console.log(`⚡ AI response time: ${elapsed}ms`);
    }
    
    switch (data.type) {
      case 'ai_response':
        handleAIResponse(data);
        break;
        
      case 'audio_chunk':
        // Audio chunks are handled automatically by the API
        break;
        
      case 'audio_end':
        handleAudioEnd(data);
        break;
        
      case 'conversation_end':
        handleConversationEnd(data);
        break;
        
      case 'clarification':
        handleClarificationRequest(data);
        break;
        
      case 'error':
        handleServerError(data);
        break;
        
      case 'pong':
        // Heartbeat response - connection is alive
        break;
        
      default:
        console.warn('⚠️ Unknown message type:', data.type);
    }
  };
  
  const handleAIResponse = (data) => {
    console.log('🤖 AI Response received:', data.text);
    
    setCurrentMessage(data.text);
    setSessionState('speaking');
    setConversationCount(prev => prev + 1);
    
    // Reset processing timer
    processingStartTime.current = null;
  };
  
  const handleAudioEnd = (data) => {
    console.log('🎵 Audio ended, voice detection will restart automatically...');
    
    // Automatically transition to listening state after minimal delay
    setTimeout(() => {
      if (sessionState !== 'complete' && sessionState !== 'error') {
        setSessionState('idle');
        setCurrentMessage('Your turn - speak naturally, I\'ll detect when you\'re done');
        
        // Track when user starts speaking for performance monitoring
        processingStartTime.current = Date.now();
      }
    }, 200); // Ultra-fast 200ms transition
  };
  
  const handleConversationEnd = (data) => {
    console.log('🏁 Conversation ended');
    
    setCurrentMessage(data.text || 'Ultra-fast standup completed successfully!');
    setSessionState('complete');
    
    // Auto-navigate to summary after brief delay
    setTimeout(() => {
      if (realSessionId) {
        navigate(`/student/daily-standups/summary/${realSessionId}`);
      } else if (testId) {
        navigate(`/student/daily-standups/summary/${testId}`);
      }
    }, 2000); // Faster navigation
  };
  
  const handleClarificationRequest = (data) => {
    console.log('❓ AI needs clarification:', data.text);
    
    setCurrentMessage(data.text);
    setSessionState('speaking');
    
    // Quickly transition back to listening after clarification
    setTimeout(() => {
      setSessionState('idle');
      setCurrentMessage('Please speak more clearly');
    }, 1000);
  };
  
  const handleServerError = (data) => {
    console.error('❌ Server error:', data.text);
    setError(`Backend error: ${data.text}`);
    setSessionState('error');
  };
  
  const handleWebSocketError = (error) => {
    console.error('❌ WebSocket error:', error);
    setError(`Connection error: ${error.message}`);
    setSessionState('error');
    setIsConnected(false);
  };
  
  const handleWebSocketClose = (event) => {
    console.log('🔌 WebSocket closed:', event.code, event.reason);
    setIsConnected(false);
    
    if (sessionState !== 'complete' && event.code !== 1000) {
      setError(`Connection lost: Code ${event.code}, Reason: ${event.reason || 'Unknown'}`);
      setSessionState('error');
    }
  };
  
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  
  const getStatusMessage = () => {
    switch (sessionState) {
      case 'initializing':
        return 'Initializing ultra-fast system...';
      case 'ready':
        return 'Ready to start ultra-fast conversation';
      case 'connecting':
        return 'Connecting to AI backend...';
      case 'idle':
        return 'Listening for your voice (800ms detection)';
      case 'listening':
        return 'Recording your response';
      case 'speaking':
        return 'AI is responding';
      case 'processing':
        return 'Processing ultra-fast...';
      case 'complete':
        return 'Ultra-fast standup completed!';
      case 'error':
        return 'Connection Error - Check Backend';
      default:
        return 'Loading...';
    }
  };
  
  const getStatusIcon = () => {
    switch (sessionState) {
      case 'listening':
        return <Mic fontSize="inherit" />;
      case 'speaking':
        return <VolumeUp fontSize="inherit" />;
      case 'processing':
        return <Speed fontSize="inherit" />;
      case 'complete':
        return <CheckCircle fontSize="inherit" />;
      case 'error':
        return <ErrorIcon fontSize="inherit" />;
      case 'idle':
        return <RecordVoiceOver fontSize="inherit" />;
      default:
        return <RadioButtonChecked fontSize="inherit" />;
    }
  };
  
  const getStatusColor = () => {
    switch (sessionState) {
      case 'complete':
        return 'success';
      case 'error':
        return 'error';
      case 'listening':
        return 'warning';
      case 'speaking':
        return 'info';
      case 'processing':
        return 'secondary';
      default:
        return 'primary';
    }
  };
  
  const cleanup = () => {
    console.log('🧹 Cleaning up ultra-fast session...');
    
    if (durationTimerRef.current) {
      clearInterval(durationTimerRef.current);
      durationTimerRef.current = null;
    }
    
    standupCallAPI.disconnect();
  };
  
  const handleGoBack = () => {
    cleanup();
    navigate('/student/daily-standups');
  };
  
  const handleRetry = () => {
    setError(null);
    setSessionState('ready');
    setCurrentMessage('');
    setConversationCount(0);
    setSessionDuration(0);
    setProcessingTime(0);
    setIsConnected(false);
  };
  
  // ==================== ULTRA-FAST RENDER ====================
  
  return (
    <Fade in={true}>
      <Box sx={{ p: 3, minHeight: '100vh', backgroundColor: alpha(theme.palette.primary.main, 0.02) }}>
        {/* Ultra-Fast Header */}
        <Box 
          display="flex" 
          justifyContent="space-between" 
          alignItems="center" 
          mb={4}
          sx={{
            background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
            p: 3,
            borderRadius: 3,
            backdropFilter: 'blur(10px)',
            border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
          }}
        >
          <Box display="flex" alignItems="center" gap={2}>
            <IconButton onClick={handleGoBack} sx={{ mr: 1 }}>
              <ArrowBack />
            </IconButton>
            <Avatar 
              sx={{ 
                bgcolor: sessionState === 'complete' ? theme.palette.success.main : 
                         sessionState === 'error' ? theme.palette.error.main :
                         theme.palette.primary.main,
                width: 56,
                height: 56,
                boxShadow: theme.shadows[8]
              }}
            >
              {getStatusIcon()}
            </Avatar>
            <Box>
              <Typography 
                variant="h5" 
                component="h1"
                sx={{
                  background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  fontWeight: 'bold'
                }}
              >
                Ultra-Fast Daily Standup
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {formatTime(sessionDuration)} 
                {realSessionId && ` • ${realSessionId.slice(-8)}`}
                {summaryChunks > 0 && ` • ${summaryChunks} topics`}
                {processingTime > 0 && ` • ${processingTime}ms response`}
              </Typography>
            </Box>
          </Box>
          
          <Box display="flex" alignItems="center" gap={1}>
            <Chip 
              label={getStatusMessage()}
              color={getStatusColor()}
              icon={getStatusIcon()}
              size="medium"
              variant={sessionState === 'error' ? 'filled' : 'outlined'}
            />
          </Box>
        </Box>

        {/* Ultra-Fast Error Display */}
        {error && (
          <Alert 
            severity="error" 
            sx={{ mb: 3, borderRadius: 2 }}
            action={
              <Button color="inherit" size="small" onClick={handleRetry}>
                Retry Connection
              </Button>
            }
          >
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              Ultra-Fast Backend Connection Failed
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              <strong>Error:</strong> {error}
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              <strong>Troubleshooting:</strong>
            </Typography>
            <Box component="ul" sx={{ mt: 1, pl: 2 }}>
              <li>Check if backend server is running on http://192.168.48.201:8070</li>
              <li>Verify WebSocket endpoint: ws://192.168.48.201:8070/daily_standup/ws/</li>
              <li>Check network connectivity and firewall settings</li>
              <li>Ensure MongoDB and SQL Server connections are active</li>
            </Box>
          </Alert>
        )}

        {/* Performance Metrics */}
        {isConnected && (
          <Box sx={{ mb: 3 }}>
            <Card sx={{ p: 2, bgcolor: alpha(theme.palette.success.main, 0.1) }}>
              <Typography variant="h6" color="success.main" gutterBottom>
                ⚡ Ultra-Fast Performance Metrics
              </Typography>
              <Box display="flex" gap={3} flexWrap="wrap">
                <Typography variant="body2">
                  <strong>Voice Detection:</strong> 800ms silence threshold
                </Typography>
                <Typography variant="body2">
                  <strong>Conversations:</strong> {conversationCount}
                </Typography>
                <Typography variant="body2">
                  <strong>Summary Topics:</strong> {summaryChunks}
                </Typography>
                {processingTime > 0 && (
                  <Typography variant="body2">
                    <strong>Last Response Time:</strong> {processingTime}ms
                  </Typography>
                )}
              </Box>
            </Card>
          </Box>
        )}

        {/* Ultra-Fast Main Interface */}
        <StatusCard isActive={sessionState !== 'ready' && sessionState !== 'error'} elevation={8}>
          <CardContent sx={{ p: 6, textAlign: 'center' }}>
            
            {/* Ultra-Fast Main Avatar */}
            <MainAvatar status={sessionState}>
              {getStatusIcon()}
            </MainAvatar>
            
            {/* Ultra-Fast Status Message */}
            <Typography 
              variant="h4" 
              gutterBottom 
              sx={{ 
                mb: 3,
                fontWeight: 'bold',
                background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              {getStatusMessage()}
            </Typography>
            
            {/* Current AI Message */}
            {currentMessage && sessionState !== 'ready' && (
              <Box sx={{ mb: 4, maxWidth: 600, mx: 'auto' }}>
                <Typography 
                  variant="h6" 
                  sx={{ 
                    mb: 2,
                    fontStyle: sessionState === 'speaking' ? 'italic' : 'normal',
                    color: sessionState === 'speaking' ? theme.palette.info.main : theme.palette.text.primary,
                    lineHeight: 1.6,
                    fontSize: '1.1rem'
                  }}
                >
                  {sessionState === 'speaking' ? `"${currentMessage}"` : currentMessage}
                </Typography>
              </Box>
            )}
            
            {/* Ultra-Fast Visual Indicators */}
            <Box sx={{ mb: 4 }}>
              {sessionState === 'speaking' && (
                <Box>
                  <Typography variant="h5" color="info.main" sx={{ mb: 2, fontWeight: 'bold' }}>
                    🎧 AI SPEAKING (Ultra-Fast TTS)
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Listen to my response... I'll detect when you start talking in 800ms
                  </Typography>
                </Box>
              )}
              
              {sessionState === 'idle' && isConnected && (
                <Box>
                  <Typography variant="h5" color="success.main" sx={{ mb: 2, fontWeight: 'bold' }}>
                    👂 ULTRA-FAST LISTENING (800ms Detection)
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Speak naturally - Ultra-fast silence detection active (800ms threshold)
                  </Typography>
                  <LinearProgress 
                    variant="indeterminate" 
                    color="success" 
                    sx={{ mt: 2, height: 6, borderRadius: 3 }}
                  />
                </Box>
              )}
              
              {sessionState === 'connecting' && (
                <Box>
                  <Typography variant="h5" color="primary.main" sx={{ mb: 2, fontWeight: 'bold' }}>
                    🔄 CONNECTING TO ULTRA-FAST BACKEND
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Establishing WebSocket connection to AI interviewer...
                  </Typography>
                  <LinearProgress 
                    variant="indeterminate" 
                    color="primary" 
                    sx={{ mt: 2, height: 6, borderRadius: 3 }}
                  />
                </Box>
              )}
              
              {sessionState === 'processing' && (
                <Box>
                  <Typography variant="h5" color="secondary.main" sx={{ mb: 2, fontWeight: 'bold' }}>
                    ⚡ ULTRA-FAST PROCESSING
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    AI is generating response using summary-based questions...
                  </Typography>
                  <LinearProgress 
                    variant="indeterminate" 
                    color="secondary" 
                    sx={{ mt: 2, height: 6, borderRadius: 3 }}
                  />
                </Box>
              )}
            </Box>
            
            {/* Ultra-Fast Action Buttons */}
            <Box sx={{ mb: 4 }}>
              {sessionState === 'ready' && (
                <Button
                  variant="contained"
                  size="large"
                  onClick={startUltraFastConversation}
                  startIcon={<PlayArrow />}
                  sx={{ 
                    px: 4, 
                    py: 2, 
                    fontSize: '1.2rem',
                    borderRadius: 3,
                    background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                    boxShadow: theme.shadows[8],
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: theme.shadows[12]
                    }
                  }}
                >
                  Start Ultra-Fast Conversation
                </Button>
              )}
              
              {sessionState === 'complete' && (
                <Typography variant="h6" color="success.main" sx={{ fontWeight: 'bold' }}>
                  ✅ Redirecting to ultra-fast summary...
                </Typography>
              )}
              
              {sessionState === 'error' && (
                <Button
                  variant="contained"
                  color="error"
                  onClick={handleRetry}
                  startIcon={<ErrorIcon />}
                  sx={{ mr: 2 }}
                >
                  Retry Connection
                </Button>
              )}
            </Box>
            
            {/* Ultra-Fast Instructions */}
            <Box 
              sx={{ 
                mt: 4, 
                p: 3, 
                backgroundColor: alpha(theme.palette.info.main, 0.05),
                borderRadius: 2,
                border: `1px solid ${alpha(theme.palette.info.main, 0.2)}`
              }}
            >
              <Typography variant="h6" color="info.main" gutterBottom>
                ⚡ Ultra-Fast Conversation Features:
              </Typography>
              <Box sx={{ textAlign: 'left', maxWidth: 600, mx: 'auto' }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  <strong>🚀 800ms Silence Detection:</strong> Fastest voice detection for minimal delays
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  <strong>🤖 Summary-Based Questions:</strong> AI asks questions from real project summaries
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  <strong>🎙️ Auto Voice Detection:</strong> No manual controls - speaks naturally
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  <strong>⚡ Parallel Processing:</strong> Ultra-fast transcription and response generation
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>🔄 Real-time Streaming:</strong> Audio streams while AI generates next response
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </StatusCard>

        {/* Development Debug Panel */}
        {process.env.NODE_ENV === 'development' && (
          <Box sx={{ mt: 3 }}>
            <Card sx={{ p: 2, bgcolor: alpha(theme.palette.warning.main, 0.1) }}>
              <Typography variant="h6" color="warning.main" gutterBottom>
                🛠️ Development Debug Panel
              </Typography>
              <Box sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                <div>Session State: {sessionState}</div>
                <div>Test ID: {testId}</div>
                <div>Real Session ID: {realSessionId}</div>
                <div>Is Connected: {isConnected.toString()}</div>
                <div>Conversation Count: {conversationCount}</div>
                <div>Summary Chunks: {summaryChunks}</div>
                <div>Processing Time: {processingTime}ms</div>
                <div>Current Message: {currentMessage.substring(0, 50)}...</div>
              </Box>
            </Card>
          </Box>
        )}
      </Box>
    </Fade>
  );
};

export default StandupCallSession;