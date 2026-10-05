from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import health, videos

app = FastAPI(title="basket-analytics")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(videos.router)

# Sert les fichiers vidéo bruts pour lecture directe par le <video> du frontend
# (play/pause/seek natifs, support des requêtes Range).
app.mount("/media", StaticFiles(directory=videos.STORAGE_DIR), name="media")
