from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.login import LoginRequest, LoginResponse
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash
import logging
import uuid


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    log.info(f"Login attempt with username: {login_data.username}")
    
    # Get user and hashed password
    query = """
        SELECT username, password_hash 
        FROM users
        WHERE username = :username
    """
    result = db.execute(
        text(query), 
        {"username": login_data.username}
    ).first()
    
    if not result or not verify_password(login_data.password, result.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    return {
        "access_token": "mock_token_12345",  # You should generate a real JWT token here
        "username": result.username
    }

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
    return {"message": "Logout successful"}