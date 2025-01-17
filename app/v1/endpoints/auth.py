#TODO
# 1. return hints
# 2. implement function row2dict and rows2dict for conversion of sqlalchemy obj to dicts
# 3. update errors for the functions and endpoints


from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.login import LoginRequest, LoginResponse
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash
import logging
import uuid
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.core.config import settings

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

#creates new access tokens
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), refresh_token: str | None = None, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
    except JWTError as e:
        # If refresh token is provided, try to refresh the access token
        if refresh_token:
            try:
                new_access_token = await refresh_access_token(refresh_token, db)
                # Decode the new token to get user info
                payload = jwt.decode(new_access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                username = payload.get("sub")
                if username is None:
                    raise credentials_exception
            except HTTPException:
                raise credentials_exception
        else:
            raise credentials_exception

    query = "SELECT * FROM users WHERE username = :username"
    user = db.execute(text(query), {"username": username}).first()
    
    if user is None:
        raise credentials_exception

    # If we refreshed the token, attach it to the user object
    if refresh_token and 'new_access_token' in locals():
        user = dict(user)
        user['new_access_token'] = new_access_token

    return user

async def refresh_access_token(refresh_token: str, db: Session) -> str:
    """
    Validates refresh token and generates new access token
    Returns new access token if refresh token is valid
    """
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        
        # Verify user exists
        query = "SELECT * FROM users WHERE username = :username"
        user = db.execute(text(query), {"username": username}).first()
        
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Generate new access token
        new_access_token = create_access_token(
            data={"sub": username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return new_access_token
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


async def verify_refresh_token(refresh_token: str, db: Session):
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Verify user exists
        query = "SELECT * FROM users WHERE username = :username"
        user = db.execute(text(query), {"username": username}).first()
        
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    log.info(f"Login attempt with username: {login_data.username}")
    
    # Get user and hashed password
    query = """
        SELECT username, password_hash 
        FROM users
        WHERE username = :username
    """

    res = db.execute(
        text(query), 
        {"username": login_data.username}
    ).first()
    
    if not res or not res.username or not verify_password(login_data.password, res.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(
        data={"sub": res.username}, 
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    refresh_token = create_access_token(
        data={"sub": res.username}, 
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    # Create response
    response = JSONResponse(content={
        "access_token": access_token,
        "username": res.username
    })

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
    existing_user = db.execute(text(check_query), {"username": login_data.username}).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Hash the password
    hashed_password = get_password_hash(login_data.password)

    # generate a unique id for the user
    user_id =  uuid.uuid4()
    
    # Insert new user with hashed password
    insert_query = """
        INSERT INTO users (id, username, password_hash, created_at, updated_at) 
        VALUES (:id ,:username, :password_hash, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        RETURNING username
    """
    
    try:
        result = db.execute(
            text(insert_query), 
            {   
                "id": user_id,
                "username": login_data.username,
                "password_hash": hashed_password
            }
        )
        db.commit()
        return {"message": "User created successfully"}
    except Exception as e:
        db.rollback()
        log.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error creating user"
        )
    
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
# Add an example protected endpoint
@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    # Convert SQLAlchemy Row to dictionary and select specific fields
    user_data = {
        "id": current_user.id,
        "username": current_user.username,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }

    return user_data