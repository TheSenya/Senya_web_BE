from app.core.database import Base
from app.models.base import BaseModel

# add tables to be migrated into the DB from alembic
from app.models.user import User
from app.models.login import LoginAttempts
from app.models.workout import Workout, Exercise
from app.models.notes import Note, NoteFolder

