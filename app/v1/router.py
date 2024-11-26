from fastapi import APIRouter
from .endpoints import login

# Create the main API router
api_router = APIRouter()

# Include the items router
api_router.include_router(login.router)
