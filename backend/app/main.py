from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.jobs import router as jobs_router

from sqlalchemy import text

from app.database import engine


app = FastAPI(
    title="AI Speech to Word API",
    description="Multilingual Audio to Word Automation",
    version="0.1.0"
)

app.include_router(
    jobs_router
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/api/health")
def health_check():

    return {
        "status": "healthy",
        "service": "speech-to-word-api"
    }


@app.get("/api/health/database")
def database_health():

    try:

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "connected",
            "database": "speech_word"
        }

    except Exception as error:

        return {
            "status": "error",
            "message": str(error)
        }