from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import crud, schemas, models
from app.db import get_db
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.schemas import Token

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    if crud.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = hash_password(user_in.password)
    return crud.create_user(db, user_in, hashed)

@router.post("/token", response_model=Token)
def login_for_access_token(
    token_req: schemas.TokenRequest,
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_email(db, token_req.email)
    if not user or not verify_password(token_req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserRead)
def read_users_me(
    current_user: models.User = Depends(get_current_user)
):
    return current_user