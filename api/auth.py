# api/auth.py

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta

# bring in the shared functions
from services.database import (
    create_user,
    get_user_by_email,
    get_user_by_username,
    verify_password,    # this is the one and only verify_password
    get_db_session,
)
from passlib.context import CryptContext

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

router = APIRouter(tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class UserIn(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/signup", response_model=UserOut)
async def signup(user: UserIn, db_session=Depends(get_db_session)):
    if await get_user_by_email(db_session, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if await get_user_by_username(db_session, user.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    # hash via the database module’s utilities
    created = await create_user(db_session, user.email, user.username, user.password)
    return {"id": created.id, "email": created.email, "username": created.username}


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db_session = Depends(get_db_session),
):
    user = await get_user_by_email(db_session, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return JSONResponse({
        "access_token": access_token,
        "token_type": "bearer",
        "id": user.id,
        "email": user.email,
        "username": user.username
    })

@router.post("/logout")
async def logout(request: Request):
    return {"message": "Logout successful."}
