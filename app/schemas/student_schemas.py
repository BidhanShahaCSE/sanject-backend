from pydantic import BaseModel, ConfigDict


class StudentBase(BaseModel):
    department: str
    roll: str
    semester: str
    batch: str
    org_id: str
    org_name: str

class StudentCreate(StudentBase):
    pass
class StudentResponse(StudentBase):
    id: int
    model_config = {"from_attributes": True}