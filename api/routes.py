from fastapi import Request, APIRouter

# path param : "/api/home/{id}"

router = APIRouter()

@router.get("/api/home")
async def home(request: Request):
    try:
        return {"name": "Rashmika"}
    except Exception as err:
        return {"error": str(err)}, 500
