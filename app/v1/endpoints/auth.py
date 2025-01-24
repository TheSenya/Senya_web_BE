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
from app.core.auth import token_auth, create_access_token, create_refresh_token, refresh_access_token
from app.config.constants import REFRESH_TOKEN_EXPIRE_DAYS
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

#TODO
def get_user(username: str = "", user_id: str = "", db: Session = Depends(get_db)):
    try:
        user_id = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid UUID in token")
    
    if username is("" or None):
        raise HTTPException(status_code=401, detail="Invalid username")
    
    query = "SELECT * FROM users WHERE username = :username AND id = :id"
    user = db.execute(text(query), {"username": username, "id": user_id}).first()

    return row2dict(user)


async def get_current_user(
    request: Request, 
    db: Session = Depends(get_db),
    token: str =  Depends(oauth2_scheme)) -> dict | None:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials 1",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        logger.debug('get current 1')
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        logger.debug('get current 2')
        user_id = payload.get("sub") # uuid is stored as a string in the jwt
        logger.debug('get current 2.5')
        username = payload.get("name")
        logger.debug('get current 3')
        if username is None or user_id is None:
            logger.debug('get current user err 1')
            #raise credentials_exception
        
    except Exception as e:
        logger.debug('get current user err 2 {e}')
        #raise credentials_exception

    #user = get_user(username, user_id, db)

    
    #return user
    return None


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    logger.info(f"Login attempt with username: {login_data.username}")

    # Get user and hashed password
    query = """
        SELECT id, username, password_hash
        FROM users
        WHERE username = :username
    """

    res = db.execute(text(query), {"username": login_data.username}).first()

    if (
        not res
        or not res.username
        or not verify_password(login_data.password, res.password_hash)
    ):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": str(res.id), "name": res.username, "iat": datetime.now()})

    refresh_token = create_refresh_token(data={"sub": str(res.id), "name": res.username, "iat": datetime.now()})

    # Create response
    response = JSONResponse(
        content={"access_token": access_token, "username": res.username}
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


@router.post("/register")
async def register(login_data: LoginRequest, db: Session = Depends(get_db)):
    # Check if user exists
    check_query = """
        SELECT username 
        FROM users
        WHERE username = :username
    """
    existing_user = db.execute(
        text(check_query), {"username": login_data.username}
    ).first()

    logger.debug(f'1')

    if existing_user:
        logger.debug(f'1.1')
        raise HTTPException(status_code=400, detail="Username already registered")

    # Hash the password
    hashed_password = get_password_hash(login_data.password)
    logger.debug(f'2')
    # generate a unique id for the user
    user_id = uuid.uuid4()

    logger.debug(f'3')
    # Insert new user with hashed password
    insert_query = """
        INSERT INTO users (id, username, password_hash, created_at, updated_at) 
        VALUES (:id ,:username, :password_hash, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        RETURNING username
    """

    try:
        db.execute(
            text(insert_query),
            {
                "id": user_id,
                "username": login_data.username,
                "password_hash": hashed_password,
            },
        )
        logger.debug(f'4')
        db.commit()
        return {"message": "User created successfully"}
    except Exception as e:
        db.rollback()
        logger.debug(f'5')
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
async def read_me(request: Request
):  
    current_user = await get_current_user(request)
    logger.debug(f'/me')
    return current_user



@router.post("/refresh")
async def refresh_token(
    refresh_token: str | None = Cookie(None, alias="refresh_token")
):
    if not refresh_token:
        raise HTTPException(401, "Refresh token missing")

    new_access_token = await refresh_access_token(refresh_token)
    return {"access_token": new_access_token}

