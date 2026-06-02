from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/add")
def add(a: int = Query(...), b: int = Query(...)):
    return {"result": a + b}
