"""
Serializers for conversations
"""

from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import Conversation, Participant


class ParticipantSerializer(serializers.ModelSerializer):
    """
    Serializer for Participant model
    """

    user = UserSerializer(read_only=True)

    class Meta:
        model = Participant
        fields = ("id", "user", "role", "joined_at")
        read_only_fields = ("id", "joined_at")


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for Conversation model
    """

    created_by = UserSerializer(read_only=True)
    participants = ParticipantSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = (
            "id",
            "name",
            "slug",
            "created_by",
            "created_at",
            "updated_at",
            "participants",
        )
        read_only_fields = ("id", "slug", "created_by", "created_at", "updated_at")


class ConversationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating conversations
    """

    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Conversation
        fields = ("name", "participant_ids")

    def create(self, validated_data):
        participant_ids = validated_data.pop("participant_ids", [])
        request = self.context.get("request")
        conversation = Conversation.objects.create(
            created_by=request.user,
            **validated_data,
        )

        # Add creator as admin
        Participant.objects.create(
            conversation=conversation,
            user=request.user,
            role=Participant.Role.ADMIN,
        )

        # Add other participants
        from django.contrib.auth import get_user_model

        User = get_user_model()
        for user_id in participant_ids:
            try:
                user = User.objects.get(id=user_id)
                if user != request.user:  # Don't add creator twice
                    Participant.objects.create(
                        conversation=conversation,
                        user=user,
                        role=Participant.Role.MEMBER,
                    )
            except User.DoesNotExist:
                pass

        return conversation
