
# ?? FastAPI Multi-Module Interview & Testing System

A comprehensive AI-powered platform featuring voice-based interviews, mock tests, and daily standups. Built with FastAPI, MongoDB, LangChain, and OpenAI/Groq APIs, this system provides a complete solution for technical assessments, adaptive testing, and real-time evaluation.

---

## ?? Features

### ?? Daily Standup Module
- Voice-based adaptive questioning
- Whisper transcription (via Groq API)
- Text-to-speech feedback (Edge TTS)
- Real-time evaluation, silence detection
- PDF summary export

### ?? Weekend Mock Test Module
- Developer & Non-developer test modes
- Code questions, MCQs, adaptive logic
- PDF export and scoring analytics

### ?? Weekly Interview Module
- 3-round AI interview (Tech, Comm, HR)
- Realistic voice interaction
- Progressive difficulty & evaluation
- Round transitions and reports

---

## ??? Project Structure

```

+-- main.py                  # FastAPI main app
+-- requirements.txt
+-- Dockerfile
+-- docker-compose.yml
+-- .env                     # API keys
+-- yolo\_model/
�   +-- interview\_monitor.py
+-- static/index.html        # Landing UI
+-- daily\_standup/
�   +-- main.py
�   +-- index.html
+-- weekend\_mocktest/
�   +-- main.py
�   +-- frontend/index.html
+-- weekly\_interview/
+-- main.py
+-- frontend/index.html

````

---

## ?? Tech Stack

**Backend**
- FastAPI, MongoDB, LangChain
- Whisper (via Groq), OpenAI GPT-4
- Edge TTS, FFmpeg

**Frontend**
- HTML/JS + Tailwind CSS (where used)
- Web Audio API, real-time response UX

**Audio Tools**
- sounddevice, scipy, pydub
- FFmpeg for conversion/speed tuning

---

## ?? Prerequisites

- Python 3.8+ (Windows/Linux)
- MongoDB (local/cloud)
- FFmpeg installed & in PATH
- OpenAI and Groq API keys
- Microphone permission (Windows)

---

## ??? Setup (Linux)

### ? One-Step Script-Based Setup (Recommended)

```bash
git clone https://github.com/Sa1f27/Edu-app.git
cd Edu-app

sudo apt install dos2unix
dos2unix setup.sh
chmod +x setup.sh
./setup.sh
````
## for windows 

**Install FFmpeg**

```bash
choco install ffmpeg
# OR manually add to PATH from https://www.gyan.dev/ffmpeg/builds/
```

**Run the app**

```bash
uvicorn main:app --host 127.0.0.1 --port 8090 --reload
nginx -p C:\tools\nginx-1.29.0 -c conf\nginx.conf

```

Open browser: [http://localhost:8090](http://localhost:8090)

---

### ??? Docker Setup (No Python Needed)

**Steps:**

1. Install Docker Desktop
2. Add `.env` file with API keys:

```
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key
```

3. Run with Docker:

```bash
docker-compose up --build
```

Open: [http://localhost:8090](http://localhost:8090)

---

## ?? Docker Files

**Dockerfile**

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt \
 && pip install torch==2.6.0+cu118 torchvision==0.21.0+cu118 torchaudio==2.6.0+cu118 --index-url https://download.pytorch.org/whl/cu118
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"] || ["python", "main.py"]

```

**docker-compose.yml**

```yaml
version: '3.8'
services:
  interview_app:
    build: .
    ports:
      - "8090:8090"
    env_file:
      - .env
    depends_on:
      - mongo

  mongo:
    image: mongo:6.0
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
```

---

## ??? APIs (Selected)

**Daily Standup**

* `GET /daily_standup/`
* `POST /daily_standup/record_and_respond`
* `GET /daily_standup/summary`

**Mock Test**

* `POST /weekend_mocktest/start-test`
* `POST /weekend_mocktest/submit-answer`

**Weekly Interview**

* `GET /weekly_interview/start_interview`
* `POST /weekly_interview/record_and_respond`
* `GET /weekly_interview/start_next_round`

---

## ?? Usage Flow

### Daily Standup

1. Start voice-based questioning
2. Real-time transcript + reply
3. Evaluation shown + PDF export

### Mock Test

1. Choose user type
2. Answer 10 dynamic questions
3. Score + answers shown

### Interview

1. Tech ? Comm ? HR rounds
2. Voice interaction throughout
3. Final evaluation generated

---

## ?? Troubleshooting

| Issue              | Solution                                        |                                             |
| ------------------ | ----------------------------------------------- | ------------------------------------------- |
| Mic not working    | Check Windows > Settings > Privacy > Microphone |                                             |
| `ffmpeg not found` | Add to PATH or use `choco install ffmpeg`       |                                             |
| Port 8090 busy     | Use \`netstat -ano                              | findstr :8090`then`taskkill /PID <pid> /F\` |
| API error          | Check `.env` values are set properly            |                                             |

---

## ?? Performance & Security

* Audio auto-deletes after 1 hour
* Sessions expire after 2 hrs
* Secured API keys (via .env)
* Recommend adding auth for production

---

## ?? Future Add-ons

* ? JWT Authentication
* ? Admin dashboard with results
* ? AI candidate scoring with LLM memory
* ? Leaderboard & job alerts integration

---
