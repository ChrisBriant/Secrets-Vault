import requests
from auth.get_entra_token import get_entra_token_management
import json

def get_service_principals_with_secrets(access_token):
    # next_url = (
    #     "https://graph.microsoft.com/v1.0/servicePrincipals"
    #     "?$select=id,appId,displayName,passwordCredentials"
    # )

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


def main():
    token = get_entra_token_management()
    print("TOKEN", token)
    secret_data = get_service_principals_with_secrets(token)
    # print("SECRET DATA FROM ENTRA", json.dumps(secret_data,indent=4))
    # for secret_item in secret_data:
    #     if(len(secret_item["passwordCredentials"]) > 0):
    #         print(secret_item["displayName"])
    secrets_with_credentials = [s for s in secret_data if len(s["passwordCredentials"]) > 0]
    print("SECRET DATA FROM ENTRA", json.dumps(secrets_with_credentials,indent=4))


if __name__ =="__main__":
    main()


