from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Dict

class WorkoutCreate(BaseModel):
    exercise: Dict[str, int]
    user_id: str
    date: date
    duration: int

# class WorkoutResponse(BaseModel):


