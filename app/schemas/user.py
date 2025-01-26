from pydantic import BaseModel

class User(BaseModel):
    id: str | None = None
    username: str | None = None
    email: str | None = None
    full_name: str | None = None
    is_active: bool | None = None

