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

# creates new access tokens
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "token_type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


# creates new refresh tokens
def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "token_type": "refresh"})
    return jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM  # Original: data instead of to_encode
    )

# refreshes the access token is refresh token is valid
async def refresh_access_token(refresh_token: str) -> str:
    """
    Validates refresh token and generates new access token
    Returns username and new access token if refresh token is valid
    """
    #open up a new db session
    db = next(get_db())

    try:
        # check if refresh token is valid
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        # check if payload is of valid type
        if payload.get("token_type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        # get user_id and username data from the refresh token
        user_id = payload.get("sub")
        username = payload.get("name")

        # Verify user exists
        query = "SELECT * FROM users WHERE username = :username"
        user = db.execute(text(query), {"username": username}).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        # Generate new access token
        new_access_token = create_access_token(
            data={"sub": username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        return new_access_token
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    finally:
        db.close()

# verify both access and refresh token
async def verify_tokens(
    access_token: str, 
    refresh_token: str | None, 
    db: Session
) -> tuple[str, str | None]:
    """
    Verifies access token or uses refresh token to get new access token
    Returns username and new access token (if refreshed)
    """

    logger.debug(f'verify tokens 1')
    credentials_exception = HTTPException(
        status_code=401, detail="Could not validate credentials 2"
    )
    # First try to verify access token
    try:
        payload = jwt.decode(
            access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        logger.debug(f'payload : {payload}')
        if payload.get("token_type") != "access":
            raise credentials_exception
        
        username: str = str(payload.get("sub"))
        if not username:
            raise credentials_exception

        return username, None

    except JWTError:
        # Access token invalid - try refresh if available
        if not refresh_token:
            raise credentials_exception

        try:
            new_access_token = await refresh_access_token(refresh_token)

            return username, new_access_token
        except HTTPException:
            raise credentials_exception


def token_auth():
    """Decorator to enforce token validation and refresh logic."""
    def decorator(func):
        @wraps(func)
        async def wrapper(
            request: Request,
            *args, **kwargs
        ):  


            # Extract tokens
            access_token = None
            refresh_token = request.cookies.get("refresh_token")
            auth_header = request.headers.get("Authorization")
            
            logger.debug(f'token_auth auth_header: {auth_header} refresh: {refresh_token}')

            # Get access token from header
            if auth_header and auth_header.startswith("Bearer "):
                access_token = auth_header.split(" ")[1]

            logger.debug(f'token_auth access_token: {access_token}')

            try:
                # Check if access token exists
                if access_token:
                    # validate acccess token 
                    payload = jwt.decode(
                        access_token,
                        settings.SECRET_KEY,
                        algorithms=[settings.ALGORITHM]
                    )

                    # check if token is of correct type
                    if payload.get("token_type") != "access":
                        raise HTTPException(401, "Invalid token type")
                    
                    # get username and user_id from decoded JWT payload
                    username = payload.get("name")
                    user_id = payload.get("sub")

                else: 
                    # check if refresh token exists
                    if not refresh_token:
                        raise HTTPException(401, "No valid tokens provided") #TODO prompt a logout
                    logger.debug(f'4')
                    # Validate refresh token and get new access token
                    new_access_token = await refresh_access_token(refresh_token)

                    kwargs["new_access_token"] = new_access_token  # Pass to endpoint

            except ExpiredSignatureError:
                # refresh token should be used to generate new access token in this case
                logger.debug(f' ExpiredSignatureError  with access token')

                if not refresh_token:
                    raise HTTPException(401, "No valid tokens provided") #TODO prompt a logout
                new_access_token = await refresh_access_token(refresh_token)

            except Exception as e:
                # JWTError is the common case here
                # user should be kicked immediately and prompted to relogin 
                logger.error(f' Error with jwt decode of access token ')
                raise HTTPException(401, "Invalid or expired tokens")

            # Execute endpoint
            response = await func(request, *args, **kwargs)
            
            # Attach new access token to response (if generated)
            if "new_access_token" in kwargs:
                if isinstance(response, JSONResponse):
                    logger.debug(f'2')
                    response_data = json.loads(response.body.decode())
                    response_data["new_access_token"] = kwargs["new_access_token"]
                    return JSONResponse(content=response_data)
            
            logger.debug(f'3')
            return response

        return wrapper
    return decorator
