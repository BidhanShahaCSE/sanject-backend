from app.db.database import Base, engine
from app.model.assignment_model import Assignment
from app.model.assignment_subtask_model import AssignmentSubTask
from app.model.daily_task_model import DailyTask
from app.model.employee_model import Employee
from app.model.manager_model import Manager
from app.model.note_model import Note
from app.model.notification_model import Notification
from app.model.organization_model import Organization
from app.model.personal_goal_model import PersonalGoal
from app.model.project_member_model import ProjectMember
from app.model.project_model import Project
from app.model.reminder_model import Reminder
from app.model.student_models import Student
from app.model.subtask_model import SubTask
from app.model.task_model import Task
from app.model.teacher_models import Teacher
from app.model.team_model import Team
from app.model.user_model import User

Base.metadata.create_all(bind=engine)
print("Tables created successfully!")