from fastapi import APIRouter, HTTPException, Request, Depends, Response, Query
from auth.token import validate_ms_token
from data.models.entra_credential import EntraCredential
from data.models.models import Secret
from data.db import SessionLocal
from vault.vault_operations import add_or_update_secret_to_vault, get_vault_username_password
from data.schemas import VaultUsernamePasswordSchema, EntraCredentialSchema, EntraAppInputSchema
from entra.secrets import remove_secret_credentials_and_create_new, create_service_principal_and_secret
from datetime import datetime
from auth.get_entra_token import get_entra_token_management, get_entra_token
import json

router = APIRouter()

# @router.get("/status")
# async def status(token=Depends(validate_ms_token)):
#     """
#         This is a status page that demonstrates the client app authenticates
#         _____________________________________________________________________
#         Press "Authorize" at the tope of the page nad paste the MS token for the authorized app registration into the input and click "Authorize". 
#     """
#     return {
#         "status": "ok"
#     }

@router.post("/{object_id}/rotate", response_model=EntraCredentialSchema)
async def rotate_app_client_secret(
    object_id : str
):
    """
        Rotates the entra credential
    """
    token = get_entra_token_management()
    app_id, display_name, new_credential = await remove_secret_credentials_and_create_new(token,object_id)
    print("HERE")
    #Update in the database
    async with SessionLocal() as session:
        entra_credential = await EntraCredential.update_one_by_object_id(session,object_id,{
            "secret_id" : new_credential["keyId"],
            "display_name" : new_credential["displayName"],
            "start_date" : datetime.fromisoformat(new_credential["startDateTime"]),
            "end_date" : datetime.fromisoformat(new_credential["endDateTime"]),   
        })
        if not entra_credential:
            #Create new if there is not one to update
            entra_credential = await EntraCredential.create_one(
                session,
                new_credential["keyId"],
                object_id,
                app_id,
                display_name,
                datetime.fromisoformat(new_credential["startDateTime"].replace("Z", "+00:00")),
                datetime.fromisoformat(new_credential["endDateTime"].replace("Z", "+00:00")),
            )
        entra_credential_response = EntraCredentialSchema.model_validate(entra_credential)
        print("CREDENTIAL RESPONSE", entra_credential_response)
        try:
            add_or_update_secret_to_vault("entra",object_id,app_id,new_credential["secretText"])
        except Exception as e:
            raise HTTPException(status_code=400, detail="Unable to update the vault")
        if not entra_credential_response.secret:
            print("ADDING NEW SECRET")
            #Create in vault and then new secret in database
            add_or_update_secret_to_vault("entra",object_id,app_id,new_credential["secretText"])
            new_secret = await Secret.create_one(
                session,
                object_id,
                None,
                f"entra/{object_id}"
            )
            updated_entra_credential = await EntraCredential.update_one_by_object_id(session,object_id,{
                "secret" : new_secret,
            })
            entra_credential_response = EntraCredentialSchema.model_validate(updated_entra_credential)
        return entra_credential_response




@router.get("/{object_id}/credential", response_model=VaultUsernamePasswordSchema)
async def get_entra_credential_from_vault(
    object_id : str
):
    """
        Gets the entra credential from the vault
    """
    #Get the Entra object
    async with SessionLocal() as session:
        entra_credential = await EntraCredential.get_by_object_id(session,object_id)
        if not entra_credential:
            raise HTTPException(status_code=404, detail=f"Unable to find credential with object ID {object_id}.")

        if not entra_credential.secret:
            raise HTTPException(status_code=404, detail=f"Unable to find credential with object ID {object_id}.")
        #Find in the vault
        try:
            username, password = get_vault_username_password(entra_credential.secret.path)
            print("USERNAME AND PASSWORD", username, password)
            return VaultUsernamePasswordSchema(
                username = username,
                password = password,
                path =  entra_credential.secret.path
            )
        except Exception as e:
            print("ERROR",e)
            raise HTTPException(status_code=404, detail=f"Unable to find secret in vault.")

@router.post("/createapp",  response_model= EntraCredentialSchema)
async def create_entra_app(
    app_name : EntraAppInputSchema
):
    token = get_entra_token_management()
    new_service_principal = await create_service_principal_and_secret(token,app_name.app_name)
    print("NEW SERVICE PRINCIPAL", json.dumps(new_service_principal,indent=4))
    #Update in the database
    async with SessionLocal() as session:
        #Create new if there is not one to update
        password_credential = new_service_principal["passwordCredentials"][0]
        try:
            add_or_update_secret_to_vault("entra",new_service_principal["id"],password_credential["secretText"])
        except Exception as e:
            raise HTTPException(status_code=400, detail="Unable to update the vault")
        entra_credential = await EntraCredential.create_one(
            session,
            password_credential["keyId"],
            new_service_principal["id"],
            new_service_principal["appId"],
            new_service_principal["displayName"],
            datetime.fromisoformat(password_credential["startDateTime"].replace("Z", "+00:00")),
            datetime.fromisoformat(password_credential["endDateTime"].replace("Z", "+00:00")),
        )
        new_secret = await Secret.create_one(
            session,
            new_service_principal["id"],
            None,
            f"entra/{new_service_principal["id"]}"
        )
        entra_credential = await EntraCredential.update_one_by_object_id(session,new_service_principal["id"],{
            "secret" : new_secret,
        })
        print("ENTRA CREDENTIAL",entra_credential)
        entra_credential_response = EntraCredentialSchema.model_validate(entra_credential)
        print("CREDENTIAL RESPONSE", entra_credential_response)
        return entra_credential_response
