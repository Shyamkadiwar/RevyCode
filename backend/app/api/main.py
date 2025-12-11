from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db
from app.api.routes import auth, repositories, webhooks, reviews

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    #startup
    await init_db()
    yield

    #shutdown
    pass

app = FastAPI(
    title = "RevyCode",
    version = "1.0.0",
    lifespan = lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(repositories.router, prefix="/api/repositories", tags=["Repositories"])
app.include_router(webhooks.router, prefix="/api/webhook", tags=["Webhooks"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["Reviews"])
# app.include_router(webhooks.router, prefix="/webhook", tags=["Webhooks"])
# app.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])

@app.get("/")
async def root():
    return {
        "message": "RevyCode API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}