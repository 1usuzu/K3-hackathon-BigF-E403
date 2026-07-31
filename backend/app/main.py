import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.v1.documents import router as documents_router
from backend.app.api.v1.progress import router as progress_router
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.learning import router as learning_router

app = FastAPI(
    title="AI Learning Agent API",
    version="1.0.0",
    description="Backend API for AI Learning Agent (Student-Facing Only)"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(progress_router)
app.include_router(chat_router)
app.include_router(learning_router)

@app.get("/healthcheck")
def healthcheck():
    return {"status": "OK", "service": "AI Learning Agent Backend"}

# Mount data and codebase static directories
if os.path.exists("data"):
    app.mount("/data", StaticFiles(directory="data"), name="data")

if os.path.exists("codebase"):
    app.mount("/", StaticFiles(directory="codebase", html=True), name="static")
