from django.urls import path

from plane.app.views import (
    AIChatConversationViewSet,
    AIChatSendMessageEndpoint,
    AIChatTruncateConversationEndpoint,
)

urlpatterns = [
    # AI Chat conversations
    path(
        "workspaces/<str:slug>/ai-chat/conversations/",
        AIChatConversationViewSet.as_view({"get": "list", "post": "create"}),
        name="ai-chat-conversations",
    ),
    path(
        "workspaces/<str:slug>/ai-chat/conversations/<uuid:pk>/",
        AIChatConversationViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="ai-chat-conversation-detail",
    ),
    path(
        "workspaces/<str:slug>/ai-chat/conversations/<uuid:pk>/archive/",
        AIChatConversationViewSet.as_view({"post": "archive"}),
        name="ai-chat-conversation-archive",
    ),
    path(
        "workspaces/<str:slug>/ai-chat/conversations/<uuid:pk>/title/",
        AIChatConversationViewSet.as_view({"patch": "update_title"}),
        name="ai-chat-conversation-update-title",
    ),
    # Send message to AI
    path(
        "workspaces/<str:slug>/ai-chat/send-message/",
        AIChatSendMessageEndpoint.as_view(),
        name="ai-chat-send-message",
    ),
    # Truncate conversation from a message
    path(
        "workspaces/<str:slug>/ai-chat/conversations/<uuid:conversation_id>/truncate/<uuid:message_id>/",
        AIChatTruncateConversationEndpoint.as_view(),
        name="ai-chat-truncate-conversation",
    ),
]

