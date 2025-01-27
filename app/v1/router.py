from fastapi import APIRouter
from .endpoints import auth, note

# Create the main API router
api_router = APIRouter()

# Include the items router
api_router.include_router(auth.router)
api_router.include_router(note.router)
