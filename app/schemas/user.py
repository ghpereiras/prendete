from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr

Language = Literal["es", "en"]


class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    language: Language | None = None
    avatar_base64: str | None = None


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    language: Language | None = None
    avatar_base64: str | None = None
    remove_avatar: bool = False


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    first_name: str
    last_name: str
    full_name: str
    language: str
    email_verified_at: datetime | None
    has_password: bool
    avatar_url: str | None
    created_at: datetime
