from sqlalchemy import Column, ForeignKey, Null, String, Integer, Date, PickleType, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
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

class Workout(BaseModel):
    __tablename__ = "workout"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    date = Column(Date, default=func.current_date())
    duration = Column(Integer, nullable=True)

    # Relationships
    user = relationship('User', back_populates='workouts')
    exercises = relationship('Exercise', back_populates='workout', cascade="all, delete-orphan")

class Exercise(BaseModel):
    __tablename__ = "exercise"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    workout_id = Column(Integer, ForeignKey("workout.id"), nullable=False)
    name = Column(String(50), nullable=False)
    reps_and_weights = Column(JSONB, nullable=True)

    # Relationships
    user = relationship('User', back_populates='exercises')
    workout = relationship('Workout', back_populates='exercises')



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