from django.urls import path

from .views import MessageHistoryView

app_name = "messaging"

urlpatterns = [
    path(
        "conversations/<uuid:conversation_id>/messages",
        MessageHistoryView.as_view(),
        name="message-history",
    ),
]
