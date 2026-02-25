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
app = FastAPI()

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
app.include_router(profile_setup_router)
app.include_router(team_router)
