"use client";

import { observer } from "mobx-react";
import { useState } from "react";
import { Plus, MoreVertical, Trash2, Edit2 } from "lucide-react";
// plane imports
import { Button } from "@plane/propel/button";
import { CustomMenu } from "@plane/ui";
import { cn } from "@plane/utils";
// components
import { ScrollArea } from "@plane/ui";
// types
import type { AIChatConversation } from "@/services/ai-chat.service";

interface Props {
  conversations: AIChatConversation[];
  selectedConversationId: string | null;
  onSelectConversation: (conversationId: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (conversationId: string) => void;
  onUpdateTitle: (conversationId: string, newTitle: string) => void;
}

export const AIChatHistorySidebar = observer((props: Props) => {
  const {
    conversations,
    selectedConversationId,
    onSelectConversation,
    onNewConversation,
    onDeleteConversation,
    onUpdateTitle,
  } = props;

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  const handleStartEdit = (conversation: AIChatConversation) => {
    setEditingId(conversation.id);
    setEditTitle(conversation.title);
  };

  const handleSaveEdit = (conversationId: string) => {
    if (editTitle.trim()) {
      onUpdateTitle(conversationId, editTitle.trim());
    }
    setEditingId(null);
    setEditTitle("");
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditTitle("");
  };

  return (
    <div className="flex flex-col h-full w-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-custom-border-200">
        <h2 className="text-lg font-semibold text-custom-text-100">歷史記錄</h2>
        <Button 
          variant="neutral-primary" 
          size="sm" 
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onNewConversation();
          }}
          type="button"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {/* Conversations List */}
      <ScrollArea className="flex-1">
        <div className="flex flex-col p-2">
          {conversations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <p className="text-sm text-custom-text-400">還沒有對話記錄</p>
              <Button
                variant="neutral-primary"
                size="sm"
                className="mt-4"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  onNewConversation();
                }}
                type="button"
              >
                <Plus className="h-4 w-4 mr-2" />
                開始新對話
              </Button>
            </div>
          ) : (
            conversations.map((conversation) => (
              <div
                key={conversation.id}
                className={cn(
                  "group relative flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors",
                  selectedConversationId === conversation.id
                    ? "bg-custom-background-80"
                    : "hover:bg-custom-background-90"
                )}
                onClick={() => onSelectConversation(conversation.id)}
              >
                {editingId === conversation.id ? (
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    onBlur={() => handleSaveEdit(conversation.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        handleSaveEdit(conversation.id);
                      } else if (e.key === "Escape") {
                        handleCancelEdit();
                      }
                    }}
                    className="flex-1 px-2 py-1 text-sm border border-custom-border-300 rounded bg-custom-background-100 focus:outline-none focus:ring-2 focus:ring-custom-primary-100"
                    autoFocus
                    onClick={(e) => e.stopPropagation()}
                  />
                ) : (
                  <>
                    <div className="flex-1 min-w-0 overflow-hidden">
                      <p className="text-sm font-medium text-custom-text-100 truncate">
                        {conversation.title}
                      </p>
                    </div>
                    <div className="flex-shrink-0" onClick={(e) => e.stopPropagation()}>
                      <CustomMenu
                        placement="bottom-end"
                        closeOnSelect
                        customButton={
                          <button
                            type="button"
                            className="opacity-0 group-hover:opacity-100 p-1 hover:bg-custom-background-80 rounded transition-opacity"
                            aria-label="更多選項"
                          >
                            <MoreVertical className="h-4 w-4 text-custom-text-400" />
                          </button>
                        }
                      >
                        <CustomMenu.MenuItem
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStartEdit(conversation);
                          }}
                        >
                          <div className="flex items-center gap-2">
                            <Edit2 className="h-3.5 w-3.5" />
                            <span>更名</span>
                          </div>
                        </CustomMenu.MenuItem>
                        <CustomMenu.MenuItem
                          onClick={(e) => {
                            e.stopPropagation();
                            if (confirm("確定要刪除這個對話嗎？")) {
                              onDeleteConversation(conversation.id);
                            }
                          }}
                        >
                          <div className="flex items-center gap-2 text-red-500">
                            <Trash2 className="h-3.5 w-3.5" />
                            <span>刪除</span>
                          </div>
                        </CustomMenu.MenuItem>
                      </CustomMenu>
                    </div>
                  </>
                )}
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
});

