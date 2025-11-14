"""Routers package for API"""
from .analysis import router as analysis_router
from .config import router as config_router
from .datasets import router as datasets_router
from .reports import router as reports_router

__all__ = [
    "analysis_router",
    "config_router",
    "datasets_router",
    "reports_router",
]
