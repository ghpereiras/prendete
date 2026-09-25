from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    avatar_base64: str | None = None


class UserUpdate(BaseModel):
    full_name: str | None = None
    avatar_base64: str | None = None
    remove_avatar: bool = False


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    avatar_url: str | None
    created_at: datetime
