# Fact-Check Service - Implementation Progress

> **Approach:** API skeleton first (top-down with stubs)
> **Architecture:** [architecture.md](./architecture.md)

---

## Phase 1: Project Setup

- [x] Create directory structure
  ```
  fact-check/
  ├── app/
  │   ├── __init__.py
  │   ├── config/
  │   ├── models/
  │   ├── adapters/
  │   ├── pipelines/
  │   ├── services/
  │   └── api/
  └── tests/
  ```
- [x] Create `requirements.txt` with dependencies
- [x] Create `.env.example` with required variables
- [x] Create all `__init__.py` files

---

## Phase 2: API Layer (Skeleton)

### 2.1 FastAPI Entry Point
- [x] Create `app/main.py` with FastAPI app instance
- [x] Add CORS middleware
- [x] Add health check endpoint (`GET /health`)
- [x] Include router from `app/api/routes.py`

### 2.2 Logging & Middleware (seo-acg pattern)
- [x] Create `app/utils/logging.py` with structlog
- [x] Create `app/api/middlewares/request_logging.py`
- [x] Create `app/api/middlewares/response.py`
- [x] Create `app/api/exception_handlers.py`
- [x] Create `app/api/transformers.py`
- [x] Create `app/schemas/response.py` (StandardResponse, ErrorResponse)

### 2.3 Request/Response Models (Stubs)
- [x] Create `app/models/request.py` with `FactCheckRequest`
- [x] Create `app/models/response.py` with `ClaimReview` (and nested models)
- [x] Create `app/models/internal.py` with `PipelineParams`

### 2.4 API Routes
- [x] Create `app/api/routes.py`
- [x] Add `POST /fact-check` endpoint (stub returning mock data)
- [x] Verify endpoint works with mock response

---

## Phase 3: Service Layer

### 3.1 Service Implementation
- [x] Create `app/services/fact_check_service.py`
- [x] Implement `FactCheckService` class
- [x] Add `fact_check()` method (stub calling pipeline)
- [x] Wire service to API route

---

## Phase 4: Configuration

### 4.1 Settings
- [x] Create `app/config/settings.py`
- [x] Implement `Settings` class with `BaseSettings`
- [x] Add `openrouter_api_key` field
- [x] Add `max_search_results` field
- [x] Add `log_level` field

### 4.2 Model Configuration
- [x] Create `app/config/model_config.py`
- [x] Define `ModelUseCase` enum
- [x] Define `ModelConfig` dataclass
- [x] Create `MODEL_MAPPING` dictionary
- [x] Implement `ModelSelector` class with static methods

---

## Phase 5: Adapters

### 5.1 OpenRouter Adapter
- [ ] Create `app/adapters/openrouter_adapter.py`
- [ ] Implement `OpenRouterAdapter` class
- [ ] Add `make_request()` method with retry logic
- [ ] Add structured output support (`output_type` parameter)
- [ ] Add JSON schema response format handling

### 5.2 Websearch Adapter
- [ ] Create `app/adapters/openrouter_websearch_adapter.py`
- [ ] Define `WebsearchResponse` model
- [ ] Define `WebsearchResponseList` model
- [ ] Implement `OpenRouterWebsearchAdapter` class
- [ ] Add `WEBSEARCH_SYSTEM_PROMPT`
- [ ] Add `search()` method with `:online` suffix logic

---

## Phase 6: Pipeline

### 6.1 Prompts
- [ ] Create `app/pipelines/prompts/__init__.py`
- [ ] Create `app/pipelines/prompts/evaluation.py`
- [ ] Add `EVALUATION_PROMPT` constant

### 6.2 Pipeline Implementation
- [ ] Create `app/pipelines/fact_check_pipeline.py`
- [ ] Implement `FactCheckPipeline` class
- [ ] Add `execute()` method (main orchestrator)
- [ ] Add `_search_for_evidence()` method (Step 1)
- [ ] Add `_evaluate_claim()` method (Step 2)
- [ ] Add `_build_user_prompt()` helper method
- [ ] Create singleton `fact_check_pipeline` instance

---

## Phase 7: Integration & Testing

### 7.1 Wire Everything Together
- [ ] Remove stubs from API routes
- [ ] Connect service to real pipeline
- [ ] End-to-end test with real API call

### 7.2 Unit Tests
- [ ] Create `tests/conftest.py` with fixtures
- [ ] Create `tests/test_api.py`
  - [ ] Test `/health` endpoint
  - [ ] Test `/fact-check` with valid request
  - [ ] Test `/fact-check` with invalid request (422)
- [ ] Create `tests/test_pipeline.py`
  - [ ] Test `_build_user_prompt()`
  - [ ] Test pipeline with mocked adapters

### 7.3 Error Handling
- [ ] Add proper exception handling in adapters
- [ ] Add retry logic validation
- [ ] Test error scenarios

---

## Phase 8: Docker & Deployment

- [ ] Create `Dockerfile`
- [ ] Create `docker-compose.yml`
- [ ] Test containerized deployment
- [ ] Document deployment process in README.md

---

## Current Status

| Phase | Status | Notes |
|-------|--------|-------|
| 1. Project Setup | Complete | Directory structure, requirements, .env.example |
| 2. API Layer | Complete | main.py, routes, middlewares, logging, transformers, exception handlers |
| 3. Service Layer | Complete | FactCheckService with stub, wired to route |
| 4. Configuration | Complete | Settings, ModelUseCase, ModelSelector |
| 5. Adapters | Not Started | |
| 6. Pipeline | Not Started | |
| 7. Integration | Not Started | |
| 8. Docker | Not Started | |

---

## Notes

_Add implementation notes, blockers, and decisions here as we progress._
