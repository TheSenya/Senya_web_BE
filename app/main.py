# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings

from pydantic import BaseModel
from typing import Optional

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, openapi_url=f"{settings.API_V1_STR}/openapi.json")

# class Item(BaseModel):
#     name: str
#     description: Optional[str] = None
#     price: float
#     tax: Optional[float] = None

# @app.get("/")
# async def root():
#     return {"message": "Hello World"}

# @app.get("/items/{item_id}")
# async def read_item(item_id: int):
#     return {"item_id": item_id}

# @app.post("/items/")
# async def create_item(item: Item):
#     return item