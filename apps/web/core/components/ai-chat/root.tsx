"use client";

import { observer } from "mobx-react";
import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import useSWR from "swr";
// plane imports
import { cn } from "@plane/utils";
import { ResizableSidebar } from "@/components/sidebar/resizable-sidebar";
// components
import { AIChatHistorySidebar } from "./history-sidebar";
import { AIChatInterface } from "./chat-interface";
// services
import { AIChatService, type AIChatConversation } from "@/services/ai-chat.service";

const aiChatService = new AIChatService();

export const AIChatView = observer(() => {
  const { workspaceSlug } = useParams();
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [sidebarWidth, setSidebarWidth] = useState(280);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [showPeek, setShowPeek] = useState(false);

  // Fetch conversations
  const { data: conversations, mutate: mutateConversations } = useSWR<AIChatConversation[]>(
    workspaceSlug ? `AI_CHAT_CONVERSATIONS_${workspaceSlug}` : null,
    workspaceSlug ? () => aiChatService.getConversations(workspaceSlug.toString()) : null,
    {
      revalidateIfStale: true,
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
    }
  );

  // Auto-select first conversation if none selected (but only if user hasn't explicitly started a new conversation)
  const [hasStartedNewConversation, setHasStartedNewConversation] = useState(false);
  
  useEffect(() => {
    if (conversations && conversations.length > 0 && !selectedConversationId && !hasStartedNewConversation) {
      setSelectedConversationId(conversations[0].id);
    }
  }, [conversations, selectedConversationId, hasStartedNewConversation]);

  const handleNewConversation = () => {
    setSelectedConversationId(null);
    setHasStartedNewConversation(true);
  };

  // Reset flag when a new conversation is created
  useEffect(() => {
    if (selectedConversationId) {
      setHasStartedNewConversation(false);
    }
  }, [selectedConversationId]);

  const handleSelectConversation = (conversationId: string) => {
    setSelectedConversationId(conversationId);
  };

  const handleDeleteConversation = async (conversationId: string) => {
    if (!workspaceSlug) return;
    try {
      await aiChatService.deleteConversation(workspaceSlug.toString(), conversationId);
      if (selectedConversationId === conversationId) {
        setSelectedConversationId(null);
      }
      mutateConversations();
    } catch (error) {
      console.error("Failed to delete conversation:", error);
    }
  };

  const handleUpdateTitle = async (conversationId: string, newTitle: string) => {
    if (!workspaceSlug) return;
    try {
      await aiChatService.updateConversationTitle(workspaceSlug.toString(), conversationId, newTitle);
      mutateConversations();
    } catch (error) {
      console.error("Failed to update title:", error);
    }
  };

  const handleMessageSent = () => {
    mutateConversations();
  };

  return (
    <div className="relative flex h-full w-full overflow-hidden">
      {/* History Sidebar */}
      <ResizableSidebar
        isCollapsed={isSidebarCollapsed}
        toggleCollapsed={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        width={sidebarWidth}
        setWidth={setSidebarWidth}
        showPeek={showPeek}
        togglePeek={setShowPeek}
        minWidth={240}
        maxWidth={400}
        defaultWidth={280}
      >
        <AIChatHistorySidebar
          conversations={conversations || []}
          selectedConversationId={selectedConversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          onDeleteConversation={handleDeleteConversation}
          onUpdateTitle={handleUpdateTitle}
        />
      </ResizableSidebar>

      {/* Chat Interface */}
      <div className={cn("flex-1 flex flex-col h-full overflow-hidden")}>
        <AIChatInterface
          workspaceSlug={workspaceSlug?.toString() || ""}
          conversationId={selectedConversationId}
          onMessageSent={handleMessageSent}
          onNewConversationCreated={(conversationId) => {
            setSelectedConversationId(conversationId);
            mutateConversations();
          }}
        />
      </div>
    </div>
  );
});

