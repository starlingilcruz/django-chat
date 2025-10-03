"""
Template-based views for conversations
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .models import Conversation, Participant
from .serializers import ConversationCreateSerializer


class ConversationListTemplateView(LoginRequiredMixin, View):
    """List all conversations for the current user"""

    login_url = "/login"

    def get(self, request):
        conversations = Conversation.objects.filter(
            participants__user=request.user
        ).distinct()
        return render(
            request, "conversations/list.html", {"conversations": conversations}
        )


class CreateConversationTemplateView(LoginRequiredMixin, View):
    """Create a new conversation"""

    login_url = "/login"

    def post(self, request):
        name = request.POST.get("name")
        serializer = ConversationCreateSerializer(
            data={"name": name, "participant_ids": [request.user.id]},
            context={"request": request},
        )

        if serializer.is_valid():
            conversation = serializer.save()
            return redirect("chat-room", conversation_id=conversation.id)

        # If validation fails, redirect back to list
        return redirect("conversation-list")


class ChatRoomTemplateView(LoginRequiredMixin, View):
    """Chat room view"""

    login_url = "/login"

    def get(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)

        # Check if user is a participant
        participant = Participant.objects.filter(
            conversation=conversation, user=request.user
        ).first()

        if not participant:
            return render(
                request,
                "conversations/list.html",
                {
                    "error": "You are not a participant in this conversation",
                    "conversations": Conversation.objects.filter(
                        participants__user=request.user
                    ).distinct(),
                },
            )

        is_admin = participant.role == Participant.Role.ADMIN

        return render(
            request,
            "conversations/chat_room.html",
            {"conversation": conversation, "is_admin": is_admin},
        )
