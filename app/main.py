from fastapi import FastAPI
from app.api.v1.endpoints.log.log_in_router import router as login_router
from app.api.v1.endpoints.log.sign_up_router import router as signup_router
from app.api.v1.endpoints.project.projects_router import router as projects_router
from app.api.v1.endpoints.note.note_router import router as note_router
from app.api.v1.endpoints.personal_goal.personal_goal_router import router as personal_goal_router
from app.api.v1.endpoints.reminder.reminder_router import router as reminder_router 
from app.api.v1.endpoints.notification.notification_router import router as notification_router
from app.api.v1.endpoints.dt.daily_task_router import router as daily_task_router
from app.api.v1.endpoints.assignment.assignment_router import router as assignment_router
from app.api.v1.endpoints.log.profile_setup import router as profile_setup_router
from app.api.v1.endpoints.project.sub_task_router import router as sub_task_router
from app.api.v1.endpoints.team.team_router import router as team_router
from app.api.v1.endpoints.sms.sms_router import router as sms_router
# নতুন Gemini রাউটার ইম্পোর্ট
from app.api.v1.endpoints.gemini_model.gemini_router import router as gemini_router 

from app.db.database import Base, engine
from app.model.device_token_model import DeviceToken
from app.model.notification_model import Notification
from app.model.user_model import User
from app.model.team_member_model import TeamMember
from app.model.sms_message_model import SmsMessage
from app.model.direct_chat_room_model import DirectChatRoom
from app.model.gemini_model import GeminiChat # নতুন মডেল

app = FastAPI()

@app.on_event("startup")
def create_missing_tables():
    Base.metadata.create_all(bind=engine)

# সব রাউটার রেজিস্ট্রেশন
app.include_router(login_router)
app.include_router(signup_router)
app.include_router(profile_setup_router)
app.include_router(projects_router)
app.include_router(sub_task_router)
app.include_router(note_router)
app.include_router(personal_goal_router)
app.include_router(reminder_router)
app.include_router(notification_router)
app.include_router(daily_task_router)
app.include_router(assignment_router)
app.include_router(team_router)
app.include_router(sms_router)
app.include_router(gemini_router) # Gemini রাউটার অ্যাড করা হলো

@app.get("/")
def home():
    return {"status": "Backend is running with Gemini AI integration"}