# AI Customer Support Agent Platform

A production-ready, multi-agent customer support platform demonstrating advanced AI agent orchestration, RAG pipelines, and real-time conversational interfaces.

## Features

- **Multi-Agent Orchestration**: Router, RAG, Tool, and Supervisor agents using LangGraph
- **Advanced RAG Pipeline**: Hybrid search with Qdrant vector database
- **Real-time Chat**: FastAPI backend with WebSocket support
- **Observability**: Prometheus metrics and Grafana dashboards
- **Production-Ready**: Docker containerization, health checks, and CI/CD

## Tech Stack

### Backend
- **FastAPI** - High-performance async API framework
- **LangGraph** - Multi-agent workflow orchestration
- **Qdrant** - Vector database for RAG
- **PostgreSQL** - Relational data storage
- **Redis** - Caching and session management
- **Prometheus + Grafana** - Metrics and monitoring

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **GitHub Actions** - CI/CD pipeline

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)

### 1. Clone and Setup

```bash
# Clone repository
git clone git@github-secondary:moseskim1027/ai-support-agent-platform.git
cd ai-support-agent-platform

# Copy environment file
cp .env.example .env

# Edit .env and add your API keys
# OPENAI_API_KEY=your_key
# ANTHROPIC_API_KEY=your_key
```

### 2. Start Services

```bash
# Build and start all services
make up

# Or use docker-compose directly
docker-compose up -d
```

### 3. Access Services

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/api/health

# Chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, I need help with my order"}'
```

## Development

### Run Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov
```

### View Logs

```bash
# All services
make logs

# Backend only
make logs-backend
```

### Local Development (without Docker)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
python -m app.main
```

## Project Structure

```
ai-support-agent-platform/
├── backend/
│   ├── app/
│   │   ├── agents/          # Agent implementations
│   │   ├── orchestration/   # LangGraph workflows
│   │   ├── rag/             # RAG pipeline
│   │   ├── tools/           # Function calling tools
│   │   ├── api/             # FastAPI routes
│   │   └── observability/   # Metrics and monitoring
│   ├── tests/               # Test suite
│   ├── Dockerfile
│   └── requirements.txt
├── infrastructure/
│   ├── prometheus.yml       # Prometheus config
│   ├── terraform/           # IaC (coming soon)
│   └── k8s/                 # Kubernetes manifests (coming soon)
├── docker-compose.yml
├── Makefile
└── README.md
```

## API Endpoints

### Health Checks
- `GET /api/health` - Service health status
- `GET /api/ready` - Readiness probe (K8s)
- `GET /api/live` - Liveness probe (K8s)

### Chat
- `POST /api/chat` - Send message to agent
- `GET /api/conversations/{id}` - Get conversation history

### Metrics
- `GET /metrics` - Prometheus metrics

## Roadmap

- [x] Project setup and Docker configuration
- [x] Basic FastAPI application
- [ ] Multi-agent orchestration with LangGraph
- [ ] RAG pipeline with Qdrant
- [ ] Frontend React chat interface
- [ ] Comprehensive testing suite
- [ ] CI/CD with GitHub Actions
- [ ] Kubernetes deployment

## Contributing

This is a portfolio project. Feel free to fork and experiment!

## License

MIT