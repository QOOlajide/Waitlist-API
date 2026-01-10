from fastapi import FastAPI
from app.routes import router
from app.db import Base, engine
from app import models_db  # IMPORTANT: ensures model is registered

app = FastAPI(title="Waitlist API", version="1.0.0")
app.include_router(router)

# Simple table creation (OK for MVP; migrations later)
Base.metadata.create_all(bind=engine)
