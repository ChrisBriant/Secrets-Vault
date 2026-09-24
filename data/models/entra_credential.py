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
from pathlib import Path
from datetime import datetime, timedelta, timezone
from .models import Secret



class EntraCredential(Base):
    __tablename__ = "entra_credentials"

    id = Column(Integer, primary_key=True, index=True)
    secret_id = Column(String, index=True)
    object_id = Column(String, index=True)
    client_id  = Column(String, index=True, unique=True)
    display_name = Column(String, index=True, unique=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    #vault_id = Column(Integer, ForeignKey("entra_vault_associations.id"), nullable=False)
    
    vault_associations = relationship(
        "EntraVaultAssociation",
        back_populates="entra",
    )

    @classmethod
    async def create_one(
        cls,
        db: AsyncSession,
        secret_id : str,
        object_id : str,
        client_id  : str,
        display_name : str,
        start_date : datetime,
        end_date : datetime,
    ):
        entra_credential = cls(
            secret_id = secret_id,
            object_id = object_id,
            client_id  = client_id,
            display_name = display_name,
            start_date = start_date,
            end_date = end_date,
        )

        try:
            db.add(entra_credential)
            await db.commit()
            await db.flush()
            await db.refresh(entra_credential)
        except IntegrityError as ie:
            print("Error inserting secret", ie)
            await db.rollback()

        inserted_secret = await db.execute(
            select(cls)
            .options(
                selectinload(cls.vault_associations)
            )
            .where(cls.id == entra_credential.id))

        return inserted_secret.scalar_one_or_none()

    @classmethod
    async def update_one(
        cls,
        db: AsyncSession,
        id: int,
        updates: dict,
    ):

        entra_credential_result = await db.execute(
            select(cls)
            .where(cls.id == id)
        )

        entra_credential = entra_credential_result.scalar_one_or_none()

        if entra_credential is None:
            return None


        #Get the list of fields
        update_items = updates.items()

        allowed_fields = {
            "secret_id",
            "object_id",
            "client_id",
            "display_name",
            "start_date",
            "end_date"
        }


        try:
            #Load the secret object with the updated values
            for field, value in update_items:

                if field not in allowed_fields:
                    continue

                if hasattr(entra_credential, field):
                    print("UPDATING", field, value)                    
                    setattr(entra_credential, field, value)

            #set the timestamp
            updated_date = datetime.now(timezone.utc)
            entra_credential.last_updated = updated_date

            await db.commit()
            await db.flush()
            await db.refresh(entra_credential)
        except IntegrityError as ie:
            print("Error updating entra credential", ie)
            await db.rollback()
            return None

        updated_entra_credential = await db.execute(
            select(cls)
            .where(cls.id == id)
        )

        return updated_entra_credential.scalar_one_or_none()


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
            Get all the credentials paginated
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

class EntraVaultAssociation(Base):
    __tablename__ = "entra_vault_associations"

    id = Column(Integer, primary_key=True, index=True)
    entra_id = Column(Integer, ForeignKey("entra_credentials.id"), nullable=False)
    vault_id =  Column(Integer, ForeignKey("secrets.id"), nullable=False)

    entra = relationship(
        "EntraCredential",
        back_populates="vault_associations",
    )

    vault = relationship(
        "Secret",
        back_populates="entra_associations",
    )    