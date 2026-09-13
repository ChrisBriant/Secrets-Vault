from vault.generate_secrets import get_all_secrets
from data.models import Secret
from data.db import SessionLocal
import asyncio, json

async def add_secrets_to_database(secrets):
    #Add the secrets to the database
    async with SessionLocal() as session:
        paths = secrets.keys()
        for path in paths:
            path = path
            secrets_data = secrets[path]
            print("SECRET", json.dumps(secrets_data,indent=4))
            for key in secrets_data.keys():
                secret = secrets_data[key]
                await Secret.create_one(
                    session,
                    secret['username'],
                    secret['password'],
                    path
                )

if __name__ == "__main__":
    #Get the secrets from the vault
    secrets = get_all_secrets()
    print(json.dumps(secrets['animals'],indent=4))
    asyncio.run(add_secrets_to_database(secrets))

