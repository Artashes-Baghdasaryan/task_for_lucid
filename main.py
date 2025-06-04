from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from config import settings
from database import create_tables
from controllers import auth_router, post_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Social Posts API",
    description="A FastAPI application with MVC architecture for managing user posts",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Payload size middleware
@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    if request.method == "POST":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.MAX_PAYLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Request payload too large. Maximum size: {settings.MAX_PAYLOAD_SIZE} bytes"
            )
    
    response = await call_next(request)
    return response

# Exception handlers
@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)}
    )

@app.exception_handler(413)
async def payload_too_large_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=413,
        content={"detail": "Payload too large"}
    )

# Include routers
app.include_router(auth_router)
app.include_router(post_router)

@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "message": "Social Posts API is running"
    }

@app.get("/health", tags=["Health"])
def detailed_health():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time(),
        "environment": "development"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["./"]
    )