from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, event
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.db.database import Base
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, nullable=False)  # who receives notification

    title = Column(String, nullable=False)     # Project Title / Team Title
    message = Column(Text, nullable=False)     # assigned as manager etc.

    type = Column(String)  # "project", "team", "goal"

    reference_id = Column(Integer)  
    # project_id / team_id / goal_id (optional use)

    is_read = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)


@event.listens_for(Notification, "after_insert")
def notification_after_insert(mapper, connection, target):
    from app.services.push_notification_service import send_push_for_notification

    send_push_for_notification(
        connection=connection,
        user_id=target.user_id,
        title=target.title,
        message=target.message,
    )
