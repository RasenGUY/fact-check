# Fact-Check API

A 2-step LLM pipeline for fact-checking claims and generating Schema.org ClaimReview JSON.

## Overview

This API uses a two-step approach to fact-check claims:

1. **Web Search**: Queries the web for evidence using OpenRouter's online models
2. **Evaluation**: Analyzes the evidence and generates a ClaimReview verdict

## Quick Start

### Prerequisites

- Python 3.13+
- OpenRouter API key

### Setup

```bash
# Clone and setup
make setup

# Add your OpenRouter API key
echo "OPENROUTER_API_KEY=your-key-here" >> .env

# Start the API
make up-api
```

### Using Docker

```bash
# Build and run
make build
make up

# View logs
make logs

# Stop
make down
```

## API Documentation

Once the API is running, access the documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/v1/openapi.json

## API Endpoints

### Health Check

```
GET /health
```

Returns the health status of the API.

### Fact Check

```
POST /api/v1/fact-check
```

**Request Body:**
```json
{
  "query": "The sky is blue"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "claimReviewed": "The sky is blue",
    "author": {
      "name": "WordLift"
    },
    "datePublished": "2025-01-01",
    "reviewRating": {
      "ratingValue": "5",
      "alternateName": "True",
      "bestRating": "5",
      "worstRating": "1"
    },
    "url": "https://fact-check.wordlift.io/review/...",
    "reviewBody": "This claim is verified as true...",
    "itemReviewed": {
      "url": ["https://source1.com", "https://source2.com"]
    }
  }
}
```

## Development

### Project Structure

```
fact_check_task/
├── app/
│   ├── adapters/          # External API adapters
│   ├── api/               # FastAPI routes & middlewares
│   ├── config/            # Settings & model configuration
│   ├── models/            # Pydantic models
│   ├── pipelines/         # LLM pipeline logic
│   ├── services/          # Business logic
│   └── utils/             # Logging, retry decorator
├── tests/
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── docs/                  # Documentation
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── requirements.txt
```

### Makefile Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make setup` | Setup development environment |
| `make venv` | Create virtual environment |
| `make env` | Create .env from template |
| `make up-api` | Start API locally |
| `make build` | Build Docker image |
| `make up` | Start services in Docker |
| `make down` | Stop all services |
| `make logs` | Show Docker logs |
| `make test` | Run unit tests |
| `make test-all` | Run all tests |
| `make coverage` | Run tests with coverage |
| `make clean` | Remove cache files |
| `make status` | Show system status |

### Running Tests

```bash
# Unit tests only
make test

# All tests (unit + integration)
make test-all

# With coverage report
make coverage
```

## Configuration

Environment variables (set in `.env`):

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key | (required) |
| `OPENROUTER_API_URL` | OpenRouter API URL | `https://openrouter.ai/api/v1` |
| `MAX_SEARCH_RESULTS` | Max web search results | `5` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Architecture

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.
