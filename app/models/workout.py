from sqlalchemy import Column, String, List, Integer, DateTime
from sqlalchemy import func
from app.models.base import BaseModel

class Workouts(BaseModel):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    exercise = Column(String, index=True)
    sets = Column(List[Integer])
    reps = Column(List[Integer])
    weight = Column(List[Integer])
    date = Column(DateTime, default=func.now())

    
 