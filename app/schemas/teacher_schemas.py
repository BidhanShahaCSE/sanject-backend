from pydantic import BaseModel
from typing import Optional
from pydantic import BaseModel, ConfigDict
class TeacherBase(BaseModel):
    department: str
    designation: str
    joining_year: int
    org_id: str
    org_name: str

class TeacherCreate(TeacherBase):
    pass
class TeacherResponse(TeacherBase):
    id: int
    model_config = {"from_attributes": True}