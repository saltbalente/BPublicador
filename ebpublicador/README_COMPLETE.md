# EBPublicador - AI-Powered Content Management System

## 🚀 Overview

EBPublicador is a modern, cloud-native content management system powered by artificial intelligence. Built with FastAPI and designed for seamless deployment across multiple cloud platforms.

### ✨ Key Features

- **AI-Powered Content Generation**: Generate high-quality content using OpenAI GPT and Google Gemini
- **Cloud-Native Architecture**: Optimized for Vercel, Railway, Render, and Docker deployments
- **Robust Error Handling**: Graceful fallbacks and comprehensive error management
- **Multi-Environment Support**: Automatic configuration based on deployment platform
- **RESTful API**: Complete API for content management and AI generation
- **Theme System**: Customizable themes with CSS management
- **File Management**: Secure file uploads with cloud storage optimization
- **SEO Optimization**: Built-in SEO analysis and optimization tools

## 🏗️ Architecture

```
ebpublicador/
├── api/                    # Core API application
│   ├── core/              # Application core (app, database)
│   ├── middleware/        # Custom middleware (logging, errors)
│   ├── models/           # SQLAlchemy models
│   ├── routes/           # API endpoints
│   └── services/         # Business logic services
├── config/               # Environment configuration
├── deploy/               # Deployment configurations
│   ├── docker/          # Docker setup
│   ├── vercel/          # Vercel configuration
│   ├── railway/         # Railway configuration
│   └── render/          # Render configuration
├── storage/              # File storage
│   ├── uploads/         # User uploads
│   ├── generated/       # AI-generated content
│   └── cache/           # Temporary files
├── web/                  # Frontend assets
│   ├── assets/          # Static assets
│   ├── templates/       # HTML templates
│   └── components/      # Reusable components
└── tests/                # Test suite
```

## 🛠️ Technology Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Database**: SQLite (local/Vercel), PostgreSQL (Railway/Render)
- **AI Services**: OpenAI GPT, Google Gemini
- **Deployment**: Vercel, Railway, Render, Docker
- **Frontend**: Vanilla JavaScript, Modern CSS

## 📋 Prerequisites

- Python 3.11+
- pip or poetry
- Git
- AI API keys (OpenAI and/or Gemini)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd ebpublicador

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Required: OPENAI_API_KEY or GEMINI_API_KEY
# Optional: DATABASE_URL, SECRET_KEY, etc.
```

### 3. Run Locally

```bash
# Start the development server
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Access the application at `http://localhost:8000`

## 🌐 Deployment Options

### Vercel (Serverless)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cp deploy/vercel/vercel.json .
vercel --prod
```

**Features on Vercel:**
- ✅ Basic API endpoints
- ✅ AI content generation
- ✅ SQLite database
- ❌ File uploads (limited)
- ❌ Background tasks

### Railway (Full-Featured)

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway link
cp deploy/railway/railway.toml .
railway up
```

**Features on Railway:**
- ✅ All features supported
- ✅ PostgreSQL database
- ✅ File uploads
- ✅ Background tasks
- ✅ Custom domains

### Docker (Self-Hosted)

```bash
# Build and run with Docker Compose
cp deploy/docker/docker-compose.yml .
cp deploy/docker/Dockerfile .
docker-compose up -d
```

**Includes:**
- FastAPI application
- PostgreSQL database
- Redis cache
- Nginx reverse proxy
- PgAdmin (development)

### Render (Managed)

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables

## 📚 API Documentation

### Core Endpoints

#### Posts Management
- `GET /api/posts` - List posts with pagination
- `POST /api/posts` - Create new post
- `GET /api/posts/{id}` - Get specific post
- `PUT /api/posts/{id}` - Update post
- `DELETE /api/posts/{id}` - Delete post
- `POST /api/posts/{id}/upload` - Upload post image

#### AI Content Generation
- `POST /generate/content` - Generate AI content
- `POST /generate/titles` - Generate title suggestions
- `POST /generate/seo-analysis` - SEO analysis
- `GET /generate/history` - Generation history
- `GET /generate/providers` - Available AI providers
- `GET /generate/stats` - Generation statistics

#### Administration
- `GET /admin/themes` - List themes
- `POST /admin/themes` - Create theme
- `PUT /admin/themes/{id}` - Update theme
- `DELETE /admin/themes/{id}` - Delete theme
- `GET /admin/settings` - Get settings
- `PUT /admin/settings` - Update settings
- `GET /admin/stats` - System statistics
- `POST /admin/backup` - Create backup
- `GET /admin/health` - Health check

### Authentication

Currently, the API is open for development. For production, implement authentication:

```python
# Add to your routes
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

def get_current_user(token: str = Depends(security)):
    # Implement your authentication logic
    pass
```

## 🎨 Frontend Integration

### Basic HTML Example

```html
<!DOCTYPE html>
<html>
<head>
    <title>EBPublicador</title>
    <link rel="stylesheet" href="/static/main.css">
</head>
<body>
    <div id="app">
        <!-- Your content here -->
    </div>
    <script src="/static/app.js"></script>
</body>
</html>
```

### JavaScript API Client

```javascript
class EBPublicadorAPI {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
    }
    
    async generateContent(data) {
        const response = await fetch(`${this.baseURL}/generate/content`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return response.json();
    }
    
    async getPosts(page = 1, perPage = 10) {
        const response = await fetch(
            `${this.baseURL}/api/posts?page=${page}&per_page=${perPage}`
        );
        return response.json();
    }
}

// Usage
const api = new EBPublicadorAPI();
api.generateContent({
    topic: "AI in Content Marketing",
    content_type: "blog_post",
    tone: "professional",
    length: "medium"
}).then(content => console.log(content));
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Deployment environment | `local` | No |
| `DEBUG` | Debug mode | `true` | No |
| `DATABASE_URL` | Database connection | SQLite | No |
| `OPENAI_API_KEY` | OpenAI API key | - | Yes* |
| `GEMINI_API_KEY` | Gemini API key | - | Yes* |
| `SECRET_KEY` | JWT secret key | Generated | No |
| `ALLOWED_ORIGINS` | CORS origins | `*` | No |
| `UPLOAD_MAX_SIZE_MB` | Max upload size | `10` | No |

*At least one AI provider key is required

### Database Configuration

#### SQLite (Local/Vercel)
```bash
DATABASE_URL=sqlite:///./storage/ebpublicador.db
```

#### PostgreSQL (Railway/Render)
```bash
DATABASE_URL=postgresql://user:password@host:port/database
```

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=api

# Run specific test
pytest tests/test_content_service.py
```

## 📊 Monitoring and Logging

### Health Checks
- `/health` - Application health
- `/admin/health` - Comprehensive system health

### Logging
Logs are written to:
- Console (always)
- `storage/logs/app.log` (if writable)
- Cloud platform logs (in production)

### Metrics
- Request/response times
- AI generation statistics
- Storage usage
- Database performance

## 🔒 Security

### Best Practices Implemented
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy
- File upload restrictions
- CORS configuration
- Security headers
- Rate limiting (in nginx)

### Production Security Checklist
- [ ] Set strong `SECRET_KEY`
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS
- [ ] Implement authentication
- [ ] Set up monitoring
- [ ] Regular backups
- [ ] Update dependencies

## 🚨 Troubleshooting

### Common Issues

#### Permission Errors
```bash
# Fix storage permissions
chmod -R 755 storage/
# Or use fallback to /tmp (automatic in cloud)
```

#### Database Connection
```bash
# Check database URL
echo $DATABASE_URL

# Test connection
python -c "from api.core.database import get_db_info; print(get_db_info())"
```

#### AI Provider Issues
```bash
# Check API keys
echo $OPENAI_API_KEY
echo $GEMINI_API_KEY

# Test providers
curl -X GET http://localhost:8000/generate/providers
```

### Debug Mode
Enable debug mode for detailed error information:
```bash
DEBUG=true python main.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt pytest black flake8

# Format code
black .

# Lint code
flake8 .

# Run tests
pytest
```

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- Documentation: This README
- Issues: GitHub Issues
- API Docs: `/docs` (when running)
- Health Check: `/health`

## 🗺️ Roadmap

- [ ] User authentication system
- [ ] Advanced theme editor
- [ ] Multi-language support
- [ ] Plugin system
- [ ] Advanced analytics
- [ ] Mobile app
- [ ] Collaborative editing
- [ ] Advanced AI features

---

**EBPublicador** - Empowering content creation with AI 🚀