from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routes.hashicorp import router as hashicorp_router
from routes.entra import router as entra_router
from routes.status_app import router as status_app_router
from routes.github import router as github_router
import os
import dotenv



# #LOAD ENVIRONMENT
dotenv_file = ".env"
if os.path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React app origin
    allow_credentials=True,                   # must be True for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hashicorp_router, prefix="/hashicorp")
app.include_router(entra_router, prefix="/entra")
app.include_router(status_app_router, prefix="/status-app")
app.include_router(github_router,prefix="/github")