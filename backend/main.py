from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import ask  # type: ignore[attr-defined]

app = FastAPI(title="SmartMind API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"]
)

app.include_router(ask.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
