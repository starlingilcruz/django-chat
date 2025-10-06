"""
Development settings
"""

from .base import *  # noqa: F403

DEBUG = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
