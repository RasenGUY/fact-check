from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.utils.logging import configure_logging_for_api, get_logger
from app.api.middlewares.request_logging import RequestLoggingMiddleware
from app.api.middlewares.response import ResponseTransformerMiddleware
from app.api.exception_handlers import add_exception_handlers
from app.api.routes import router

# Configure logging before anything else
configure_logging_for_api()

logger = get_logger(__name__)

app = FastAPI(
    title="Fact-Check API",
    description="A 2-step LLM pipeline for fact-checking claims and generating ClaimReview JSON",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middlewares (order matters - first added = last executed)
app.add_middleware(ResponseTransformerMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Add exception handlers
add_exception_handlers(app)

# Include API routes
app.include_router(router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """Log startup message."""
    logger.info("Fact-Check API starting up")


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown message."""
    logger.info("Fact-Check API shutting down")
