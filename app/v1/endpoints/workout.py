from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas.login import LoginRequest, LoginResponse
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash
import logging

router = APIRouter(
    prefix="/workout",
    tags=["workout"]
)

@router.post("/create")
async def create_workout(workour, db: Session = Depends(get_db)):
    return {"message": "Workout created successfully"}

@router.get("/get")
async def get_workouts(db: Session = Depends(get_db)):
    return {"message": "Workouts fetched successfully"}

@router.delete("/delete")
async def delete_workout(workout_id: int, db: Session = Depends(get_db)):
    return {"message": "Workout deleted successfully"}

