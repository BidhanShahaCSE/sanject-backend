from pydantic import BaseModel, ConfigDict
from typing import Optional
class ManagerBase(BaseModel):
    department: str
    designation: str
    joining_year: int
    org_id: str
    org_name: str

class ManagerCreate(ManagerBase):
    pass
class ManagerOut(ManagerBase):
    id: int
    model_config = {"from_attributes": True}