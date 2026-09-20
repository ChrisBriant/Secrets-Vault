from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
import dotenv
from jwt import PyJWKClient
import requests


security = HTTPBearer()

# #LOAD ENVIRONMENT
dotenv_file = ".env"
if os.path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)

TENANT_ID = os.environ.get("ENTRA_TENANT_ID")
API_CLIENT_ID = f"api://{os.environ.get("STATUS_PAGE_API_CLIENT_ID")}"
#API_CLIENT_ID = "api://852ea681-0ca0-4439-91a9-86740376d847"

ISSUER = f"https://sts.windows.net/{TENANT_ID}/"
JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"

jwks = requests.get(JWKS_URL).json()


def validate_ms_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"

        jwks_client = PyJWKClient(JWKS_URL)

        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=API_CLIENT_ID,
            issuer=ISSUER,
        )

        return payload
    except Exception as e:
        print("ERROR VALIDATING TOKEN", e)
        raise HTTPException(
            status_code=401,
            detail="Invalid access token"
        )
