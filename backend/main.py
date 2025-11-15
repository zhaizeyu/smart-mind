import logging
import os
from logging.config import dictConfig
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from routers import ask  # type: ignore[attr-defined]
from routers import summary  # type: ignore[attr-defined]
from routers import generate  # type: ignore[attr-defined]
from routers import mindmap  # type: ignore[attr-defined]

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(levelname)s] %(asctime)s %(name)s: %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("mindflow.api")

app = FastAPI(
    title="MindFlow API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"]
)

routers = [ask.router, summary.router, generate.router, mindmap.router]
for router in routers:
    app.include_router(router)

api_router = APIRouter()
for router in routers:
    api_router.include_router(router)

app.include_router(api_router, prefix="/api")


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("MindFlow API starting with routers: %s", [route.path for route in app.routes])


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("MindFlow API stopping")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


FRONTEND_DIST = Path(os.getenv("FRONTEND_DIST", Path(__file__).resolve().parents[1] / "frontend" / "dist"))
INDEX_FILE = FRONTEND_DIST / "index.html"

if INDEX_FILE.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(INDEX_FILE)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path.startswith(("api", "openapi", "docs", "redoc", "health")):
            raise HTTPException(status_code=404)
        candidate = (FRONTEND_DIST / full_path).resolve()
        if candidate.is_file() and str(candidate).startswith(str(FRONTEND_DIST)):
            return FileResponse(candidate)
        return FileResponse(INDEX_FILE)
