from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bot.api.routes import router
from bot.config import get_settings

settings = get_settings()

app = FastAPI(
    title="FinAI Assistant API",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "finai-api"}
