"use client";

import { observer } from "mobx-react";
import { useState, useEffect, useRef } from "react";
import useSWR from "swr";
import { Send, Loader2 } from "lucide-react";
// plane imports
import { Button } from "@plane/propel/button";
import { TextArea } from "@plane/ui";
import { cn } from "@plane/utils";
// components
import { ScrollArea } from "@plane/ui";
import { AIChatMessageItem } from "./message-item";
// services
import { AIChatService, type AIChatConversation, type AIChatMessage } from "@/services/ai-chat.service";

const aiChatService = new AIChatService();

interface Props {
  workspaceSlug: string;
  conversationId: string | null;
  onMessageSent: () => void;
  onNewConversationCreated: (conversationId: string) => void;
}

export const AIChatInterface = observer((props: Props) => {
  const { workspaceSlug, conversationId, onMessageSent, onNewConversationCreated } = props;
  const [message, setMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Fetch conversation details
  const { data: conversation, mutate: mutateConversation } = useSWR<AIChatConversation>(
    conversationId && workspaceSlug ? `AI_CHAT_CONVERSATION_${workspaceSlug}_${conversationId}` : null,
    conversationId && workspaceSlug
      ? () => aiChatService.getConversation(workspaceSlug, conversationId)
      : null,
    {
      revalidateIfStale: true,
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
    }
  );

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation?.messages]);

  const handleSend = async () => {
    const trimmedMessage = message.trim();
    if (!trimmedMessage || isSending || !workspaceSlug) return;

    setIsSending(true);
    const currentMessage = trimmedMessage;
    setMessage("");

    try {
      const response = await aiChatService.sendMessage(workspaceSlug, {
        conversation_id: conversationId || undefined,
        message: currentMessage,
      });

      if (!conversationId && response.id) {
        onNewConversationCreated(response.id);
      }

      mutateConversation();
      onMessageSent();
    } catch (error: any) {
      console.error("Failed to send message:", error);
      setMessage(currentMessage); // Restore message on error
      alert(error?.error || "發送消息失敗，請重試");
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Don't send message if user is composing (e.g., typing Chinese/Japanese)
    // Check nativeEvent.isComposing to detect IME composition state
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleEditMessage = async (messageId: string) => {
    if (!conversationId || !workspaceSlug) return;
    
    // Find the message to edit
    const messageToEdit = messages.find((msg) => msg.id === messageId);
    if (!messageToEdit || messageToEdit.role !== "user") return;
    
    try {
      // Truncate conversation from this message (including the message itself)
      await aiChatService.truncateConversation(workspaceSlug, conversationId, messageId);
      
      // Update conversation
      await mutateConversation();
      
      // Set the message content in the input box
      setMessage(messageToEdit.content);
      
      // Focus on the textarea
      setTimeout(() => {
        textareaRef.current?.focus();
        // Scroll to bottom of textarea
        if (textareaRef.current) {
          textareaRef.current.scrollTop = textareaRef.current.scrollHeight;
        }
      }, 100);
    } catch (error: any) {
      console.error("Failed to edit message:", error);
      alert(error?.error || "編輯消息失敗，請重試");
    }
  };

  const messages = conversation?.messages || [];

  return (
    <div className="flex flex-col h-full w-full">
      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4">
        <div className="max-w-3xl mx-auto w-full space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <p className="text-lg font-medium text-custom-text-200 mb-2">開始新的對話</p>
              <p className="text-sm text-custom-text-400">輸入您的問題，AI 將為您提供幫助</p>
            </div>
          ) : (
            messages.map((msg: AIChatMessage) => (
              <AIChatMessageItem
                key={msg.id}
                message={msg}
                isUser={msg.role === "user"}
                onEdit={msg.role === "user" ? handleEditMessage : undefined}
              />
            ))
          )}
          {isSending && (
            <div className="flex gap-3 justify-start">
              <div className="bg-custom-background-80 rounded-lg px-4 py-2">
                <Loader2 className="h-4 w-4 animate-spin text-custom-text-400" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t border-custom-border-200 p-4 bg-custom-background-100">
        <div className="max-w-3xl mx-auto w-full">
          <div className="flex items-end gap-2">
            <TextArea
              ref={textareaRef}
              value={message}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="輸入你的問題"
              rows={1}
              className="flex-1 min-h-[44px] max-h-[200px] resize-none"
              disabled={isSending}
            />
            <Button
              onClick={handleSend}
              disabled={!message.trim() || isSending}
            >
              {isSending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
});

