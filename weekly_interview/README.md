# Mock Interview Module - AI-Powered Real-Time Interview System

![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)
![Status](https://img.shields.io/badge/status-production--ready-green.svg)
![Frontend](https://img.shields.io/badge/frontend-React%2018-61dafb.svg)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688.svg)
![Database](https://img.shields.io/badge/database-MongoDB%20%2B%20MySQL-47a248.svg)

## 🎯 **Purpose & Vision**

The Mock Interview Module is an **AI-powered, real-time interview simulation system** designed to provide students with realistic interview practice using their actual project work and learning history. The system leverages **7-day content summaries** to generate personalized, relevant interview questions while maintaining professional interview standards.

### **Key Objectives:**
- 🎤 **Realistic Practice**: Real-time audio interaction simulating actual interview conditions
- 📊 **Intelligent Assessment**: AI-driven evaluation across technical, communication, and behavioral dimensions
- 📚 **Personalized Content**: Questions based on user's recent work and learning activities
- 🔄 **Continuous Improvement**: Comprehensive feedback and performance tracking

## 🏗️ **System Architecture**

### **High-Level Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Databases     │
│   (React)       │◄──►│   (FastAPI)     │◄──►│ MongoDB + MySQL │
│                 │    │                 │    │                 │
│ • MockInterviews│    │ • WebSocket     │    │ • 7-day summaries│
│ • StartInterview│    │ • Audio Process │    │ • Student data   │
│ • Results       │    │ • AI Services   │    │ • Interview logs │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  AI Services    │
                    │ • OpenAI GPT-4  │
                    │ • Groq Whisper  │
                    │ • EdgeTTS       │
                    └─────────────────┘
```

### **Design Patterns Used**

1. **Daily Standup Style Architecture**: 
   - Ultra-fast processing with minimal latency
   - Fragment-based content management
   - Real-time streaming communication

2. **Microservice Communication**:
   - RESTful APIs for state management
   - WebSocket for real-time interaction
   - Service-oriented architecture

3. **Event-Driven Processing**:
   - Async audio processing pipeline
   - Real-time state updates
   - Non-blocking UI interactions

## 🌊 **Complete System Flow**

### **Phase 1: Interview Initialization**
```
1. Student Navigation
   └── /student/mock-interviews
       └── MockInterviews.jsx renders dashboard
           └── System health check (/weekly_interview/health)
           └── Load previous interview statistics
           └── Display "Start Interview" interface

2. Interview Start Request
   └── User clicks "Start Interview"
       └── interviewOperationsAPI.startInterview()
           └── POST /weekly_interview/start_interview
               └── Backend creates session with 7-day summaries
               └── Returns {test_id, session_id, websocket_url}

3. Navigation to Interview Session
   └── navigate(`/student/mock-interviews/session/${testId}`)
       └── StartInterview.jsx component loads
           └── Initialize WebSocket connection
           └── Test microphone permissions
```

### **Phase 2: Real-Time Interview Execution**
```
4. WebSocket Connection Establishment
   └── ws://192.168.48.201:8070/weekly_interview/ws/{sessionId}
       └── Backend processes 7-day summaries into fragments
       └── AI generates personalized greeting question
       └── Streams greeting audio to frontend

5. Interactive Interview Rounds
   └── Round 1: Greeting (2 questions)
   └── Round 2: Technical (6 questions) - Based on 7-day summaries
   └── Round 3: Communication (6 questions) - Presentation skills
   └── Round 4: HR/Behavioral (6 questions) - Cultural fit

6. Real-Time Audio Processing Pipeline
   └── User speaks → Audio recorded (30s max with auto-stop)
       └── Base64 encoding → WebSocket transmission
           └── Groq Whisper transcription (ultra-fast)
               └── OpenAI GPT-4 response generation
                   └── EdgeTTS audio synthesis
                       └── Chunked audio streaming to frontend
```

### **Phase 3: Evaluation & Results**
```
7. Interview Completion
   └── All rounds completed OR manual completion
       └── Comprehensive evaluation generation
           └── MongoDB storage with full analytics
               └── Navigate to results page

8. Results Display & Export
   └── /student/mock-interviews/results/{testId}
       └── InterviewResultsComponent.jsx
           └── Performance scores visualization
           └── PDF report generation & download
           └── Detailed feedback and recommendations
```

## 💾 **Data Architecture**

### **MongoDB Collections**

#### **1. Summaries Collection** (`ml_notes.summaries`)
```javascript
{
  "_id": ObjectId,
  "summary": "7-day content summary text",
  "timestamp": 1640995200.0,
  "date": "2024-01-01",
  "session_id": "session_123"
}
```

#### **2. Interview Results Collection** (`ml_notes.interview_results`)
```javascript
{
  "test_id": "interview_1640995200",
  "session_id": "session_uuid",
  "student_id": 12345,
  "student_name": "John Doe",
  "timestamp": 1640995200.0,
  "conversation_log": [
    {
      "timestamp": 1640995200.0,
      "stage": "technical",
      "ai_message": "Can you explain...",
      "user_response": "I would approach...",
      "transcript_quality": 0.95,
      "concept": "Fragment Topic 1",
      "is_followup": false
    }
  ],
  "evaluation": "Comprehensive evaluation text...",
  "scores": {
    "technical_score": 8.5,
    "communication_score": 7.8,
    "behavioral_score": 8.2,
    "overall_score": 8.1,
    "weighted_overall": 8.16
  },
  "interview_analytics": {
    "total_duration_minutes": 45.2,
    "questions_per_round": {
      "greeting": 2,
      "technical": 6,
      "communication": 6,
      "hr": 6
    },
    "followup_questions": 3,
    "fragments_covered": 8,
    "total_fragments": 10,
    "fragment_coverage_percentage": 80.0,
    "rounds_completed": 4,
    "interview_completion_status": "complete"
  }
}
```

### **MySQL Tables**

#### **Student Information** (`tbl_Student`)
```sql
CREATE TABLE tbl_Student (
  ID INT PRIMARY KEY,
  First_Name VARCHAR(255),
  Last_Name VARCHAR(255),
  Email VARCHAR(255),
  -- Additional student fields
);
```

## 🔧 **Technology Stack**

### **Frontend (React 18)**
- **Framework**: React 18 with functional components and hooks
- **Routing**: React Router v6 with nested routes
- **UI Library**: Material-UI v5 with custom theming
- **State Management**: React hooks (useState, useEffect, useContext)
- **HTTP Client**: Fetch API with custom service layers
- **WebSocket**: Native WebSocket API with reconnection logic
- **Audio**: Web Audio API for recording and playback

### **Backend (FastAPI)**
- **Framework**: FastAPI with async/await for high performance
- **WebSocket**: Real-time communication with connection management
- **Audio Processing**: Groq Whisper for transcription
- **AI Services**: OpenAI GPT-4 for conversation and evaluation
- **TTS**: EdgeTTS for ultra-fast audio synthesis
- **Database**: Motor (async MongoDB) + mysql-connector-python
- **PDF Generation**: ReportLab for evaluation reports

### **AI & External Services**
- **Transcription**: Groq Whisper (distil-whisper-large-v3-en)
- **Conversation AI**: OpenAI GPT-4-mini with optimized prompts
- **Text-to-Speech**: Microsoft EdgeTTS (en-IN-PrabhatNeural)
- **Content Processing**: 7-day summary analysis with fragment extraction

### **Infrastructure**
- **Development**: Hot reload with Uvicorn (FastAPI) + Vite (React)
- **Production**: HTTPS with SSL certificates
- **Network**: Cross-platform access (Linux server → Windows client)
- **Storage**: File-based audio processing with cleanup

## 📂 **File Structure**

```
TMPS/                                           # Frontend React Application
├── src/
│   ├── components/student/MockInterviews/
│   │   ├── MockInterviews.jsx                 # 🏠 Main dashboard component
│   │   ├── StartInterview.jsx                 # 🎤 Real-time interview session
│   │   └── InterviewResultsComponent.jsx     # 📊 Results display & PDF download
│   ├── services/API/
│   │   ├── index2.js                         # 🔧 Core API & WebSocket manager
│   │   ├── studentmockinterview.js           # 🎯 Interview operations API
│   │   └── mockinterviews.js                 # 📈 Interview data API
│   └── App.jsx                               # 🛣️ Route definitions

APP/                                            # Backend FastAPI Application
├── weekly_interview/
│   ├── main.py                               # 🚀 FastAPI app & WebSocket endpoints
│   ├── core/
│   │   ├── ai_services.py                    # 🤖 AI processing & conversation management
│   │   ├── database.py                       # 💾 MongoDB & MySQL connections
│   │   ├── content_service.py                # 📚 7-day summary processing
│   │   └── config.py                         # ⚙️ Configuration management
│   └── __init__.py                           # 📦 Module exports
└── app.py                                      # 🏗️ Main application launcher
```

## 🚀 **Deployment Guide**

### **1. Environment Setup**

#### **Backend (.env file)**
```bash
# AI Service Keys
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
MYSQL_HOST=192.168.48.201
MYSQL_PORT=3306
MYSQL_DATABASE=SuperDB
MYSQL_USER=sa
MYSQL_PASSWORD=Welcome@123

MONGODB_HOST=192.168.48.201
MONGODB_PORT=27017
MONGODB_DATABASE=ml_notes
MONGODB_USERNAME=connectly
MONGODB_PASSWORD=LT@connect25

# Interview Configuration
RECENT_SUMMARIES_DAYS=7
SUMMARIES_LIMIT=10
QUESTIONS_PER_ROUND=6
INTERVIEW_DURATION_MINUTES=45

# TTS Configuration
TTS_VOICE=en-IN-PrabhatNeural
TTS_SPEED=+25%
```

#### **Frontend (environment variables)**
```bash
VITE_API_BASE_URL=https://192.168.48.201:8070
VITE_ASSESSMENT_API_URL=https://192.168.48.201:8070
```

### **2. Installation & Startup**

#### **Backend (Linux Server)**
```bash
cd APP
pip install -r requirements.txt

# Start with SSL (production)
python app.py

# Access at: https://192.168.48.201:8070
```

#### **Frontend (Any Platform)**
```bash
cd TMPS
npm install
npm start

# Development server: http://localhost:3000
# Production build: npm run build
```

### **3. Network Configuration**

The system is designed for **cross-platform network access**:

- **Backend**: Runs on Linux server (192.168.48.201:8070)
- **Frontend**: Can be accessed from any device on the network
- **WebSocket**: Supports both WS (HTTP) and WSS (HTTPS) protocols
- **CORS**: Configured for cross-origin requests

## 🔄 **API Documentation**

### **Core Endpoints**

#### **Interview Management**
```bash
# Start new interview session
GET /weekly_interview/start_interview
Response: {
  "test_id": "interview_1640995200",
  "session_id": "uuid-session-id",
  "websocket_url": "/weekly_interview/ws/session-id",
  "greeting": "Hello! Welcome to your interview...",
  "fragments_count": 8,
  "estimated_duration": 45
}

# Get interview evaluation
GET /weekly_interview/evaluate?test_id={testId}
Response: {
  "test_id": "interview_1640995200",
  "evaluation": "Comprehensive evaluation text...",
  "scores": {...},
  "analytics": {...}
}

# Download PDF report
GET /weekly_interview/download_results/{test_id}
Response: PDF file download
```

#### **WebSocket Communication**
```bash
# WebSocket endpoint
WSS /weekly_interview/ws/{session_id}

# Message types:
{
  "type": "audio_data",
  "audio": "base64_encoded_audio"
}

{
  "type": "ai_response", 
  "text": "Interview question...",
  "stage": "technical"
}

{
  "type": "audio_chunk",
  "audio": "hex_encoded_audio"
}

{
  "type": "interview_complete",
  "evaluation": "...",
  "scores": {...}
}
```

#### **Data APIs (Frontend Compatibility)**
```bash
# Get all interview students
GET /weekly_interview/api/interview-students

# Get student's interviews
GET /weekly_interview/api/interview-students/{student_id}/interviews
```

### **System Health**
```bash
GET /weekly_interview/health
Response: {
  "status": "healthy",
  "service": "ultra_fast_interview_system",
  "active_sessions": 3,
  "database_status": {
    "mysql": true,
    "mongodb": true
  },
  "features": {
    "7_day_summaries": true,
    "fragment_based_questions": true,
    "real_time_streaming": true,
    "ultra_fast_tts": true
  }
}
```

## 🎯 **Why This Architecture?**

### **1. Daily Standup Style Inspiration**
The architecture follows the **"Daily Standup" pattern** because:
- ⚡ **Ultra-fast processing**: Minimal latency for real-time interaction
- 🧩 **Fragment-based content**: Intelligent content slicing for relevant questions
- 🔄 **Streaming communication**: Continuous data flow without blocking
- 📊 **Rich analytics**: Comprehensive tracking and evaluation

### **2. Real-Time Requirements**
- **WebSocket Protocol**: Enables true real-time audio interaction
- **Async Processing**: Non-blocking operations for smooth UX
- **Streaming TTS**: Audio chunks delivered as they're generated
- **Connection Management**: Robust handling of network issues

### **3. AI-Driven Personalization**
- **7-Day Summaries**: Questions based on actual user work/learning
- **Fragment Processing**: Intelligent content extraction and slicing
- **Round-Aware AI**: Context-sensitive question generation
- **Quality Assessment**: Transcript quality-based response adaptation

### **4. Scalability Considerations**
- **Connection Pooling**: Efficient database resource usage
- **Thread Pool Management**: Concurrent request handling
- **Session Management**: Active session tracking and cleanup
- **Microservice Design**: Independent service scaling

### **5. Production Readiness**
- **Comprehensive Error Handling**: Graceful failure recovery
- **Health Monitoring**: Real-time system status tracking
- **SSL/HTTPS Support**: Secure communication protocols
- **Cross-Platform Support**: Universal device compatibility

## 📈 **Performance Metrics**

### **Expected Performance**
- **Interview Start Time**: < 3 seconds (7-day summary processing)
- **Audio Transcription**: < 2 seconds (Groq Whisper)
- **AI Response Generation**: < 3 seconds (OpenAI GPT-4)
- **Audio Synthesis**: < 1 second (EdgeTTS streaming)
- **Total Round-Trip**: < 8 seconds per interaction

### **Scalability Targets**
- **Concurrent Sessions**: 100+ active interviews
- **Database Load**: Optimized queries with connection pooling
- **Memory Usage**: Efficient fragment management
- **Network Bandwidth**: Compressed audio streaming

## 🛡️ **Security Features**

- **Input Validation**: Comprehensive request validation
- **Audio Processing**: Secure file handling with cleanup
- **Database Security**: Parameterized queries preventing injection
- **CORS Configuration**: Controlled cross-origin access
- **SSL/TLS**: Encrypted communication in production
- **Session Management**: Secure session handling and cleanup

## 🔮 **Future Enhancements**

### **Planned Features**
- **Interview Scheduling**: Calendar integration for practice sessions
- **Video Support**: Video call simulation with facial analysis
- **Custom Question Banks**: User-defined question categories
- **Performance Analytics**: Long-term progress tracking
- **Multi-Language Support**: Internationalization capabilities
- **Mobile App**: React Native mobile application

### **Technical Improvements**
- **Redis Caching**: Session state caching for better performance
- **Load Balancing**: Multiple backend instances
- **Database Sharding**: Horizontal scaling for large datasets
- **Advanced AI**: Fine-tuned models for domain-specific interviews
- **Real-time Collaboration**: Multi-interviewer support

## 🆘 **Troubleshooting Guide**

### **Common Issues**

#### **WebSocket Connection Failures**
```bash
# Check backend health
curl https://192.168.48.201:8070/weekly_interview/health

# Verify network connectivity
ping 192.168.48.201

# Check firewall settings
sudo ufw status
```

#### **Audio Processing Issues**
```bash
# Verify microphone permissions in browser
# Check browser compatibility (Chrome recommended)
# Ensure stable internet connection
# Test with different audio devices
```

#### **Database Connection Problems**
```bash
# Test MongoDB connection
mongo mongodb://connectly:LT@connect25@192.168.48.201:27017/admin

# Test MySQL connection
mysql -h 192.168.48.201 -u sa -p SuperDB
```

## 👥 **Contributing**

### **Development Workflow**
1. **Frontend Changes**: React hot reload for immediate feedback
2. **Backend Changes**: FastAPI auto-reload for API modifications
3. **Database Changes**: Migration scripts for schema updates
4. **AI Improvements**: Prompt engineering and model optimization

### **Code Standards**
- **Frontend**: ESLint + Prettier for consistent formatting
- **Backend**: Black + isort for Python code formatting
- **Documentation**: Comprehensive inline comments and README updates
- **Testing**: Unit tests for critical functionality

## 📄 **License & Credits**

**Mock Interview Module v3.0.0**
- Built with ❤️ using React, FastAPI, and modern AI services
- Inspired by daily standup methodology for ultra-fast processing
- Designed for educational and professional interview preparation

---

**🎉 Ready to revolutionize interview practice with AI-powered, real-time interaction!**