from datetime import datetime, timedelta
from functools import wraps
from typing import Optional
import json
import inspect  # <-- To check if a function is a coroutine
from fastapi import Request, HTTPException, Depends, WebSocket
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool  # <-- To run sync endpoints asynchronously
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

        #logger.debug(f"user: {user}")
        #logger.debug(f"User.model_validate(user): {User.model_validate(user)}")

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

    # First try to verify access token
    try:
        payload = jwt.decode(
            access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

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
    """
    Decorator to enforce token validation and refresh logic.
    This decorator extracts the access token and refresh token, validates them,
    and if necessary refreshes the access token. It also attaches a new access token
    to the JSONResponse if a refresh occurred.
    
    This implementation supports both asynchronous and synchronous endpoint functions.
    If the endpoint is synchronous, it is executed in a thread pool to avoid blocking the event loop.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Store the original access token from the Authorization header.
            auth_header = request.headers.get("Authorization")
            original_access_token = None
            new_access_token = None
            
            # Extract tokens from request.
            if auth_header and auth_header.startswith("Bearer "):
                original_access_token = auth_header.split(" ")[1]
            
            # Get the refresh token from cookies.
            refresh_token = request.cookies.get("refresh_token")
            
            #logger.debug(f"token_auth original_access_token: {original_access_token}")
            #logger.debug(f"token_auth refresh_token: {refresh_token}")
            
            # Verify the tokens. The verify_tokens() function returns a tuple:
            # (access_token, user_id). If the access token was refreshed, the returned
            # access_token will be different from the original.
            verified_access_token, user_id = await verify_tokens(original_access_token, refresh_token)
            
            # Check if the token was refreshed.
            if original_access_token != verified_access_token:
                new_access_token = verified_access_token
            
            #logger.debug(f"Verified access token: {verified_access_token}")
            #logger.debug(f"user_id: {user_id}")
            
            # Make sure that the endpoint function receives the request object if it expects it.
            if "request" in func.__code__.co_varnames:
                kwargs["request"] = request
            
            # Attach the user information to the request so that endpoint functions can use it.
            request.state.user = {"id": user_id}
            
            # Execute the endpoint function.
            #
            # If func is a coroutine (i.e. asynchronous), simply await it.
            # Otherwise, wrap it in run_in_threadpool so that it does not block the event loop.
            if inspect.iscoroutinefunction(func):
                response = await func(*args, **kwargs)
            else:
                response = await run_in_threadpool(func, *args, **kwargs)
            
            # If a new access token was generated (i.e. the token was refreshed) and the response
            # is a JSONResponse, attach the new access token to the response JSON.
            if new_access_token:
                if isinstance(response, JSONResponse):
                    # Decode the current response body so we can add the new token.
                    response_data = json.loads(bytes(response.body).decode())
                    response_data["new_access_token"] = new_access_token
                    response = JSONResponse(content=response_data)
            
            return response

        return wrapper

    return decorator

def token_auth_ws():
    """
    Decorator to enforce token validation and refresh logic for WebSocket connections.
    This decorator extracts the access token from route parameters and refresh token from cookies,
    validates them, and if necessary refreshes the access token.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(websocket: WebSocket, *args, **kwargs):
            logger.info(f"--------------------------------------: {websocket}")
            try:
                # Extract access token from query parameters
                access_token = websocket.query_params.get("token")
                
                # Get refresh token from cookies
                cookies = websocket.cookies
                refresh_token = cookies.get("refresh_token")
                
                # Verify the tokens
                verified_access_token, user_id = await verify_tokens(access_token, refresh_token)
                
                # Attach user information to the websocket state
                websocket.state.user = {"id": user_id}
                logger.info(f"websocket.state.user: {websocket.state.user}")
                logger.info(f"websocket.query_params: {websocket.query_params}")
                logger.info(f"websocket.cookies: {websocket.cookies}")
                # Execute the websocket handler
                return await func(websocket, *args, **kwargs)
                
            except Exception as e:
                # Close websocket connection if authentication fails
                await websocket.close(code=1008, reason="Authentication failed")
                raise
                
        return wrapper
    return decorator