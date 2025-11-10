import logging
from logging.config import dictConfig

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import ask  # type: ignore[attr-defined]
from routers import summary  # type: ignore[attr-defined]

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

app = FastAPI(title="MindFlow API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"]
)

app.include_router(ask.router)
app.include_router(summary.router)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("MindFlow API starting with routers: %s", [route.path for route in app.routes])


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("MindFlow API stopping")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
