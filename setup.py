from vault.generate_secrets import get_all_secrets, add_secrets_to_vault
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

async def clear_data():
    async with SessionLocal() as session:
        await Secret.purge_all(session)

async def main():
    #Purge the database
    await clear_data()
    #Generate the data in Hashicorp
    #Add secrets to the vault
    add_secrets_to_vault("animals", "secrets.json")
    #Get the secrets from the vault
    secrets = get_all_secrets()
    print(json.dumps(secrets['animals'],indent=4))
    #Add them to the database
    await add_secrets_to_database(secrets)

if __name__ == "__main__":
    asyncio.run(main())


