from ..db import Base, AsyncSession, SessionLocal
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
    created = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    last_updated = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    entra_associations = relationship(
        "EntraVaultAssociation",
        back_populates="vault",
    )

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

                if hasattr(secret, field):
                    print("UPDATING", field, value)                    
                    setattr(secret, field, value)

            #set the timestamp
            updated_date = datetime.now(timezone.utc)
            secret.last_updated = updated_date

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

    @classmethod
    async def get_all(cls, db: AsyncSession):
        """
            Get all of the secrets
        """
        result = await db.execute(
            select(cls)
        )
        return result.scalars().all()

    @classmethod
    async def get_all_paginated(cls,db:AsyncSession, page: int = 1 , page_size: int = 10):
        """
            Get all the secrets paginated
        """

        total_result = await db.execute(
            select(func.count()).select_from(cls)
        )
        total = total_result.scalar_one()

        #Get the paginated sessions
        offset = (page - 1) * page_size

        result = await db.execute(
            select(cls)
            .offset(offset)
            .limit(page_size)
        )

        return result.scalars().all(), total


    @classmethod
    async def purge_all(cls, db : AsyncSession):
        """
            Purge all the data in the table
        """
        rows = await db.execute(
            delete(cls)
        )
        print("ROWS", rows.rowcount)
        await db.commit()


