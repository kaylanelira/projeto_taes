from fastapi import APIRouter

from endpoints import sql_generator

api_router = APIRouter()
api_router.include_router(sql_generator.router)
