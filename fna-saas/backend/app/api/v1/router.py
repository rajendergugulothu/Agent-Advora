"""
Central API v1 router — registers all sub-routers.
"""

from fastapi import APIRouter

from app.api.v1 import drafts, instagram, users, webhook

api_router = APIRouter()

api_router.include_router(users.router,     prefix="/users",     tags=["users"])
api_router.include_router(drafts.router,    prefix="/drafts",    tags=["drafts"])
api_router.include_router(instagram.router, prefix="/instagram", tags=["instagram"])
api_router.include_router(webhook.router,   prefix="/webhook",   tags=["webhook"])
