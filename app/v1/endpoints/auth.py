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
from app.core.auth import get_current_user

from app.v1.endpoints.note_folder import create_default_folder

router = APIRouter(prefix="/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    logger.info(f"Login attempt with email: {login_data.email}")

    # Get user and hashed password
    query = """
        SELECT id, email, password_hash, username
        FROM users
        WHERE email = :email
    """

    res = db.execute(text(query), {"email": login_data.email}).first()

    res_dict = row2dict(res)
    if (
        not res_dict
        or not res_dict.get("email")
        or not verify_password(login_data.password, res_dict.get("password_hash", ""))
    ):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token(
        data={"sub": str(res_dict.get("id"))}
    )

    refresh_token = create_refresh_token(
        data={"sub": str(res_dict.get("id"))}
    )

    # Create response
    response = JSONResponse(
        content={
            "access_token": access_token,
            "username": res_dict.get("username", ""),
            "email": res_dict.get("email", ""),
            "id": str(res_dict.get("id", "")), 
        }
    )

    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=False,
        secure=True,
        samesite="none",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )

    return response


@router.post("/register")
async def register(register_data: RegisterRequest, db: Session = Depends(get_db)):

    logger.debug(f"register_data: {register_data}")
    # Check if user exists by username and email
    check_query = """
        SELECT email 
        FROM users
        WHERE email = :email
        OR username = :username
    """
    existing_user = db.execute(
        text(check_query), {"email": register_data.email, "username": register_data.username}
    ).first()


    if existing_user:
        raise HTTPException(status_code=400, detail="Email or username already registered")

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


        # create a default root folder for the user
        create_default_folder(db, register_data.username, user_id)

        # commit the transaction
        db.commit()

        # get the user data from db response
        user_data = row2dict(res)

        # create access token
        access_token = create_access_token(
            data={
                "sub": str(user_id)
            }
        )

        refresh_token = create_refresh_token(
            data={
                "sub": str(user_id)
            }
        )

        new_user = User(
            username=user_data.get("username", None),
            email=user_data.get("email", None),
            id=str(user_data.get("id", None)),
            is_active=user_data.get("is_active", None),
        )

        response = JSONResponse(
            content={
                "user": new_user.model_dump(),
                "token": Token(access_token=access_token, token_type="access").model_dump()
            }
        )
        # Set refresh token as httpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=False,
            secure=True,
            samesite="none",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            path="/",
        )

        # return the user data and access token
        return response
    
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
        httponly=False,
        secure=True,
        samesite="none",
        path="/",
    )
    
    return response


@router.get("/me")
@token_auth()
async def read_me(request: Request, db: Session = Depends(get_db)):
    logger.debug(f"/me start")
    user = get_current_user(request, db)
    logger.debug(f"/me user: {user}")
    return user


@router.post("/refresh")
async def refresh_token(
    refresh_token: str | None = Cookie(None, alias="refresh_token")
):
    if not refresh_token:
        raise HTTPException(401, "Refresh token missing")

    new_access_token = await refresh_access_token(refresh_token)
    return {"access_token": new_access_token}

# @router.get("/debug/get_cookies")
# async def debug_get_cookies(request: Request):
#     logger.debug(f"request.cookies: {request.cookies}")
#     return {"cookies": dict(request.cookies)}

# @router.get("/debug/set_cookie")
# async def debug_set_cookie(request: Request):
#     response = JSONResponse(content={"message": "Set cookie successful"})
#     response.set_cookie(
#         key="refresh_token",
#         value="test_value",
#         httponly=False,
#         secure=True,
#         samesite="none",
#         max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
#         path="/",
#     )
    
#     logger.debug(f"response: {response}")
#     return response