import json
import os

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
        token_row = connection.execute(
            select(DeviceToken.fcm_token).where(DeviceToken.user_id == user_id)
        ).first()
    except SQLAlchemyError:
        return

    token = token_row[0] if token_row else None
    if not token:
        return

    notification = messaging.Notification(
        title=title,
        body=message,
    )

    firebase_message = messaging.Message(
        token=token,
        notification=notification,
        android=messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                channel_id="in_app_popup_channel_v2",
                sound="default",
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
    except FirebaseError:
        try:
            connection.execute(
                delete(DeviceToken)
                .where(DeviceToken.user_id == user_id)
            )
        except SQLAlchemyError:
            pass
