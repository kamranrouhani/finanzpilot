"""Main FastAPI application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.features.auth.router import router as auth_router
from app.features.receipts.router import router as receipts_router
from app.features.categories.router import router as categories_router
from app.features.transactions.router import router as transactions_router
from app.features.budgets.router import router as budgets_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    print("Starting FinanzPilot backend...")
    yield
    # Shutdown
    print("Shutting down FinanzPilot backend...")


# Create FastAPI app
app = FastAPI(
    title="FinanzPilot API",
    description="Local AI-powered personal finance application for German users",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(receipts_router, prefix="/api")
app.include_router(categories_router)
app.include_router(transactions_router, prefix="/api")
app.include_router(budgets_router)


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker."""
    return {"status": "healthy", "service": "finanzpilot-backend"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "FinanzPilot API",
        "version": "0.1.0",
        "docs": "/docs",
    }
