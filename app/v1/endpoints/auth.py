# TODO
# 1. update errors for the functions and endpoints
# 2. create user schemas ,token schemas , etc schemas

from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Cookie, Request, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.login import LoginRequest, LoginResponse
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash
from app.config.logger import logger
import uuid
from jose import JWTError, jwt

from app.core.helper import row2dict
from app.core.auth import (
    token_auth,
    create_access_token,
    create_refresh_token,
    refresh_access_token,
)
from app.config.constants import REFRESH_TOKEN_EXPIRE_DAYS
from app.core.config import settings
from app.schemas.login import RegisterRequest, RegisterResponse, Token
from app.schemas.user import User

router = APIRouter(prefix="/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# TODO
def get_user(username: str = "", user_id: str = "", db: Session = Depends(get_db)):
    try:
        user_id = uuid.UUID(user_id)  # TODO: double check this
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid UUID in token")

    if username is ("" or None):
        raise HTTPException(status_code=401, detail="Invalid username")

    query = "SELECT * FROM users WHERE username = :username AND id = :id"
    user = db.execute(text(query), {"username": username, "id": user_id}).first()

    return row2dict(user)


async def get_current_user(
    request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> dict | None:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials 1",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        logger.debug("get current 1")
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        logger.debug("get current 2")
        user_id = payload.get("sub")  # uuid is stored as a string in the jwt
        logger.debug("get current 2.5")
        username = payload.get("name")
        logger.debug("get current 3")
        if username is None or user_id is None:
            logger.debug("get current user err 1")
            # raise credentials_exception

    except Exception as e:
        logger.debug("get current user err 2 {e}")
        # raise credentials_exception

    # user = get_user(username, user_id, db)

    # return user
    return None


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    logger.info(f"Login attempt with email: {login_data.email}")

    # Get user and hashed password
    query = """
        SELECT id, email, password_hash
        FROM users
        WHERE email = :email
    """

    res = db.execute(text(query), {"email": login_data.email}).first()

    if (
        not res
        or not res.email
        or not verify_password(login_data.password, res.password_hash)
    ):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token(
        data={"sub": str(res.id), "name": res.email, "iat": datetime.now()}
    )

    refresh_token = create_refresh_token(
        data={"sub": str(res.id), "name": res.email, "iat": datetime.now()}
    )

    # Create response
    response = JSONResponse(
        content={"access_token": access_token, "username": res.email}
    )

    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )

    return response


@router.post("/register", response_model=RegisterResponse)
async def register(register_data: RegisterRequest, db: Session = Depends(get_db)):
    # Check if user exists
    check_query = """
        SELECT email 
        FROM users
        WHERE email = :email
    """
    existing_user = db.execute(
        text(check_query), {"email": register_data.email}
    ).first()

    logger.debug(f"/register existing_user: {existing_user}")

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password
    hashed_password = get_password_hash(register_data.password)

    # generate a unique id for the user
    user_id = uuid.uuid4()

    # Insert new user with hashed password
    insert_query = """
        INSERT INTO users (id, email, username, password_hash, is_active) 
        VALUES (:id ,:email, :username, :password_hash, true)
        RETURNING id, email, username
    """

    try:
        # add new user to db
        res = db.execute(
            text(insert_query),
            {
                "id": user_id,
                "email": register_data.email,
                "username": register_data.username,
                "password_hash": hashed_password,
            },
        ).one()

        # commit the transaction
        db.commit()

        # get the user data from db response
        logger.debug(f'res: {res}')
        user_data = row2dict(res)
        logger.debug(f'user_data: {user_data}')
        # create access token
        access_token = create_access_token(
            data={
                "sub": str(user_id),
                "name": register_data.email,
                "iat": datetime.now(),
            }
        )

        # return the user data and access token
        return RegisterResponse(user=User(username=user_data['username'], email=user_data['email'], id=user_data['id']), token=Token(access_token=access_token, token_type="access"))
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating user")


@router.post("/logout")
async def logout(db: Session = Depends(get_db)):
    response = JSONResponse(content={"message": "Logout successful"})

    # Clear the refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )

    return response


@router.get("/me")
@token_auth()
async def read_me(request: Request):
    current_user = await get_current_user(request)
    logger.debug(f"/me")
    return current_user


@router.post("/refresh")
async def refresh_token(
    refresh_token: str | None = Cookie(None, alias="refresh_token")
):
    if not refresh_token:
        raise HTTPException(401, "Refresh token missing")

    new_access_token = await refresh_access_token(refresh_token)
    return {"access_token": new_access_token}
