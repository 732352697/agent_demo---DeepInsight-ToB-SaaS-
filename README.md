# 🤖 DeepInsight - AI Live Streaming Assistant

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**AI-Powered ToB SaaS Platform for Tech Content Creators**

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [API](#-api-reference)

</div>

---

## 📖 Overview

DeepInsight is an intelligent live streaming assistant designed for tech content creators. It combines multi-agent AI systems with OBS automation to streamline content creation, live streaming, and post-stream analytics.

### Core Modules

- 🎬 **Live Script Generation** - AI-powered director outlines and anchor scripts
- 👨‍🏫 **VIP Tutor Assistant** - Context-aware Q&A for post-live support
- 📝 **Business Asset Generation** - One-click marketing materials
- 📊 **Live Review & Judging** - LLM-as-a-Judge analytics with radar charts

---

## ✨ Features

| Feature | Description | Technology |
|---------|-------------|------------|
| **Script Generation** | Director outlines + anchor scripts + OBS automation | DeepSeek + LangChain |
| **Tutor Chat** | Course material-based Q&A system | RAG + FastAPI |
| **Asset Creation** | Xiaohongshu copy + Douyin scripts | Multi-Agent System |
| **Stream Analytics** | Post-stream evaluation with scoring | LLM-as-a-Judge |
| **OBS Integration** | Real-time scene switching | WebSocket |
| **TTS Generation** | Automated voiceover | edge-tts |

---

## 🚀 Quick Start

### Prerequisites

```bash
- Python 3.9+
- Node.js 16+
- OBS Studio (optional, for live streaming)
```

### Installation

```bash
# Clone repository
git clone https://github.com/732352697/agent_demo---DeepInsight-ToB-SaaS-.git
cd agent_demo

# Backend setup
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install
cd ..

# Configure environment
cp .env.example .env
# Edit .env with your DeepSeek API key
```

### Running the Application

**Backend (FastAPI):**
```bash
python main.py
# Server runs on http://localhost:8000
```

**Frontend (Next.js):**
```bash
cd frontend
npm run dev
# UI runs on http://localhost:3000
```

**Streamlit UI (Alternative):**
```bash
streamlit run app.py
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (Next.js)              │
│  ┌──────────┐  ┌──────────┐            │
│  │Dashboard │  │ Chat UI  │            │
│  └──────────┘  └──────────┘            │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│      Backend (FastAPI)                  │
│  ┌──────────────────────────────────┐  │
│  │ /live-script                     │  │
│  │ /tutor-chat                      │  │
│  │ /business-assets                 │  │
│  │ /judge-report                    │  │
│  └──────────────────────────────────┘  │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│      Multi-Agent System                 │
│  ┌──────────┐  ┌──────────┐            │
│  │ Director │  │  Tutor   │            │
│  │  Agent   │  │  Agent   │            │
│  └──────────┘  └──────────┘            │
│  ┌──────────┐  ┌──────────┐            │
│  │ Business │  │  Judge   │            │
│  │  Agent   │  │  Agent   │            │
│  └──────────┘  └──────────┘            │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│      Data Layer                         │
│  ┌──────────┐  ┌──────────┐            │
│  │  SQLite  │  │   OBS    │            │
│  │ Database │  │WebSocket │            │
│  └──────────┘  └──────────┘            │
└─────────────────────────────────────────┘
```

---

## 📚 API Reference

### 1. Generate Live Script

```bash
POST /live-script
Content-Type: application/json

{
  "topic": "Python异步编程入门",
  "duration": 60,
  "target_audience": "初级开发者"
}

# Response
{
  "director_outline": "...",
  "anchor_script": "...",
  "action_queue": [...],
  "obs_scenes": [...]
}
```

### 2. Tutor Chat

```bash
POST /tutor-chat
Content-Type: application/json

{
  "question": "asyncio和threading有什么区别？",
  "context": "Python异步编程课程"
}

# Response
{
  "answer": "...",
  "references": [...]
}
```

### 3. Generate Business Assets

```bash
POST /business-assets
Content-Type: application/json

{
  "live_topic": "Python异步编程",
  "key_points": ["asyncio", "协程", "并发"]
}

# Response
{
  "xiaohongshu_copy": "...",
  "douyin_script": "...",
  "course_materials": [...]
}
```

### 4. Judge Live Stream

```bash
POST /judge-report
Content-Type: application/json

{
  "transcript": "...",
  "danmu_history": [...],
  "metrics": {...}
}

# Response
{
  "overall_score": 8.5,
  "dimensions": {
    "content_quality": 9.0,
    "engagement": 8.0,
    "technical_depth": 8.5
  },
  "suggestions": [...]
}
```

---

## 🔧 Configuration

### Environment Variables

```bash
# DeepSeek API
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com

# OBS WebSocket (optional)
OBS_WEBSOCKET_HOST=localhost
OBS_WEBSOCKET_PORT=4455
OBS_WEBSOCKET_PASSWORD=your-password

# Database
DATABASE_PATH=./deepinsight.db
```

---

## 🐳 Docker Deployment

```bash
# Build and run
docker-compose up -d

# Access
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

---

## 📊 Tech Stack

**Backend:**
- FastAPI - REST API framework
- LangChain - Agent orchestration
- DeepSeek - LLM provider
- SQLite - Data persistence
- edge-tts - Text-to-speech

**Frontend:**
- Next.js 14 - React framework
- TypeScript - Type safety
- Tailwind CSS - Styling
- Framer Motion - Animations
- Recharts - Data visualization

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 📮 Contact

- **Issues**: [GitHub Issues](https://github.com/732352697/agent_demo---DeepInsight-ToB-SaaS-/issues)
- **Email**: chenleyang05@gmail.com

---

<div align="center">

**[⬆ Back to Top](#-deepinsight---ai-live-streaming-assistant)**

Made with ❤️ for Tech Content Creators

</div>
