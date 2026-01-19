import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router
from app import models_db  # noqa: F401  (ensures model is registered for tooling)

app = FastAPI(title="Waitlist API", version="1.0.0")

# CORS configuration
# Set ALLOWED_ORIGINS env var to restrict (comma-separated), or leave unset to allow all
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
origins = ["*"] if allowed_origins == "*" else [o.strip() for o in allowed_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
