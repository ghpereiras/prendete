from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, email, google_auth
from app.auth import create_access_token
from app.database import get_db
from app.schemas.auth import (
    EmailVerifyConfirm,
    GoogleLoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    ResendVerificationRequest,
    Token,
)
from app.security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

# Accounts can log in unverified for a grace period before being locked out —
# see the plan doc for why (registering doesn't prove the email is real, but
# blocking login immediately would be too much friction for a low-stakes app).
EMAIL_VERIFICATION_GRACE_DAYS = 7


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.user.get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.email_verified_at is None:
        grace_deadline = user.created_at + timedelta(days=EMAIL_VERIFICATION_GRACE_DAYS)
        if datetime.now(timezone.utc) > grace_deadline:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="email_not_verified")

    access_token = create_access_token(subject=user.email)
    return Token(access_token=access_token)


@router.post("/google", response_model=Token)
def login_with_google(body: GoogleLoginRequest, db: Session = Depends(get_db)):
    try:
        info = google_auth.verify_google_id_token(body.credential, body.nonce)
    except google_auth.GoogleUnavailable as exc:
        raise HTTPException(status_code=503, detail="Google sign-in unavailable") from exc
    except google_auth.InvalidGoogleToken as exc:
        raise HTTPException(status_code=401, detail="Invalid Google credential") from exc

    google_email = info["email"]
    user = crud.user.get_user_by_email(db, google_email)
    if user is None:
        email_prefix = google_email.split("@")[0]
        user = crud.user.create_google_user(
            db,
            email=google_email,
            first_name=info.get("given_name") or info.get("name") or email_prefix,
            last_name=info.get("family_name") or "",
            language=body.language,
            avatar=google_auth.fetch_profile_picture(picture) if (picture := info.get("picture")) else None,
        )
    elif user.email_verified_at is None:
        # Google just proved ownership of this address. The existing password
        # was set by whoever registered it first, who never proved the same, so
        # drop it — otherwise they could keep signing in to the real owner's account.
        user.email_verified_at = datetime.now(timezone.utc)
        user.hashed_password = None
        db.commit()

    return Token(access_token=create_access_token(subject=user.email))


@router.post("/verify-email", status_code=204)
def verify_email(body: EmailVerifyConfirm, db: Session = Depends(get_db)):
    token = crud.email_verification_token.get_valid_by_token(db, body.token)
    if token is None:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = crud.user.get_user(db, token.user_id)
    user.email_verified_at = datetime.now(timezone.utc)
    db.commit()


@router.post("/resend-verification", status_code=204)
def resend_verification(body: ResendVerificationRequest, db: Session = Depends(get_db)):
    user = crud.user.get_user_by_email(db, body.email)
    if user and user.email_verified_at is None:
        email.send_verification_email(db, user, language=body.language)


@router.post("/password-reset/request", status_code=204)
def request_password_reset(body: PasswordResetRequest, db: Session = Depends(get_db)):
    user = crud.user.get_user_by_email(db, body.email)
    if user:
        email.send_password_reset_email(db, user, language=body.language)


@router.post("/password-reset/confirm", status_code=204)
def confirm_password_reset(body: PasswordResetConfirm, db: Session = Depends(get_db)):
    token = crud.password_reset_token.get_valid_by_token(db, body.token)
    if token is None:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = crud.user.get_user(db, token.user_id)
    user.hashed_password = hash_password(body.new_password)
    crud.password_reset_token.mark_used(db, token)
    db.commit()
