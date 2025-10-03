"""
Production settings
"""

from .base import *  # noqa: F403

DEBUG = False

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# WebSocket allowed origins (configure based on your domain)
ALLOWED_WEBSOCKET_ORIGINS = os.getenv(  # noqa: F405
    "ALLOWED_WEBSOCKET_ORIGINS", ""
).split(",")
