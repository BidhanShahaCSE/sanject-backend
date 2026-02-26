from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List

from app.api.v1.endpoints.auth.auth_utils import get_current_user_email
from app.db.database import get_db
from app.model.direct_chat_room_model import DirectChatRoom
from app.model.sms_message_model import SmsMessage
from app.model.team_member_model import TeamMember
from app.model.team_model import Team
from app.model.user_model import User
from app.model.notification_model import Notification
from app.schemas.sms_schemas import (
    DirectConversationOut,
    DirectChatRoomOut,
    DirectSmsCreate,
    SmsMessageOut,
    TeamSmsCreate,
)

router = APIRouter(prefix="/sms", tags=["SMS"])


def _display_name_from_email(email: str) -> str:
    local = (email or "").split("@")[0].strip()
    if not local:
        return "User"
    return local[:1].upper() + local[1:]


def _assert_user_exists(db: Session, email: str) -> None:
    user = db.query(User).filter(func.lower(User.email) == email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {email}")


def _normalize_direct_pair(a: str, b: str) -> tuple[str, str]:
    left = (a or "").strip().lower()
    right = (b or "").strip().lower()
    if left <= right:
        return left, right
    return right, left


def _assert_team_member(db: Session, team_id: int, user_email: str) -> Team:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    user = db.query(User).filter(func.lower(User.email) == user_email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user.id,
    ).first()
    if not is_member:
        raise HTTPException(status_code=403, detail="You are not a member of this team")

    return team


@router.post("/direct", response_model=SmsMessageOut, status_code=status.HTTP_201_CREATED)
def send_direct_sms(
    payload: DirectSmsCreate,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    recipient = payload.recipient_email.strip().lower()
    message = payload.message.strip()

    if not recipient or "@" not in recipient:
        raise HTTPException(status_code=400, detail="Valid recipient_email is required")
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    _assert_user_exists(db, recipient)

    sender_user = (
        db.query(User)
        .filter(func.lower(User.email) == current_user_email.lower())
        .first()
    )
    recipient_user = (
        db.query(User)
        .filter(func.lower(User.email) == recipient.lower())
        .first()
    )

    sms = SmsMessage(
        sender_email=current_user_email,
        recipient_email=recipient,
        message=message,
    )
    db.add(sms)
    db.flush()

    sender_name = _display_name_from_email(current_user_email)
    recipient_name = _display_name_from_email(recipient)

    if sender_user:
        db.add(
            Notification(
                user_id=sender_user.id,
                title="Message Sent",
                message=f"You messaged to {recipient_name}",
                type="sms",
                reference_id=sms.id,
                is_read=False,
            )
        )

    if recipient_user:
        db.add(
            Notification(
                user_id=recipient_user.id,
                title="New Message",
                message=f"{sender_name} sent you a message",
                type="sms",
                reference_id=sms.id,
                is_read=False,
            )
        )

    db.commit()
    db.refresh(sms)
    return sms


@router.post("/direct/ensure-room", response_model=DirectChatRoomOut, status_code=status.HTTP_200_OK)
def ensure_direct_chat_room(
    payload: DirectSmsCreate,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    recipient = payload.recipient_email.strip().lower()
    if not recipient or "@" not in recipient:
        raise HTTPException(status_code=400, detail="Valid recipient_email is required")

    if recipient == current_user_email.strip().lower():
        raise HTTPException(status_code=400, detail="You cannot start chat with yourself")

    _assert_user_exists(db, recipient)
    _assert_user_exists(db, current_user_email)

    participant_one, participant_two = _normalize_direct_pair(current_user_email, recipient)

    room = (
        db.query(DirectChatRoom)
        .filter(
            DirectChatRoom.participant_one == participant_one,
            DirectChatRoom.participant_two == participant_two,
        )
        .first()
    )

    if room:
        return {
            "id": room.id,
            "recipient_email": recipient,
            "created_at": room.created_at,
            "existed": True,
        }

    room = DirectChatRoom(
        participant_one=participant_one,
        participant_two=participant_two,
    )
    db.add(room)
    db.commit()
    db.refresh(room)

    return {
        "id": room.id,
        "recipient_email": recipient,
        "created_at": room.created_at,
        "existed": False,
    }


@router.get("/direct/{recipient_email}", response_model=List[SmsMessageOut])
def get_direct_chat(
    recipient_email: str,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    recipient = recipient_email.strip().lower()
    _assert_user_exists(db, recipient)

    messages = (
        db.query(SmsMessage)
        .filter(SmsMessage.team_id.is_(None))
        .filter(
            or_(
                (SmsMessage.sender_email == current_user_email)
                & (SmsMessage.recipient_email == recipient),
                (SmsMessage.sender_email == recipient)
                & (SmsMessage.recipient_email == current_user_email),
            )
        )
        .order_by(SmsMessage.created_at.asc())
        .all()
    )
    return messages


@router.get("/direct-conversations", response_model=List[DirectConversationOut])
def get_direct_conversations(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    all_messages = (
        db.query(SmsMessage)
        .filter(SmsMessage.team_id.is_(None))
        .filter(
            or_(
                SmsMessage.sender_email == current_user_email,
                SmsMessage.recipient_email == current_user_email,
            )
        )
        .order_by(SmsMessage.created_at.desc())
        .all()
    )

    seen = set()
    conversations = []

    for msg in all_messages:
        if msg.sender_email == current_user_email:
            other = msg.recipient_email
        else:
            other = msg.sender_email

        if not other or other in seen:
            continue

        seen.add(other)
        conversations.append(
            {
                "id": msg.id,
                "recipient_email": other,
                "last_message": msg.message,
                "created_at": msg.created_at,
            }
        )

    return conversations


@router.get("/message/{message_id}", response_model=SmsMessageOut)
def get_message_by_id(
    message_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    sms = db.query(SmsMessage).filter(SmsMessage.id == message_id).first()
    if not sms:
        raise HTTPException(status_code=404, detail="Message not found")

    if sms.team_id is None:
        participants = {sms.sender_email, sms.recipient_email}
        if current_user_email not in participants:
            raise HTTPException(status_code=403, detail="Not allowed")
    else:
        _assert_team_member(db, sms.team_id, current_user_email)

    return sms


@router.post("/team/{team_id}", response_model=SmsMessageOut, status_code=status.HTTP_201_CREATED)
def send_team_sms(
    team_id: int,
    payload: TeamSmsCreate,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    team = _assert_team_member(db, team_id, current_user_email)
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    sms = SmsMessage(
        sender_email=current_user_email,
        team_id=team_id,
        message=message,
    )
    db.add(sms)
    db.flush()

    sender_user = (
        db.query(User)
        .filter(func.lower(User.email) == current_user_email.lower())
        .first()
    )
    sender_name = _display_name_from_email(current_user_email)

    members = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id)
        .all()
    )

    if sender_user:
        db.add(
            Notification(
                user_id=sender_user.id,
                title="Team Message Sent",
                message=f"You messaged to team '{team.team_name}'",
                type="sms",
                reference_id=team_id,
                is_read=False,
            )
        )

    for member in members:
        if sender_user and member.user_id == sender_user.id:
            continue

        db.add(
            Notification(
                user_id=member.user_id,
                title="Team Message",
                message=f"{sender_name} sent a message in '{team.team_name}'",
                type="sms",
                reference_id=team_id,
                is_read=False,
            )
        )

    db.commit()
    db.refresh(sms)
    return sms


@router.get("/team/{team_id}", response_model=List[SmsMessageOut])
def get_team_sms(
    team_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    _assert_team_member(db, team_id, current_user_email)

    messages = (
        db.query(SmsMessage)
        .filter(SmsMessage.team_id == team_id)
        .order_by(SmsMessage.created_at.asc())
        .all()
    )
    return messages
