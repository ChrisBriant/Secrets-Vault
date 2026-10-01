from fastapi import APIRouter, HTTPException, Header, Request, Depends, Response, Query
from auth.token import validate_ms_token, validate_github_token
from data.models.entra_credential import EntraCredential
from data.models.models import Secret
from data.db import SessionLocal
from vault.vault_operations import add_or_update_secret_to_vault, get_vault_username_password
from data.schemas import VaultUsernamePasswordSchema, EntraCredentialSchema, EntraAppInputSchema
from entra.secrets import remove_secret_credentials_and_create_new, create_service_principal_and_secret
from datetime import datetime
from auth.get_entra_token import get_status_app_token_from_entra
from auth.token import validate_ms_token_from_string
import json, os, dotenv, requests
from auth.token import (
    obtain_jwt_pair, 
    ACCESS_TOKEN_LIFETIME,
    REFRESH_TOKEN_LIFETIME
)


router = APIRouter()

# #LOAD ENVIRONMENT
dotenv_file = ".env"
if os.path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)


@router.post("/auth")
async def github_auth(request: Request, authorization: str = Header(None)):
    """
        This is a status page that demonstrates the client app authenticates
        _____________________________________________________________________
        Press "Authorize" at the tope of the page nad paste the MS token for the authorized app registration into the input and click "Authorize". 
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header"
        )

    token = authorization.removeprefix("Bearer ")

    try:
        claims = validate_github_token(token)
    except HTTPException as http_error:
        raise
    except Exception as e:
        print("ERROR VALIDATING TOKEN", e)

    print("GitHub token validated")
    print("Repository:", claims["repository"])
    print("Workflow:", claims["workflow"])
    print("Actor:", claims["actor"])

    return {
        "status": "authenticated",
        "repository": claims["repository"],
        "workflow": claims["workflow"],
    }