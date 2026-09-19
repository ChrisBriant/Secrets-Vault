from fastapi import APIRouter, HTTPException, Request, Depends, Response, Query
from typing import Optional
from data.models import Secret
from data.db import SessionLocal
from data.schemas import (
    PaginatedResponse,
    SecretSchema
)
from vault.generate_secrets import rotate_secret
from typing import List
from pathlib import Path
import json
import os
#import bleach
import base64
from math import ceil

router = APIRouter()

# Go to project root (adjust parents[n] if needed)
#PROJECT_ROOT = Path(__file__).resolve().parents[1]


@router.get("/secrets")
async def get_secrets(
    request : Request,
    page : int = 1,
    page_size : int = 10,
):
    """
        Get the secrets from that are stored in the database
    """
    async with SessionLocal() as session:
        paginated_secrets, total = await Secret.get_all_paginated(
            session,
            page,
            page_size
        )

        all_secrets_result = [SecretSchema.model_validate(s) for s in paginated_secrets ]

        total_pages = ceil(total / page_size)

        #Build next page URL
        next_page: Optional[str] = None
        if len(paginated_secrets) == page_size:
            next_page = str(
                request.url.include_query_params(
                    page=page + 1,
                    page_size=page_size
                )
            )
        prev_page: Optional[str] = None
        if page > 0:
            prev_page = str(
                request.url.include_query_params(
                    page=page - 1,
                    page_size=page_size
                )
            )     

        return {
            "data": all_secrets_result,
            "next_page": next_page,
            "prev_page" : prev_page,
            "total": total,
            "total_pages": total_pages,
            "page": page,
            "page_size": page_size
        }

@router.post("/rotate/{secret_id}", response_model = SecretSchema)
async def rotate_secret_route(secret_id: int):
    """
        Rotates the secret by the ID and returns the updated secret
    """
    new_secret = await rotate_secret(secret_id)

    response = SecretSchema.model_validate(new_secret)

    return response

