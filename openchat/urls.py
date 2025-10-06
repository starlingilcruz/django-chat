"""
URL configuration for openchat project
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from accounts.template_views import LoginTemplateView, LogoutTemplateView, SignupTemplateView
from common.views import health_check
from conversations.template_views import (
    ChatRoomTemplateView,
    ConversationListTemplateView,
    CreateConversationTemplateView,
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Health check
    path("healthz", health_check, name="health-check"),
    # Web UI
    path("", RedirectView.as_view(url="/login", permanent=False)),
    path("login", LoginTemplateView.as_view(), name="login"),
    path("signup", SignupTemplateView.as_view(), name="signup"),
    path("logout", LogoutTemplateView.as_view(), name="logout"),
    path(
        "conversations/",
        ConversationListTemplateView.as_view(),
        name="conversation-list",
    ),
    path(
        "conversations/create",
        CreateConversationTemplateView.as_view(),
        name="create-conversation",
    ),
    path(
        "conversations/<uuid:conversation_id>/",
        ChatRoomTemplateView.as_view(),
        name="chat-room",
    ),
    # API v1
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/", include("conversations.urls")),
    path("api/v1/", include("messaging.urls")),
]
