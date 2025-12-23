from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

from app.utils.logging import configure_logging_for_api, get_logger
from app.api.middlewares.request_logging import RequestLoggingMiddleware
from app.api.middlewares.response import ResponseTransformerMiddleware
from app.api.exception_handlers import add_exception_handlers
from app.api.routes import router
from app.config.settings import settings

# Configure logging before anything else
configure_logging_for_api()

logger = get_logger(__name__)

app = FastAPI(
    title=settings.project_name,
    description="A 2-step LLM pipeline for fact-checking claims and generating ClaimReview JSON",
    version=f"v{settings.api_version}",
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
    openapi_url=f"/v{settings.api_version}/openapi.json",
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
app.include_router(router, prefix=f"/api/v{settings.api_version}")


# Custom Swagger UI route
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with persistent authorization."""
    return get_swagger_ui_html(
        openapi_url=f"/v{settings.api_version}/openapi.json",
        title=f"{settings.project_name} - Swagger UI",
        oauth2_redirect_url=None,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_ui_parameters={"persistAuthorization": True},
    )


# Custom ReDoc route
@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """Custom ReDoc documentation."""
    return get_redoc_html(
        openapi_url=f"/v{settings.api_version}/openapi.json",
        title=f"{settings.project_name} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )


# Custom OpenAPI schema
@app.get(f"/v{settings.api_version}/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    """Custom OpenAPI schema with security definitions."""
    openapi_schema = get_openapi(
        title=settings.project_name,
        version=f"v{settings.api_version}",
        description="A 2-step LLM pipeline for fact-checking claims and generating ClaimReview JSON",
        routes=app.routes,
    )

    # Add API key security scheme
    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKey": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication",
        }
    }

    # Apply security requirement to all operations
    if "security" not in openapi_schema:
        openapi_schema["security"] = [{"ApiKey": []}]

    return openapi_schema


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.project_name}


@app.on_event("startup")
async def startup_event():
    """Log startup message."""
    logger.info("Fact-Check API starting up")


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown message."""
    logger.info("Fact-Check API shutting down")
