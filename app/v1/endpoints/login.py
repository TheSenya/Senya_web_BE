from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas.login import LoginRequest, LoginResponse
from core.database import get_db
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/login",
    tags=["authentication"]
)

@router.post("/", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    log.info(f"Login attempt with username: {login_data.username}")
    
    # Use raw SQL with parameters to prevent SQL injection
    query = """
        SELECT username, password 
        FROM users 
        WHERE username = :username AND password = :password
    """
    result = db.execute(
        query, 
        {
            "username": login_data.username,
            "password": login_data.password
        }
    ).first()
    
    if not result:
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
    existing_user = db.execute(check_query, {"username": login_data.username}).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Insert new user
    insert_query = """
        INSERT INTO users (username, password, created_at, updated_at) 
        VALUES (:username, :password, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        RETURNING username
    """
    
    try:
        result = db.execute(
            insert_query,
            {
                "username": login_data.username,
                "password": login_data.password
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