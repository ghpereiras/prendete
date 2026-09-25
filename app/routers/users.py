from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app import crud
from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from app.utils.avatar import InvalidAvatarError, process_avatar

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=201)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    if crud.user.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=409, detail="Email already registered")

    avatar = None
    if user_in.avatar_base64:
        try:
            avatar = process_avatar(user_in.avatar_base64)
        except InvalidAvatarError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return crud.user.create_user(db, user_in, avatar=avatar)


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("", response_model=list[UserRead])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.user.list_users(db, skip, limit)


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = crud.user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}/avatar")
def get_user_avatar(user_id: int, db: Session = Depends(get_db)):
    # Unauthenticated on purpose: it's rendered via plain <img src="...">
    # tags (header, profile, attendee lists), which never send the JWT
    # bearer token used everywhere else in the API.
    user = crud.user.get_user(db, user_id)
    if not user or user.avatar is None:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return Response(
        content=user.avatar,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )
