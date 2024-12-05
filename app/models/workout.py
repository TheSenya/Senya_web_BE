from sqlalchemy import Column, String, Integer, Date, PickleType
from sqlalchemy.sql import func
from app.models.base import BaseModel
from app.core.database import Base

# # Visual Reperesentation of Data
# {
#     id: '12345',
#     user_id: 'sam',      
#     exercise: { benchpress: {reps: [[1],[2],[3],[4,2]], weight:[[10], [12], [13], [13, 14]] }
#     },
#     date: 12-01-2012, 
#     duration: 64 # minutes
# }

class Workouts(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    exercise = Column(PickleType, nullable = False )
    date = Column(Date, default=func.current_date())
    duration = Column(Integer, nullable=True)

# Visual Reperesentation of Data 'Exercise'

# {
#     name = 'pushup',
#     workout_id = '12345'
#     exercise: {
#     }
# }

# class Exercise(Base):
#     __tablename__ = "exercise"

#     workout_id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, index=True)
#     reps = Column(ARRAY(Integer))
#     weight = Column(ARRAY(Integer))
#     sets = 