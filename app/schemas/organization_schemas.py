from pydantic import BaseModel, ConfigDict

class OrganizationBase(BaseModel):
    org_id: str
    org_name: str

class OrganizationCreate(OrganizationBase):
    pass
class OrganizationOut(OrganizationBase):
    id: int
    model_config = {"from_attributes": True}