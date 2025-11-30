# Python imports
import uuid

# Django imports
from django.db import models

# Module imports
from plane.db.models.workspace import WorkspaceBaseModel


class AIChatConversation(WorkspaceBaseModel):
    """
    Model for storing AI chat conversations.
    Each conversation belongs to a user and workspace.
    Note: project field from WorkspaceBaseModel is not used (set to null).
    """

    id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True, primary_key=True)
    # User who owns this conversation
    user = models.ForeignKey(
        "db.User",
        on_delete=models.CASCADE,
        related_name="ai_chat_conversations",
    )
    # Conversation title (can be renamed by user)
    title = models.CharField(max_length=255, default="New Conversation")
    # Whether this conversation is archived
    is_archived = models.BooleanField(default=False)

    class Meta:
        verbose_name = "AI Chat Conversation"
        verbose_name_plural = "AI Chat Conversations"
        db_table = "ai_chat_conversations"
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=["workspace", "user", "-updated_at"]),
            models.Index(fields=["workspace", "user", "is_archived", "-updated_at"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.email}"


class AIChatMessage(WorkspaceBaseModel):
    """
    Model for storing individual messages in AI chat conversations.
    """

    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    ]

    id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True, primary_key=True)
    # Conversation this message belongs to
    conversation = models.ForeignKey(
        AIChatConversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    # Message role (user, assistant, system)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")
    # Message content
    content = models.TextField()
    # Optional: token count for tracking usage
    token_count = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "AI Chat Message"
        verbose_name_plural = "AI Chat Messages"
        db_table = "ai_chat_messages"
        ordering = ("created_at",)
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."

