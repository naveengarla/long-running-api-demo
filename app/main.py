from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import settings
from app.core.database import init_db
from app.api.router import api_router
# Import models to ensure they are registered with Base.metadata before create_all
import app.models.job

from app.core.telemetry import init_tracer, instrument_fastapi

# Initialize Tracer
init_tracer("api-service")

app = FastAPI(title=settings.PROJECT_NAME)

# Instrument FastAPI
instrument_fastapi(app)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
async def on_startup():
    try:
        await init_db()
    except Exception as e:
        print(f"STARTUP ERROR: {e}")
        # Keep running to allow diagnosis, or re-raise if fatal
        # raise e

@app.get("/")
async def read_root():
    return FileResponse('app/static/index.html')

app.include_router(api_router)
