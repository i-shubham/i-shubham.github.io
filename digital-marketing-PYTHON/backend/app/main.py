import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import auth, users, products, bids, influencers, payments, admin, stats

app = FastAPI(title="Plugg API", version="1.0.0")

# CORS (needed if frontend served separately; same-origin is fine without it)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(bids.router)
app.include_router(influencers.router)
app.include_router(payments.router)
app.include_router(admin.router)
app.include_router(stats.router)

# Serve static frontend files
frontend_path = Path(__file__).parent.parent / settings.frontend_dir
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
