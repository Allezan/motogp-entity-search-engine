from fastapi import APIRouter
from app.api import documents, entities, evaluation, health, index, search

api_router = APIRouter()
for module in (health, search, documents, entities, index, evaluation):
    api_router.include_router(module.router)
