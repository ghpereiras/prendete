from pydantic import BaseModel, EmailStr

from app.schemas.user import Language


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EmailVerifyConfirm(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr
    # The page's current language at the moment of clicking "resend" — used
    # instead of the account's saved language, which may be stale (set back
    # when the account was first created, possibly in a different language).
    language: Language | None = None


class PasswordResetRequest(BaseModel):
    email: EmailStr
    language: Language | None = None


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
