from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
import dotenv
from jwt import PyJWKClient
import requests
from datetime import datetime,timezone,timedelta


security = HTTPBearer()

# Settings for JWT
ALGORITHM = "HS256"             # Use HS256 or any preferred algorithm
ACCESS_TOKEN_LIFETIME = 7200      # Token lifetime in seconds
REFRESH_TOKEN_LIFETIME = 14400
SECRET_KEY = os.environ.get("SECRET_KEY")


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


def validate_ms_token_from_string(
    token: str
):
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

        return True
    except Exception as e:
        print("ERROR VALIDATING TOKEN", e)
        raise HTTPException(
            status_code=401,
            detail="Invalid access token"
        )

def obtain_jwt_pair(app_id):
    # 1. Generate Access Token (Short-lived)
    access_payload = {
        "sub": app_id,
        "type": "access",  # Important to distinguish types
        "exp": datetime.now(timezone.utc) + timedelta(seconds=ACCESS_TOKEN_LIFETIME),
    }
    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)

    # 2. Generate Refresh Token (Long-lived)
    refresh_payload = {
        "sub": app_id,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(seconds=REFRESH_TOKEN_LIFETIME),
    }
    refresh_token = jwt.encode(refresh_payload, os.environ.get("SECRET_KEY"), algorithm=ALGORITHM)

    return {
        "access": access_token,
        "refresh": refresh_token
    }

#GITHUB SETTINGS
GITHUB_ISSUER = "https://token.actions.githubusercontent.com"
GITHUB_AUDIENCE = "secrets-vault"

GITHUB_JWKS_URL = (
    "https://token.actions.githubusercontent.com/.well-known/jwks"
)

jwks_client = PyJWKClient(GITHUB_JWKS_URL)


def validate_github_token(token: str):
    """
        Validates that the github token is genuine by verifying the signature
    """
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=GITHUB_AUDIENCE,
            issuer=GITHUB_ISSUER,
        )

    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid GitHub OIDC token: {e}"
        )

    # Restrict this token to your repository
    if claims.get("repository") != "ChrisBriant/github-credential-rotation":
        raise HTTPException(
            status_code=403,
            detail="GitHub repository is not authorised"
        )

    return claims