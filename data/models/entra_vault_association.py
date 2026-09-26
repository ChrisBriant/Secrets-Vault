from __future__ import annotations
from ..db import Base, AsyncSession, SessionLocal
from typing import List
from sqlalchemy.exc import IntegrityError
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    select,
)
from sqlalchemy.orm import relationship, selectinload
from fastapi import HTTPException
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .entra_credential import EntraCredential
    from .models import Secret

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

    @classmethod
    async def create_association(
        cls,
        session: AsyncSession,
        entra_credential: EntraCredential,
        secret: Secret,
    ) -> EntraCredential:

        from .entra_credential import EntraCredential
        from .models import Secret

        association = cls(
            entra=entra_credential,
            vault=secret,
        )

        session.add(association)
        await session.commit()

        result = await session.execute(
            select(EntraCredential)
            .options(
                selectinload(EntraCredential.vault_associations)
            )
            .where(EntraCredential.id == entra_credential.id)
        )

        return result.scalar_one()