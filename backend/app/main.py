from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import manufacturing, auth, character
from .services.auth_service import init_auth_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_auth_db()
    yield


app = FastAPI(
    title="EVE Industry Calculator",
    description="Manufacturing calculator for EVE Online",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(manufacturing.router, prefix="/api")
app.include_router(auth.router)
app.include_router(character.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
