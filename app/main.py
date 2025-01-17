# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings    

# from pydantic import BaseModel
# from typing import Optional

from .v1.router import api_router

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, openapi_url=f"{settings.API_V1_STR}/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# This code configures CORS policies for your FastAPI backend. Here's a detailed breakdown:
# What is CORS?
# CORS is a security feature implemented by web browsers
# It prevents web pages from making requests to a different domain than the one that served the web page
# Without proper CORS settings, your frontend (running on one domain) couldn't communicate with your backend API (running on another domain)

# Configuration Details:
# allow_origins=["*"]:
#   The * means any domain can access your API
#   In production, you should replace this with specific domains, e.g., ["https://yourfrontend.com"]
#   This is currently set to the most permissive setting

# allow_credentials=True:
#   Allows requests to include credentials like cookies, authorization headers, or TLS client certificates
#   Important for authenticated requests
#   When this is True, allow_origins shouldn't be "*" in production for security reasons

# allow_methods=["*"]:
#   Allows all HTTP methods (GET, POST, PUT, DELETE, OPTIONS, etc.)
#   You could restrict this to specific methods like ["GET", "POST"]

# allow_headers=["*"]:
#   Allows all HTTP headers in requests
#   Could be restricted to specific headers like ["Authorization", "Content-Type"]

# Security Consideration:
# The current configuration is very permissive and suitable for development, but for production, you should:
# - Specify exact origins instead of "*"
# - Consider limiting methods to only those you need
# - Specify exact headers instead of allowing all
# - Be careful with allow_credentials=True combined with wildcard origins

# Example of a more secure production configuration:
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourfrontend.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
"""

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)
