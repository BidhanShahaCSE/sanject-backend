from pydantic import BaseModel, ConfigDict

class EmployeeBase(BaseModel):
    employee_id: str
    joining_year: int
    org_id: str
    org_name: str

class EmployeeCreate(EmployeeBase):
    pass
class EmployeeOut(EmployeeBase):
    id: int
    model_config = {"from_attributes": True}