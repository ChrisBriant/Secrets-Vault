from fastapi import APIRouter, HTTPException, Request, Depends, Response, Query
from auth.token import validate_ms_token
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

router = APIRouter()

# #LOAD ENVIRONMENT
dotenv_file = ".env"
if os.path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)

VAULT_STATUS_APP_CREDENTIALS_PATH = "/entra/1fc41e5d-004b-4615-96d5-080c06a17fdc"
VAULT_URL = os.environ.get("VAULT_URL")
VAULT_TOKEN = os.environ.get("VAULT_TOKEN")


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


@router.get("/authenticate", response_model = str)
async def authenticate():
    """
        Endpoint that retrieves the credentials from the vault and attempts to authenticate with Entra.
        If successful it issues a JWT
    """
    #GET CREDENTIAL FROM THE VAULT    
    url = VAULT_URL + VAULT_STATUS_APP_CREDENTIALS_PATH

    headers = {
        "X-Vault-Token" : VAULT_TOKEN
    }

    response = requests.get(url,headers=headers)

    print("RESPONSE", response.status_code, response.text)
    response.raise_for_status()

    if response.status_code == 200:
        credential = response.json()["data"]["data"]
        username = credential["username"]
        password = credential["password"]
    
        #WITH THESE CREDENTIALS GET THE TOKEN FOR ACCESS TO THE STATUS APP
        try:
            status_access_token = get_status_app_token_from_entra(username,password)
            print("ACCESS TOKEN", status_access_token)
            #Validate the token
            try:
                valid =validate_ms_token_from_string(status_access_token)
                print("VALID", valid)
                if valid:
                    #ISSUE A JWT FOR THE CLIENT TO ACCESS THE STATUS PAGE
                    pass
            except Exception as e:
                print("TOKEN NOT VALID", e)
        except Exception as e:
            print("UNABLE TO GET THE TOKEN", e)
    return "Hello Mickey"    
