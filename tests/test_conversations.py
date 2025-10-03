"""
Tests for conversations
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from conversations.models import Conversation, Participant

User = get_user_model()


@pytest.mark.django_db
class TestConversations:
    """Test conversation endpoints"""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            password="SecurePass123!",
        )
        self.client.force_authenticate(user=self.user)

    def test_create_conversation(self):
        """Test creating a conversation"""
        data = {"name": "Test Conversation"}

        response = self.client.post(
            "/api/v1/conversations/",
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Test Conversation"
        assert "slug" in response.data

        # Check creator is admin participant
        conversation = Conversation.objects.get(id=response.data["id"])
        participant = Participant.objects.get(
            conversation=conversation,
            user=self.user,
        )
        assert participant.role == Participant.Role.ADMIN

    def test_list_conversations(self):
        """Test listing user's conversations"""
        conversation = Conversation.objects.create(
            name="Test Conversation",
            created_by=self.user,
        )
        Participant.objects.create(
            conversation=conversation,
            user=self.user,
            role=Participant.Role.ADMIN,
        )

        response = self.client.get("/api/v1/conversations/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_retrieve_conversation_as_participant(self):
        """Test retrieving a conversation as a participant"""
        conversation = Conversation.objects.create(
            name="Test Conversation",
            created_by=self.user,
        )
        Participant.objects.create(
            conversation=conversation,
            user=self.user,
            role=Participant.Role.MEMBER,
        )

        response = self.client.get(f"/api/v1/conversations/{conversation.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(conversation.id)

    def test_retrieve_conversation_as_non_participant(self):
        """Test retrieving a conversation as a non-participant"""
        other_user = User.objects.create_user(
            email="other@example.com",
            username="otheruser",
            first_name="Other",
            last_name="User",
            password="SecurePass123!",
        )
        conversation = Conversation.objects.create(
            name="Test Conversation",
            created_by=other_user,
        )
        Participant.objects.create(
            conversation=conversation,
            user=other_user,
            role=Participant.Role.ADMIN,
        )

        response = self.client.get(f"/api/v1/conversations/{conversation.id}/")

        assert response.status_code == status.HTTP_403_FORBIDDEN
