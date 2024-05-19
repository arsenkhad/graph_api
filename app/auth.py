from datetime import datetime, timedelta, timezone
from typing import Annotated
from enum import Enum
from functools import total_ordering

from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .sql_app import crud, models, schemas
from .sql_app.db import get_db
from . import config

@total_ordering
class AccessLevels(Enum):
    not_accessible : int = 0
    read_access : int = 1
    edit_access : int = 2
    full_access : int = 3
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        if type(other) == int:
            return self.value < other
        return NotImplemented
    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return self.value == other.value
        if type(other) == int:
            return self.value == other
        return NotImplemented


class Token(BaseModel):
    access_token: str
    token_type: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")

auth = APIRouter()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(db : Session, user_cred : schemas.UserCredAuth):
    user = crud.get_user(db, user_cred.user_login)
    if not user:
        return False
    if not verify_password(user_cred.user_password, user.user_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=15)):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        user_login: str = payload.get("sub")
        if user_login is None:
            raise credentials_exception
        token_data = schemas.UserCred(user_login=user_login)
    except JWTError:
        raise credentials_exception
    user = crud.get_user(db, token_data.user_login)
    if user is None:
        raise credentials_exception
    return user


def check_access(
    db: Session,
    current_user: Annotated[models.User, Depends(get_current_user)],
    project_id: int,
    access_level: AccessLevels = AccessLevels.read_access,
):
    access = schemas.Access(user_login=current_user.user_login, project_id=project_id)
    db_access = crud.get_user_access(db, access)
    return (db_access and (db_access >= access_level))


@auth.post("/auth")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
) -> Token:
    user = authenticate_user(db, schemas.UserCredAuth(user_login=form_data.username, user_password=form_data.password))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data = {"sub": user.user_login},
        expires_delta = access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")