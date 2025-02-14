from pydantic import BaseModel, field_validator 
from uuid import UUID

class User(BaseModel):
    id: str | None = None
    username: str | None = None
    email: str | None = None
    full_name: str | None = None
    is_active: bool | None = None

    @field_validator('id', mode='before')
    def convert_uuid_to_str(cls, value):
        if isinstance(value, UUID):
            return str(value)
        return value

    class Config:
        from_attributes = True
