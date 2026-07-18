from fastapi import FastAPI

from app.config import description, title, version


app = FastAPI(title=title, description=description, version=version)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "ShelfSense IT API is running"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/ready")
def readiness_check() -> dict[str, str]:
    return {"status": "ready"}
