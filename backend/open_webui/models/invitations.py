import time
import uuid
from typing import Optional

from open_webui.internal.db import Base, get_db
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Integer, Boolean, Text, select, and_


####################
# Invitation DB Schema
####################


class Invitation(Base):
    __tablename__ = "invitation"

    id = Column(String, primary_key=True, unique=True)
    group_id = Column(String)  # FK to groups table
    created_by = Column(String)  # FK to user who created invitation (manager/admin)
    token = Column(String, unique=True, index=True)  # Unique token for invitation link

    # Optional fields for invitation control
    max_uses = Column(Integer, nullable=True)  # null = unlimited
    current_uses = Column(Integer, default=0)
    expires_at = Column(BigInteger, nullable=True)  # Unix timestamp, null = never expires
    status = Column(String, default="active")  # active, expired, disabled

    # Metadata
    note = Column(Text, nullable=True)  # Optional note about invitation purpose

    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class InvitationModel(BaseModel):
    id: str
    group_id: str
    created_by: str
    token: str

    max_uses: Optional[int] = None
    current_uses: int = 0
    expires_at: Optional[int] = None
    status: str = "active"

    note: Optional[str] = None

    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


####################
# DB Helper Methods
####################


class InvitationTable:
    def insert_new_invitation(
        self,
        group_id: str,
        created_by: str,
        token: str,
        max_uses: Optional[int] = None,
        expires_at: Optional[int] = None,
        note: Optional[str] = None,
    ) -> Optional[InvitationModel]:
        with get_db() as db:
            invitation = InvitationModel(
                **{
                    "id": str(uuid.uuid4()),
                    "group_id": group_id,
                    "created_by": created_by,
                    "token": token,
                    "max_uses": max_uses,
                    "current_uses": 0,
                    "expires_at": expires_at,
                    "status": "active",
                    "note": note,
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                }
            )

            try:
                result = Invitation(**invitation.model_dump())
                db.add(result)
                db.commit()
                db.refresh(result)
                return InvitationModel.model_validate(result)
            except Exception as e:
                db.rollback()
                return None

    def get_invitation_by_id(self, invitation_id: str) -> Optional[InvitationModel]:
        with get_db() as db:
            invitation = db.query(Invitation).filter_by(id=invitation_id).first()
            return InvitationModel.model_validate(invitation) if invitation else None

    def get_invitation_by_token(self, token: str) -> Optional[InvitationModel]:
        with get_db() as db:
            invitation = db.query(Invitation).filter_by(token=token).first()
            return InvitationModel.model_validate(invitation) if invitation else None

    def get_invitations_by_group_id(self, group_id: str) -> list[InvitationModel]:
        with get_db() as db:
            invitations = db.query(Invitation).filter_by(group_id=group_id).all()
            return [InvitationModel.model_validate(inv) for inv in invitations]

    def get_invitations_by_creator(self, created_by: str) -> list[InvitationModel]:
        with get_db() as db:
            invitations = db.query(Invitation).filter_by(created_by=created_by).all()
            return [InvitationModel.model_validate(inv) for inv in invitations]

    def increment_invitation_uses(self, invitation_id: str) -> Optional[InvitationModel]:
        with get_db() as db:
            try:
                invitation = db.query(Invitation).filter_by(id=invitation_id).first()
                if invitation:
                    invitation.current_uses += 1
                    invitation.updated_at = int(time.time())

                    # Check if max uses reached
                    if invitation.max_uses and invitation.current_uses >= invitation.max_uses:
                        invitation.status = "expired"

                    db.commit()
                    db.refresh(invitation)
                    return InvitationModel.model_validate(invitation)
                return None
            except Exception as e:
                db.rollback()
                return None

    def update_invitation_status(
        self, invitation_id: str, status: str
    ) -> Optional[InvitationModel]:
        with get_db() as db:
            try:
                invitation = db.query(Invitation).filter_by(id=invitation_id).first()
                if invitation:
                    invitation.status = status
                    invitation.updated_at = int(time.time())
                    db.commit()
                    db.refresh(invitation)
                    return InvitationModel.model_validate(invitation)
                return None
            except Exception as e:
                db.rollback()
                return None

    def delete_invitation_by_id(self, invitation_id: str) -> bool:
        with get_db() as db:
            try:
                invitation = db.query(Invitation).filter_by(id=invitation_id).first()
                if invitation:
                    db.delete(invitation)
                    db.commit()
                    return True
                return False
            except Exception as e:
                db.rollback()
                return False

    def is_invitation_valid(self, token: str) -> bool:
        """Check if invitation is valid (active, not expired, not maxed out)"""
        invitation = self.get_invitation_by_token(token)
        if not invitation:
            return False

        # Check status
        if invitation.status != "active":
            return False

        # Check expiration
        if invitation.expires_at and invitation.expires_at < int(time.time()):
            return False

        # Check max uses
        if invitation.max_uses and invitation.current_uses >= invitation.max_uses:
            return False

        return True


Invitations = InvitationTable()
