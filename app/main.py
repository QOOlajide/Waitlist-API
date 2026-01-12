from fastapi import FastAPI
from app.routes import router
from app import models_db  # noqa: F401  (ensures model is registered for tooling)

app = FastAPI(title="Waitlist API", version="1.0.0")
app.include_router(router)
