# AI Customer Support Agent Platform

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg)](https://fastapi.tiangolo.com)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Docker](https://img.shields.io/badge/docker-enabled-blue.svg)](https://www.docker.com/)
[![CI](https://github.com/moseskim1027/ai-support-agent-platform/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/moseskim1027/ai-support-agent-platform/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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

## Deployment

### GitFlow Workflow

This project follows a production-ready GitFlow strategy:

```
develop → staging → main
```

- **develop**: Feature integration and development
- **staging**: Pre-production testing environment
- **main**: Production environment

### CI/CD Pipelines

#### Continuous Integration (CI)
Runs on: Push or PR to `develop`, `staging`, `main`

**Checks:**
- Code formatting (black, isort)
- Linting (flake8)
- Type checking (mypy)
- Unit & integration tests (pytest)
- Security scanning (safety, bandit)
- Docker build verification

#### Continuous Deployment - Staging
Runs on: Push to `staging` branch

**Steps:**
1. Build Docker image with staging tag
2. Push to AWS ECR
3. Deploy to EKS staging cluster
4. Run integration test suite
5. Notify deployment status

#### Continuous Deployment - Production
Runs on: Push to `main` branch

**Steps:**
1. Build production Docker image
2. Push to AWS ECR with version tag
3. Deploy to EKS production cluster (rolling update)
4. Run smoke tests
5. Notify deployment status

### Kubernetes Deployment

Production deployment uses AWS EKS with the following resources:

- **Deployment**: Rolling updates, health checks, 3-10 replicas
- **Service**: ClusterIP for internal communication
- **Ingress**: AWS ALB with HTTPS support
- **HPA**: Auto-scaling based on CPU/memory
- **ConfigMap**: Environment-specific configuration
- **Secrets**: Managed via AWS Secrets Manager

See `infrastructure/k8s/` for complete Kubernetes manifests.

### Local Deployment Commands

```bash
# Start all services
make up

# View logs
make logs-backend

# Run tests
make test

# Check health
make health

# Stop all services
make down
```

### Production Deployment

```bash
# Deploy to staging (via Kustomize)
kubectl apply -k infrastructure/k8s/overlays/staging/

# Deploy to production
kubectl apply -k infrastructure/k8s/overlays/production/

# Monitor deployment
kubectl rollout status deployment/backend -n production

# View logs
kubectl logs -f deployment/backend -n production
```

## Roadmap

- [x] Project setup and Docker configuration
- [x] Basic FastAPI application with health endpoints
- [x] Production-ready environment configuration
- [x] CI/CD with GitHub Actions
- [x] Kubernetes manifests for EKS deployment
- [x] Docker Compose for local development
- [x] Observability setup (Prometheus, Grafana)
- [ ] Multi-agent orchestration with LangGraph
- [ ] RAG pipeline with Qdrant
- [ ] Frontend React chat interface
- [ ] Comprehensive testing suite

## Contributing

This is a portfolio project. Feel free to fork and experiment!

## License

MIT