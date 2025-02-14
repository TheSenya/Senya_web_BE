from datetime import datetime, timedelta
from functools import wraps
from typing import Optional
import json

from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from jose import JWTError, jwt, ExpiredSignatureError

from app.core.database import get_db
from app.core.config import settings
from app.config.constants import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from app.config.logger import logger
from app.core.helper import row2dict
from app.schemas.user import User


# get the current user from the request
def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.state.user.get('id')

    if user_id is not None:

        query = "SELECT * FROM users WHERE id = :user_id"
        user = db.execute(text(query), {"user_id": user_id}).first()

        logger.debug(f"user: {user}")
        logger.debug(f"User.model_validate(user): {User.model_validate(user)}")

        return User.model_validate(user)
    
    return None

# creates new access tokens
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "token_type": "access", "iat": datetime.now()})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


# creates new refresh tokens
def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()

    expire = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "token_type": "refresh", "iat": datetime.now()})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,  # Original: data instead of to_encode
    )


# refreshes the access token is refresh token is valid
async def refresh_access_token(refresh_token: str) -> tuple[str, str]:
    """
    Validates refresh token and generates new access token
    Returns username and new access token if refresh token is valid
    """
    # open up a new db session
    db = next(get_db())

    try:
        # check if refresh token is valid
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        # check if payload is of valid type
        if payload.get("token_type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        # get user_id from the refresh token
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User id not found in payload")

        # Verify user exists
        query = "SELECT * FROM users WHERE id = :user_id"
        user = db.execute(text(query), {"user_id": user_id}).first()

        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        # Generate new access token
        new_access_token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        return new_access_token, user_id
    
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired") # TODO prompt a logout/login

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token") # TODO prompt a logout/login
    
    finally:
        db.close()


# verify both access and refresh token
async def verify_tokens(
    access_token: str | None, refresh_token: str | None
) -> tuple[str, str | None]:
    """
    Verifies access token or uses refresh token to get new access token
    Returns username and new access token (if refreshed)
    """
    if not access_token:
        raise HTTPException(status_code=401, detail="No access token provided")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token provided")

    logger.debug(f"DISPLAY TOKENS")
    logger.debug(f"access_token: {access_token}")
    logger.debug(f"refresh_token: {refresh_token}")

    # First try to verify access token
    try:
        payload = jwt.decode(
            access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        logger.debug(f"payload : {payload}")

        if payload.get("token_type") != "access":
            raise HTTPException(
                status_code=401, detail="Invalid access token type"
            )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401, detail="Access token does not contain user id"
            )

        return access_token, user_id
    
    except ExpiredSignatureError:
        # Access token invalid - try refresh if available
        if not refresh_token:
            raise HTTPException(
                status_code=401, detail="Invalid refresh token"
            )

        try:
            new_access_token, user_id = await refresh_access_token(refresh_token)

            return new_access_token, user_id
        
        except HTTPException:
            raise HTTPException(
                status_code=401, detail="Could not validate credentials"
            )

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def token_auth():
    """Decorator to enforce token validation and refresh logic."""

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):

            # set temp variables
            user_id = None
            access_token = None
            new_access_token = None

            # Extract tokens
            refresh_token = request.cookies.get("refresh_token")
            auth_header = request.headers.get("Authorization")

            # Get access token from header
            if auth_header and auth_header.startswith("Bearer "):
                access_token = auth_header.split(" ")[1]

            logger.debug(f"token_auth access_token: {access_token}")

            # verify tokens
            access_token, user_id = await verify_tokens(access_token, refresh_token)

            logger.debug(f"access token verified: {access_token}")
            logger.debug(f"user_id: {user_id}")

            # Check if the decorated function expects a request parameter
            logger.debug(f"func.__code__.co_varnames: {func.__code__.co_varnames}")

            if "request" in func.__code__.co_varnames:
                kwargs["request"] = request

            request.state.user = {
                "id": user_id,
            }

            # Execute endpoint
            response = await func(*args, **kwargs)

            # Attach new access token to response (if generated)
            if "new_access_token" in kwargs or new_access_token:
                if isinstance(response, JSONResponse):
                    response_data = json.loads(bytes(response.body).decode())

                    if new_access_token:
                        response_data["new_access_token"] = new_access_token
                    else:
                        response_data["new_access_token"] = kwargs["new_access_token"]

                    return JSONResponse(content=response_data)

            return response

        return wrapper

    return decorator
