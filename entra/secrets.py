import requests
from auth.get_entra_token import get_entra_token_management
import json, asyncio
from data.models.entra_credential import EntraCredential
from data.models.entra_vault_association import EntraVaultAssociation
from data.models.models import Secret
from data.db import SessionLocal
from data.schemas import EntraCredentialSchema
from datetime import datetime, timedelta, timezone
from vault.generate_secrets import add_secret_to_vault

def get_service_principals_with_secrets(access_token):


    next_url = (
        "https://graph.microsoft.com/v1.0/applications"
        "?$select=id,appId,displayName,passwordCredentials"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    secrets_data = []
    while next_url:
        response = requests.get(
            next_url,
            headers= headers
            #json=payload,
        )

        print(response.status_code)
        print(response.text)

        response.raise_for_status()
        response_data = response.json()

        secrets_data.extend(response_data["value"]) 
        next_url = response_data.get("@odata.nextLink")

    return secrets_data


async def rotate_secret_in_entra(access_token,app_id,secret_id,secret_name):
    url = (
        f"https://graph.microsoft.com/v1.0/applications/{app_id}/addPassword"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    #Set the end date time of the credential
    end_date_time = (
        datetime.now(timezone.utc) + timedelta(hours=24)
    ).isoformat().replace("+00:00", "Z")

    payload = {
        "passwordCredential": {
            "displayName": secret_name,
            "endDateTime": end_date_time
        }
    }

    new_secret_response = requests.post(url,headers=headers,json=payload)

    print("RESPONSE", new_secret_response.status_code, new_secret_response.text)

    new_secret_response.raise_for_status()

    #Delete the old secret    
    # url = (
    #     f"https://graph.microsoft.com/v1.0/applications/{app_id}/removePassword"
    # )

    # payload = {
    #     "keyId": secret_id
    # }

    # for attempt in range(5):
    #     delete_response = requests.post(url,headers=headers,json=payload)

    #     if delete_response.status_code == 204:
    #         break

    #     if delete_response.status_code == 409:
    #         await asyncio.sleep(2)
    #         continue

    # print("REMOVED OLD SECRET", delete_response.status_code, delete_response.text)

    # delete_response.raise_for_status()

    return new_secret_response.json()



async def main():
    token = get_entra_token_management()
    print("TOKEN", token)
    secret_data = get_service_principals_with_secrets(token)
    # print("SECRET DATA FROM ENTRA", json.dumps(secret_data,indent=4))
    # for secret_item in secret_data:
    #     if(len(secret_item["passwordCredentials"]) > 0):
    #         print(secret_item["displayName"])
    secrets_with_credentials = [s for s in secret_data if len(s["passwordCredentials"]) > 0]
    print("SECRET DATA FROM ENTRA", json.dumps(secrets_with_credentials,indent=4))
    #UPDATE DATABASE
    entra_credentials = []
    async with SessionLocal() as session:
        for app_registration in secrets_with_credentials:
            for credential in app_registration["passwordCredentials"]:
                try:
                    entra_credential = await EntraCredential.create_one(
                                                session,
                                                credential["keyId"],
                                                app_registration["id"],
                                                app_registration["appId"],
                                                app_registration["displayName"],
                                                datetime.fromisoformat(credential["startDateTime"].replace("Z", "+00:00")),
                                                datetime.fromisoformat(credential["endDateTime"].replace("Z", "+00:00")),
                                            )
                except AttributeError as ae:
                    print("ATTRIBUTE ERROR", ae)
                if entra_credential:
                    entra_credentials.append(entra_credential)
    credentials_as_dicts = [
        {k: v for k, v in c.__dict__.items() if k != "_sa_instance_state"}
        for c in entra_credentials
    ]
    #Get the entra metadata
    async with SessionLocal() as session:
        entra_metadata = await EntraCredential.get_all(session)
        entra_credentials = [ EntraCredentialSchema.model_validate(cred) for cred in entra_metadata]
        print("THESE ARE ENTRA CREDENTIALS", entra_credentials)
    #Put the secret in the vault
    object_id = '1fc41e5d-004b-4615-96d5-080c06a17fdc'
    async with SessionLocal() as session:
        entra_credential_to_rotate = await EntraCredential.get_by_object_id(session,object_id)
        print("CREDENTIAL TO ROTATE", entra_credential_to_rotate.display_name, entra_credential_to_rotate.secret_id)
        # display_name = 'status page authentication'
        # secret_id = '9dfc4110-c3bb-4bbb-a04a-7836223b9958'
        new_secret = await rotate_secret_in_entra(token,object_id,entra_credential_to_rotate.secret_id,entra_credential_to_rotate.display_name)
        #Update entra secret
        print("THE NEW SECRET IS",json.dumps(new_secret, indent=4))
        updated_entra_credential = await EntraCredential.update_one(session,id=entra_credential_to_rotate.id, updates={
            "secret_id" : new_secret["keyId"],
            "display_name" : new_secret["displayName"],
            "start_date" : datetime.fromisoformat(new_secret["startDateTime"]),
            "end_date" : datetime.fromisoformat(new_secret["endDateTime"]),        
        })
        
        #Add to the vault
        add_secret_to_vault("entra",object_id,new_secret["secretText"])
        #Add to database
        new_secret = await Secret.create_one(
            session,
            object_id,
            None,
            f"entra/{object_id}"
        )
        #Update the association
        associated_entra_credential = await EntraVaultAssociation.create_association(
            session,
            updated_entra_credential,
            new_secret,
        )
        credential_response = EntraCredentialSchema.model_validate(associated_entra_credential)
        print("NEW CREDENTIAL", credential_response)

# THE NEW SECRET IS {
#     "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#microsoft.graph.passwordCredential",
#     "customKeyIdentifier": null,
#     "displayName": "status page authentication",
#     "endDateTime": "2026-09-27T02:39:45.799393Z",
#     "hint": ".oa",
#     "keyId": "9dfc4110-c3bb-4bbb-a04a-7836223b9958",
#     "secretText": "REMOVED",
#     "startDateTime": "2026-09-26T02:39:46.0148794Z"
# }



    print(json.dumps(credentials_as_dicts, indent=4, default=str))

if __name__ =="__main__":
    asyncio.run(main()) 


