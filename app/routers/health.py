from fastapi import APIRouter


router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@router.get("/ready")
def readiness_check() -> dict[str, str]:
    return {"status": "ready"}
