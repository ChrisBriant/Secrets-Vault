import requests, os, dotenv

# #LOAD ENVIRONMENT
dotenv_file = ".env"
if os.path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)


TENANT_ID = os.environ.get("ENTRA_TENANT_ID")
CLIENT_ID = os.environ.get("ENTRA_STATUS_APP_CLIENT_ID")
CLIENT_SECRET = os.environ.get("ENTRA_STATUS_APP_CLIENT_SECRET")
STATUS_PAGE_API_CLIENT_ID = os.environ.get("STATUS_PAGE_API_CLIENT_ID")
CLIENT_ID_MANGEMENT = os.environ.get("CLIENT_ID_MANGEMENT")
CLIENT_SECRET_MANAGEMENT = os.environ.get("CLIENT_SECRET_MANAGEMENT")



def get_entra_token():
    TOKEN_URL = (
        f"https://login.microsoftonline.com/"
        f"{TENANT_ID}/oauth2/v2.0/token"
    )

    token_response = requests.post(
        TOKEN_URL,
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": f"api://{STATUS_PAGE_API_CLIENT_ID}/.default",
            "grant_type": "client_credentials",
        },
    )

    print(token_response.status_code)
    print(token_response.json())

    token_response.raise_for_status()

    access_token = token_response.json()["access_token"]

    return access_token

def get_entra_token_management():
    TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    token_response = requests.post(
        TOKEN_URL,
        data={
            "client_id": CLIENT_ID_MANGEMENT,
            "client_secret": CLIENT_SECRET_MANAGEMENT,
            "scope": f"https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        },
    )

    print(token_response.status_code)
    print(token_response.text)

    token_response.raise_for_status()

    access_token = token_response.json()['access_token']

    return access_token



if __name__ == "__main__":
    access_token = get_entra_token()
    print("ACCESS TOKEN", access_token)