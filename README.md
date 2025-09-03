# Research Board 🔍

A multimodal desktop research assistant designed to help users collect, organize, and analyze browsing activity using AI-powered summarization, semantic search, and explainable recommendations.

## 🌟 Features

- **Web Data Collection**: Capture URLs, content, and user highlights from browser extension
- **Local Storage**: All data stored locally using SQLite for privacy
- **AI-Powered Analysis**: Summarization and semantic search using local LLMs
- **Explainable AI**: Citations and transparent recommendations
- **Cognitive Support**: Tools inspired by psychology research
- **Cross-Platform**: Built for macOS (Apple Silicon optimized)

## 🏗️ Architecture

```
research-board/
├── app/                    # FastAPI backend application
│   ├── main.py            # Application entry point
│   ├── config.py          # Configuration settings
│   ├── db/                # Database setup and utilities
│   ├── models/            # SQLAlchemy models
│   └── api/               # API route handlers
├── ChromeExtention/       # Browser extension (MV3)
├── requirements.txt       # Python dependencies
├── setup.sh              # Quick setup script
└── run_dev.py            # Development server runner
```

## 🚀 Quick Start

### Backend Setup

1. **Clone and navigate to the project**:
   ```bash
   git clone <repository-url>
   cd research-board
   ```

2. **Run the setup script** (recommended):
   ```bash
   ./setup.sh
   ```

3. **Or set up manually**:
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Create environment configuration
   cp .env.example .env
   ```

4. **Start the development server**:
   ```bash
   source venv/bin/activate
   python run_dev.py
   ```

5. **Access the API**:
   - API Server: http://127.0.0.1:8000
   - Interactive Docs: http://127.0.0.1:8000/api/v1/docs
   - Health Check: http://127.0.0.1:8000/health

## 📁 Backend Structure

### Core Files

- **`app/main.py`**: FastAPI application with CORS, routers, and lifecycle management
- **`app/config.py`**: Environment-based configuration using Pydantic
- **`app/db/database.py`**: SQLAlchemy setup with session management
- **`app/models/models.py`**: Database models for pages, highlights, and history
- **`app/api/routes.py`**: API endpoints for data retrieval and search

### Database Models

- **`Page`**: Web pages and PDFs with metadata, content, and AI analysis
- **`Highlight`**: User-selected content with context and annotations
- **`History`**: Browsing sessions with interaction metrics
- **`SearchQuery`**: Search logs for improving recommendations
- **`Tag`**: Content organization and categorization

## 🔧 Configuration

Edit the `.env` file to customize your setup:

```env
# API Configuration
HOST=127.0.0.1
PORT=8000
DEBUG=True

# Database
DATABASE_URL=sqlite:///./research_board.db

# Security
SECRET_KEY=your-secret-key-here

# CORS (for Chrome extension and desktop app)
ALLOWED_ORIGINS=http://localhost:3000,chrome-extension://*
```

## 🧪 Development

### API Endpoints

Current endpoints (see `/api/v1/docs` for interactive documentation):

- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /api/v1/pages` - List pages with pagination
- `GET /api/v1/highlights` - List highlights
- `GET /api/v1/history` - Browsing history
- `GET /api/v1/search` - Search functionality
- `GET /api/v1/stats` - Application statistics

### Database Management

The SQLite database is automatically created on first run. Tables are created using SQLAlchemy's `create_all()` method.

### Adding New Features

1. **Models**: Add new tables in `app/models/models.py`
2. **Routes**: Add endpoints in `app/api/routes.py`
3. **Configuration**: Update `app/config.py` for new settings
4. **Dependencies**: Update `requirements.txt`

## 🔒 Privacy & Security

- **Local-First**: All data stored locally in SQLite
- **No Cloud Dependencies**: Runs entirely on your machine
- **CORS Protection**: Configured for specific origins only
- **Environment Isolation**: Uses virtual environments

## 🎯 Roadmap

- [ ] Chrome Extension integration endpoints
- [ ] AI summarization with local LLMs
- [ ] Semantic search implementation
- [ ] Desktop app API integration
- [ ] Export/import functionality
- [ ] Advanced analytics and insights

## 🛠️ Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **AI/ML**: Planned integration with local LLMs (Llama.cpp, Transformers)
- **Development**: Python 3.8+, Virtual environments
- **Platform**: macOS optimized (Apple Silicon)

