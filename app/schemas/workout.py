from pydantic import BaseModel
from datetime import datetime
from typing import List

class WorkoutCreate(BaseModel):
    exercise: str
    sets: List[int]
    reps: List[int]
    weight: List[int]
    date: datetime

