import sys
import os

# Backend klasörünün üst dizinini (proje kökünü) sys.path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.core.config import settings

app = FastAPI(title="Mood AI API", description="Yapay Zeka Destekli Müzik Terapisti API")

# Configure CORS
origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if settings.FRONTEND_URL != "*" else ["*"],
    allow_origin_regex=r"https://.*\.vercel\.app" if settings.FRONTEND_URL != "*" else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Healthcheck route for Render / cloud monitoring
@app.get("/")
def root():
    return {"status": "ok", "app": "Mood AI API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# Include router
app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)

