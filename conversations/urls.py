"""
URL patterns for conversations app
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ConversationViewSet

app_name = "conversations"

router = DefaultRouter()
router.register(r"conversations", ConversationViewSet, basename="conversation")

urlpatterns = [
    path("", include(router.urls)),
]
