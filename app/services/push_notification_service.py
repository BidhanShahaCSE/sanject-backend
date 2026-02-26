import json
import os
from datetime import timedelta

import firebase_admin
from firebase_admin import credentials, messaging
from firebase_admin.exceptions import FirebaseError
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from app.model.device_token_model import DeviceToken


def _initialize_firebase() -> bool:
    if firebase_admin._apps:
        return True

    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    service_account_file = os.getenv("FIREBASE_SERVICE_ACCOUNT_FILE")

    try:
        if service_account_json:
            cred_data = json.loads(service_account_json)
            cred = credentials.Certificate(cred_data)
            firebase_admin.initialize_app(cred)
            return True

        if service_account_file:
            cred = credentials.Certificate(service_account_file)
            firebase_admin.initialize_app(cred)
            return True
    except Exception:
        return False

    return False


def send_push_for_notification(connection, user_id: int, title: str, message: str) -> None:
    if not _initialize_firebase():
        return

    try:
        token_rows = connection.execute(
            select(DeviceToken.id, DeviceToken.fcm_token)
            .where(DeviceToken.user_id == user_id)
            .order_by(DeviceToken.created_at.desc())
        ).all()
    except SQLAlchemyError:
        return

    if not token_rows:
        return

    notification = messaging.Notification(
        title=title,
        body=message,
    )

    invalid_token_ids = []

    for token_id, token in token_rows:
        firebase_message = messaging.Message(
            token=token,
            notification=notification,
            android=messaging.AndroidConfig(
                priority="high",
                ttl=timedelta(hours=24),
                direct_boot_ok=True,
                notification=messaging.AndroidNotification(
                    channel_id="in_app_popup_channel_v2",
                    sound="default",
                    priority="max",
                    default_sound=True,
                    default_vibrate_timings=True,
                    visibility="public",
                ),
            ),
            data={
                "type": "app_notification",
                "user_id": str(user_id),
                "title": title,
                "body": message,
            },
        )

        try:
            messaging.send(firebase_message)
        except FirebaseError as exc:
            code = getattr(exc, "code", "") or ""
            if code in {"registration-token-not-registered", "invalid-argument"}:
                invalid_token_ids.append(token_id)

    if invalid_token_ids:
        try:
            connection.execute(
                delete(DeviceToken).where(DeviceToken.id.in_(invalid_token_ids))
            )
        except SQLAlchemyError:
            pass
