from .db import Base, AsyncSession, SessionLocal
from typing import List
from sqlalchemy.exc import IntegrityError
from sqlalchemy import (
    Column,
    Integer,
    insert,
    String,
    Text,
    ForeignKey,
    DateTime,
    func,
    Enum,
    select,
    delete,
    Boolean,
    update,
    Table,
    CheckConstraint,
    text
)
from sqlalchemy.orm import relationship, selectinload
from fastapi import HTTPException
import enum
import os, dotenv
from pathlib import Path
import json
import asyncio
import random
from datetime import datetime, timedelta, timezone
import secrets


class Secret(Base):
    __tablename__ = "secrets"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    path = Column(String, nullable=False)

    @classmethod
    async def create_one(
        cls,
        db: AsyncSession,
        username : str,
        password: str,
        path : str,
    ):

        secret = cls(
            username = username,
            password= password,
            path = path,
        )

        try:
            db.add(secret)
            await db.commit()
            await db.flush()
            await db.refresh(secret)
        except IntegrityError as ie:
            print("Error inserting secret", ie)
            await db.rollback()

        inserted_secret = await db.execute(
            select(cls)
            .where(cls.id == secret.id))

        return inserted_secret.scalar_one_or_none()

    @classmethod
    async def update_one(
        cls,
        db: AsyncSession,
        id: int,
        updates: dict,
    ):

        secret_result = await db.execute(
            select(cls)
            .where(cls.id == id)
        )

        secret = secret_result.scalar_one_or_none()

        if secret is None:
            return None

        #Get the list of fields
        update_items = updates.items()

        allowed_fields = {
            "username",
            "password",
            "path",
        }

        try:
            #Load the secret object with the updated values
            for field, value in update_items:

                if field not in allowed_fields:
                    continue

                if hasattr(field, value):
                    setattr(secret, field, value)

            await db.commit()
            await db.flush()
            await db.refresh(secret)
        except IntegrityError as ie:
            print("Error updating secret", ie)
            await db.rollback()
            return None

        updated_secret = await db.execute(
            select(cls)
            .where(cls.id == id)
        )

        return updated_secret.scalar_one_or_none()


    @classmethod
    async def delete_by_id(
        cls,
        db: AsyncSession,
        id : int
    ):
        result = await db.execute(
            delete(cls).where(cls.id == id)
        )

        await db.commit()

        if result.rowcount > 0:
            return True
        else:
            return False

    @classmethod
    async def get_by_id(cls, db: AsyncSession, secret_id: int):
        """
        Retrieve a secret by ID
        """
        result = await db.execute(
            select(cls)
            .where(cls.id == secret_id)
        )
        return result.scalar_one_or_none()

    async def get_all(cls, db: AsyncSession):
        """
            Get all of the secrets
        """
        result = await db.execute(
            select(cls)
        )
        return result.scalars().all()