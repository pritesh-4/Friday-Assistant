from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import chat, settings as settings_router, notes, tasks

app = FastAPI(title=settings.PROJECT_NAME)

# Enforce CORS for React client queries
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach router modules
app.include_router(chat.router)
app.include_router(settings_router.router)
app.include_router(notes.router)
app.include_router(tasks.router)

@app.get("/")
def root():
    return {
        "status": "online",
        "project": settings.PROJECT_NAME
    }