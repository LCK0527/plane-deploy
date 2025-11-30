# Python imports
import json
from typing import Optional

# Django imports
from rest_framework import status
from rest_framework.response import Response

# Third party imports
from openai import OpenAI

# Module imports
from plane.app.permissions import allow_permission, ROLE
from plane.app.views.base import BaseAPIView, BaseViewSet
from plane.db.models import AIChatConversation, AIChatMessage, Profile, Workspace
from plane.app.serializers.ai_chat import (
    AIChatConversationSerializer,
    AIChatConversationDetailSerializer,
    AIChatConversationCreateSerializer,
    AIChatMessageSerializer,
    AIChatSendMessageSerializer,
)
from plane.utils.exception_logger import log_exception


class AIChatConversationViewSet(BaseViewSet):
    """
    ViewSet for managing AI chat conversations.
    """

    serializer_class = AIChatConversationSerializer
    model = AIChatConversation

    def get_queryset(self):
        workspace_slug = self.kwargs.get("slug")
        return (
            AIChatConversation.objects.filter(
                workspace__slug=workspace_slug,
                user=self.request.user,
                is_archived=False,
            )
            .select_related("user", "workspace")
            .prefetch_related("messages")
            .order_by("-updated_at")
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AIChatConversationDetailSerializer
        elif self.action == "create":
            return AIChatConversationCreateSerializer
        return AIChatConversationSerializer

    def perform_create(self, serializer):
        workspace_slug = self.kwargs.get("slug")
        workspace = Workspace.objects.get(slug=workspace_slug)
        serializer.save(
            workspace=workspace,
            user=self.request.user,
            project=None,  # AI Chat doesn't use projects
        )

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def archive(self, request, slug, pk):
        """Archive a conversation."""
        conversation = AIChatConversation.objects.get(
            pk=pk,
            workspace__slug=slug,
            user=request.user,
        )
        conversation.is_archived = True
        conversation.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def update_title(self, request, slug, pk):
        """Update conversation title."""
        conversation = AIChatConversation.objects.get(
            pk=pk,
            workspace__slug=slug,
            user=request.user,
        )
        new_title = request.data.get("title", "").strip()
        if not new_title:
            return Response(
                {"error": "Title cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        conversation.title = new_title
        conversation.save()
        serializer = AIChatConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AIChatSendMessageEndpoint(BaseAPIView):
    """
    Endpoint for sending a message to AI and getting a response.
    Creates a new conversation if conversation_id is not provided.
    """

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug):
        try:
            # Log request data for debugging
            import logging
            logger = logging.getLogger("plane.api.request")
            logger.info(f"AI Chat send-message request data: {request.data}")
            
            serializer = AIChatSendMessageSerializer(data=request.data)
            if not serializer.is_valid():
                logger.warning(f"Serializer validation errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            validated_data = serializer.validated_data
            if not validated_data:
                return Response(
                    {"error": "Invalid request data"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            workspace = Workspace.objects.get(slug=slug)
            user_message = validated_data.get("message", "")
            if not user_message or not user_message.strip():
                return Response(
                    {"error": "Message is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user_message = user_message.strip()
            conversation_id = validated_data.get("conversation_id")
            title = validated_data.get("title", "").strip() if validated_data.get("title") else ""

            # Get user's LLM API key
            try:
                profile = Profile.objects.get(user=request.user)
                if profile.theme and isinstance(profile.theme, dict):
                    user_llm_api_key = profile.theme.get("llm_api_key")
                else:
                    user_llm_api_key = None
            except Profile.DoesNotExist:
                user_llm_api_key = None
            except (AttributeError, TypeError) as e:
                log_exception(e)
                user_llm_api_key = None

            if not user_llm_api_key:
                return Response(
                    {"error": "LLM API key not configured. Please set your API key in account settings."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get or create conversation
            if conversation_id:
                conversation = AIChatConversation.objects.get(
                    pk=conversation_id,
                    workspace=workspace,
                    user=request.user,
                )
            else:
                # Create new conversation
                conversation_title = title if title else "New Conversation"
                conversation = AIChatConversation.objects.create(
                    workspace=workspace,
                    user=request.user,
                    title=conversation_title,
                    project=None,
                )

            # Save user message
            user_msg = AIChatMessage.objects.create(
                workspace=workspace,
                conversation=conversation,
                role="user",
                content=user_message,
                project=None,
            )

            # Get conversation history for context
            previous_messages = conversation.messages.order_by("created_at").values("role", "content")
            messages_for_llm = [
                {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                for msg in previous_messages
            ]

            # Call LLM
            try:
                client = OpenAI(api_key=user_llm_api_key)
                chat_completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages_for_llm,
                    temperature=0.7,
                )
                if not chat_completion.choices or len(chat_completion.choices) == 0:
                    raise ValueError("No response from LLM API")
                if not chat_completion.choices[0].message or not chat_completion.choices[0].message.content:
                    raise ValueError("Empty response from LLM API")
                ai_response = chat_completion.choices[0].message.content
                token_count = None
                if hasattr(chat_completion, "usage") and chat_completion.usage:
                    token_count = getattr(chat_completion.usage, "total_tokens", None)
            except Exception as e:
                log_exception(e)
                return Response(
                    {"error": f"Failed to call LLM API: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Save AI response
            ai_msg = AIChatMessage.objects.create(
                workspace=workspace,
                conversation=conversation,
                role="assistant",
                content=ai_response,
                token_count=token_count,
                project=None,
            )

            # Update conversation title if it's still "New Conversation" and this is the first exchange
            if conversation.title == "New Conversation" and conversation.messages.count() == 2:
                # Generate a title from the first user message
                try:
                    title_client = OpenAI(api_key=user_llm_api_key)
                    title_completion = title_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "system",
                                "content": "Generate a short, descriptive title (max 50 characters) for this conversation based on the first message. Return only the title, no quotes, no explanation.",
                            },
                            {"role": "user", "content": user_message},
                        ],
                        temperature=0.3,
                        max_tokens=20,
                    )
                    if not title_completion.choices or len(title_completion.choices) == 0:
                        generated_title = "New Conversation"
                    elif not title_completion.choices[0].message or not title_completion.choices[0].message.content:
                        generated_title = "New Conversation"
                    else:
                        generated_title = title_completion.choices[0].message.content.strip()
                        # Remove quotes if present
                        generated_title = generated_title.strip('"').strip("'")
                    if generated_title and len(generated_title) <= 255:
                        conversation.title = generated_title
                        conversation.save()
                except:
                    # If title generation fails, keep "New Conversation"
                    pass

            # Return conversation with all messages
            serializer = AIChatConversationDetailSerializer(conversation)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except AIChatConversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Workspace.DoesNotExist:
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except KeyError as e:
            log_exception(e)
            return Response(
                {"error": f"The required key does not exist: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            log_exception(e)
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AIChatTruncateConversationEndpoint(BaseAPIView):
    """
    Endpoint for truncating conversation from a specific message.
    Deletes the specified message and all messages after it.
    """

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER], level="WORKSPACE")
    def post(self, request, slug, conversation_id, message_id):
        try:
            workspace = Workspace.objects.get(slug=slug)
            conversation = AIChatConversation.objects.get(
                pk=conversation_id,
                workspace=workspace,
                user=request.user,
            )
            
            # Get the message to truncate from
            message = AIChatMessage.objects.get(
                pk=message_id,
                conversation=conversation,
            )
            
            # Delete this message and all messages after it
            messages_to_delete = AIChatMessage.objects.filter(
                conversation=conversation,
                created_at__gte=message.created_at,
            )
            
            deleted_count = messages_to_delete.count()
            messages_to_delete.delete()
            
            # Return updated conversation
            conversation.refresh_from_db()
            serializer = AIChatConversationDetailSerializer(conversation)
            
            return Response({
                "conversation": serializer.data,
                "deleted_count": deleted_count,
            }, status=status.HTTP_200_OK)
            
        except AIChatConversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except AIChatMessage.DoesNotExist:
            return Response(
                {"error": "Message not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Workspace.DoesNotExist:
            return Response(
                {"error": "Workspace not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            log_exception(e)
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

