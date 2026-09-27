import json
import secrets
import string
import random
import hvac
import dotenv
import os
from hvac.exceptions import InvalidPath
from data.db import SessionLocal
from data.models.models import Secret
from fastapi import HTTPException
import asyncio


# #LOAD ENVIRONMENT
dotenv_file = ".env"
if os.path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)

VAULT_ADDR = "http://127.0.0.1:8200"
VAULT_TOKEN = os.environ.get("VAULT_TOKEN")

# Connect to Vault
client = hvac.Client(
    url=VAULT_ADDR,
    token=VAULT_TOKEN
)


def add_or_update_secret_to_vault(path,username,password):
    if not client.is_authenticated():
        raise Exception("Vault authentication failed")
    
    secret = client.secrets.kv.v2.create_or_update_secret(
        path= f"{path}/{username}",
        secret={
            "username": username,
            "password": password
        }
    )
    print("SECRET", secret)