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


def generate_secret():
    # Characters used for the generated secrets
    characters = string.ascii_letters + string.digits + "!@#$%^&*"

    # Generate the secrets
    return "".join(secrets.choice(characters) for _ in range(32))



def generate_random_secrets_json():
    INPUT_FILE = "random_animals_list.txt"
    OUTPUT_FILE = "secrets.json"

    # Read words
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]

    # Randomly select words without duplicates
    selected_words = random.sample(words, min(30, len(words)))

    # Characters used for the generated secrets
    characters = string.ascii_letters + string.digits + "!@#$%^&*"

    # Generate the secrets
    secret_data = {
        word: "".join(secrets.choice(characters) for _ in range(32))
        for word in selected_words
    }

    # Write JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(secret_data, f, indent=4)

    print(f"Generated {len(secret_data)} secrets in {OUTPUT_FILE}")


# def add_secrets_to_vault():


#     # Connect to Vault
#     client = hvac.Client(
#         url=VAULT_ADDR,
#         token=VAULT_TOKEN
#     )

#     # Check authentication
#     if not client.is_authenticated():
#         raise Exception("Vault authentication failed")

#     # Read secrets.json
#     with open("secrets.json", "r", encoding="utf-8") as f:
#         secrets_data = json.load(f)

#     # Add each credential to Vault
#     for name, password in secrets_data.items():
#         print("CREDENTIALS", name, password)

#         client.secrets.kv.v2.create_or_update_secret(
#             mount_point="secret",
#             path=name,
#             secret={
#                 "username": name,
#                 "password": password
#             }
#         )

#         print(f"Added: secret/{name}")


def add_secrets_to_vault(path_name, file_name):

    # Connect to Vault
    client = hvac.Client(
        url=VAULT_ADDR,
        token=VAULT_TOKEN
    )

    # Check authentication
    if not client.is_authenticated():
        raise Exception("Vault authentication failed")

    # Read secrets JSON
    with open(file_name, "r", encoding="utf-8") as f:
        secrets_data = json.load(f)

    # Add each credential to Vault
    for name, password in secrets_data.items():
        print("CREDENTIALS", name, password)

        client.secrets.kv.v2.create_or_update_secret(
            mount_point="secret",
            path=f"{path_name}/{name}",
            secret={
                "username": name,
                "password": password
            }
        )

        print(f"Added: secret/{path_name}/{name}")


def get_all_secrets():
    client = hvac.Client(
        url=VAULT_ADDR,
        token=VAULT_TOKEN
    )

    if not client.is_authenticated():
        raise Exception("Vault authentication failed")

    def walk_path(path=""):
        result = {}

        try:
            response = client.secrets.kv.v2.list_secrets(
                mount_point="secret",
                path=path
            )
        except InvalidPath as invalid_path:
            print("INVALID PATH")
            response = None
        except Exception as e:
            print("ERROR", e)
            response = None        

        if response:
            for key in response["data"]["keys"]:

                full_path = f"{path}/{key}".strip("/")

                # Vault uses a trailing / to indicate another path
                if key.endswith("/"):
                    result[key.rstrip("/")] = walk_path(full_path)

                else:
                    secret = client.secrets.kv.v2.read_secret_version(
                        mount_point="secret",
                        path=full_path
                    )

                    result[key] = secret["data"]["data"]

        return result

    return walk_path()


async def rotate_secret(secret_id):
    #Generate a new secret
    new_secret = generate_secret()
    updated_secret = None
    async with SessionLocal() as session:
        #secret = await Secret.get_by_id(session,secret_id)
        #Update in database
        updated_secret = await Secret.update_one(session,secret_id,{
            "password" : new_secret
        })
    if not updated_secret:
        raise HTTPException(status_code=404,detail="Unable to find secret")
    #Update in the vault
    client = hvac.Client(
        url=VAULT_ADDR,
        token=VAULT_TOKEN
    )

    if not client.is_authenticated():
        raise Exception("Vault authentication failed")
    
    client.secrets.kv.v2.create_or_update_secret(
        path= f"{updated_secret.path}/{updated_secret.username}",
        secret={
            "username": updated_secret.username,
            "password": updated_secret.password
        }
    )

    return updated_secret

def get_secret_by_path(path):
    secret = client.secrets.kv.v2.read_secret_version(
        mount_point="secret",
        path=path
    )
    return secret


if __name__ == "__main__":
    #Generate random secrets file
    #reponse_data = generate_random_secrets_json()
    #Add secrets to the vault
    #add_secrets_to_vault("animals", "secrets.json")
    #Get all of the secrets
    #all_secrets = get_all_secrets()
    #print("ALL SECRETS", json.dumps(all_secrets, indent=4))
    #Rotate a secret
    #asyncio.run(rotate_secret(61))
    secret_from_vault = get_secret_by_path("animals/alligator")
    print("RETRIEVED SECRET", secret_from_vault)


