from fastapi import APIRouter, HTTPException, Request, Depends, Response, Query
from auth.token import validate_ms_token


router = APIRouter()

@router.get("/status")
async def status(token=Depends(validate_ms_token)):
    """
        This is a status page that demonstrates the client app authenticates
        _____________________________________________________________________
        Press "Authorize" at the tope of the page nad paste the MS token for the authorized app registration into the input and click "Authorize". 
    """
    return {
        "status": "ok"
    }