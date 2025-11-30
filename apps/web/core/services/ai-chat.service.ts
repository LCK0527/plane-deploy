import { API_BASE_URL } from "@plane/constants";
import { APIService } from "@/services/api.service";

export interface AIChatMessage {
  id: string;
  conversation: string;
  role: "user" | "assistant" | "system";
  content: string;
  token_count?: number;
  created_at: string;
  updated_at: string;
}

export interface AIChatConversation {
  id: string;
  workspace: string;
  user: string;
  title: string;
  is_archived: boolean;
  message_count?: number;
  last_message?: {
    id: string;
    role: string;
    content: string;
    created_at: string;
  };
  messages?: AIChatMessage[];
  created_at: string;
  updated_at: string;
}

export class AIChatService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  async getConversations(workspaceSlug: string): Promise<AIChatConversation[]> {
    return this.get(`/api/workspaces/${workspaceSlug}/ai-chat/conversations/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async getConversation(
    workspaceSlug: string,
    conversationId: string
  ): Promise<AIChatConversation> {
    return this.get(`/api/workspaces/${workspaceSlug}/ai-chat/conversations/${conversationId}/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async createConversation(
    workspaceSlug: string,
    data: { title?: string }
  ): Promise<AIChatConversation> {
    return this.post(`/api/workspaces/${workspaceSlug}/ai-chat/conversations/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async deleteConversation(workspaceSlug: string, conversationId: string): Promise<void> {
    return this.delete(`/api/workspaces/${workspaceSlug}/ai-chat/conversations/${conversationId}/`)
      .then(() => undefined)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async updateConversationTitle(
    workspaceSlug: string,
    conversationId: string,
    title: string
  ): Promise<AIChatConversation> {
    return this.patch(`/api/workspaces/${workspaceSlug}/ai-chat/conversations/${conversationId}/title/`, { title })
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async archiveConversation(workspaceSlug: string, conversationId: string): Promise<void> {
    return this.post(`/api/workspaces/${workspaceSlug}/ai-chat/conversations/${conversationId}/archive/`)
      .then(() => undefined)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async sendMessage(
    workspaceSlug: string,
    data: {
      conversation_id?: string;
      message: string;
      title?: string;
    }
  ): Promise<AIChatConversation> {
    return this.post(`/api/workspaces/${workspaceSlug}/ai-chat/send-message/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async truncateConversation(
    workspaceSlug: string,
    conversationId: string,
    messageId: string
  ): Promise<{ conversation: AIChatConversation; deleted_count: number }> {
    return this.post(
      `/api/workspaces/${workspaceSlug}/ai-chat/conversations/${conversationId}/truncate/${messageId}/`
    )
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }
}

