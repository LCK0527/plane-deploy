# Third party imports
from rest_framework import serializers

# Module imports
from plane.db.models import AIChatConversation, AIChatMessage
from .base import BaseSerializer


class AIChatMessageSerializer(BaseSerializer):
    """Serializer for AI chat messages."""

    class Meta:
        model = AIChatMessage
        fields = [
            "id",
            "conversation",
            "role",
            "content",
            "token_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "workspace",
            "project",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        ]


class AIChatConversationSerializer(BaseSerializer):
    """Serializer for AI chat conversations with message count."""

    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = AIChatConversation
        fields = [
            "id",
            "workspace",
            "user",
            "title",
            "is_archived",
            "message_count",
            "last_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "workspace",
            "user",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        ]

    def get_message_count(self, obj):
        """Get the number of messages in this conversation."""
        return obj.messages.count()

    def get_last_message(self, obj):
        """Get the last message in this conversation."""
        last_message = obj.messages.order_by("-created_at").first()
        if last_message:
            return {
                "id": str(last_message.id),
                "role": last_message.role,
                "content": last_message.content[:100],  # First 100 chars
                "created_at": last_message.created_at,
            }
        return None


class AIChatConversationDetailSerializer(AIChatConversationSerializer):
    """Serializer for AI chat conversation with all messages."""

    messages = AIChatMessageSerializer(many=True, read_only=True)

    class Meta(AIChatConversationSerializer.Meta):
        fields = AIChatConversationSerializer.Meta.fields + ["messages"]


class AIChatConversationCreateSerializer(BaseSerializer):
    """Serializer for creating a new AI chat conversation."""

    class Meta:
        model = AIChatConversation
        fields = ["title"]
        read_only_fields = [
            "id",
            "workspace",
            "user",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        ]


class AIChatMessageCreateSerializer(BaseSerializer):
    """Serializer for creating a new AI chat message."""

    class Meta:
        model = AIChatMessage
        fields = ["conversation", "role", "content"]
        read_only_fields = [
            "id",
            "workspace",
            "project",
            "token_count",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        ]


class AIChatSendMessageSerializer(serializers.Serializer):
    """Serializer for sending a message to AI and getting response."""

    conversation_id = serializers.UUIDField(required=False, allow_null=True)
    message = serializers.CharField(required=True)
    title = serializers.CharField(required=False, allow_blank=True)

