// plane imports
import { API_BASE_URL } from "@plane/constants";
// services
import { APIService } from "@/services/api.service";

export interface ITimeEntry {
  id: string;
  workspace: string;
  project: string;
  issue: string;
  issue_detail?: {
    id: string;
    name: string;
    sequence_id: number;
  };
  user: string;
  user_detail?: {
    id: string;
    email: string;
    display_name: string;
  };
  started_at: string | null;
  ended_at: string | null;
  duration_seconds: number;
  duration_hours: number;
  duration_minutes: number;
  source: "timer" | "manual";
  note: string | null;
  is_billable: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by: string;
  updated_by: string;
}

export interface ITimeEntryCreatePayload {
  duration_seconds: number;
  started_at?: string;
  ended_at?: string;
  note?: string;
  is_billable?: boolean;
}

export interface ITimeEntryUpdatePayload {
  duration_seconds?: number;
  started_at?: string;
  ended_at?: string;
  note?: string;
  is_billable?: boolean;
}

export interface ITimeEntrySummary {
  total_seconds: number;
  total_hours: number;
  estimated_time_minutes: number | null;
  time_by_user: Array<{
    user_id: string;
    user_email: string;
    user_display_name: string;
    total_seconds: number;
    total_hours: number;
    entry_count: number;
  }>;
}

export interface ITimeEntryReportsParams {
  group_by?: "user" | "work_item" | "project" | "module";
  from?: string; // YYYY-MM-DD
  to?: string; // YYYY-MM-DD
  project_id?: string;
  user_id?: string;
}

export interface ITimeEntryReportsResponse {
  group_by: string;
  from_date: string | null;
  to_date: string | null;
  data: any[];
}

export class TimeEntryService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  async getTimeEntries(
    workspaceSlug: string,
    projectId: string,
    issueId: string,
    userId?: string
  ): Promise<ITimeEntry[]> {
    return this.get(
      `/api/workspaces/${workspaceSlug}/projects/${projectId}/issues/${issueId}/time-entries/`,
      {
        params: userId ? { user_id: userId } : {},
      }
    )
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async createTimeEntry(
    workspaceSlug: string,
    projectId: string,
    issueId: string,
    data: ITimeEntryCreatePayload
  ): Promise<ITimeEntry> {
    return this.post(
      `/api/workspaces/${workspaceSlug}/projects/${projectId}/issues/${issueId}/time-entries/`,
      data
    )
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async updateTimeEntry(
    workspaceSlug: string,
    projectId: string,
    issueId: string,
    timeEntryId: string,
    data: ITimeEntryUpdatePayload
  ): Promise<ITimeEntry> {
    return this.patch(
      `/api/workspaces/${workspaceSlug}/projects/${projectId}/issues/${issueId}/time-entries/${timeEntryId}/`,
      data
    )
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async deleteTimeEntry(
    workspaceSlug: string,
    projectId: string,
    issueId: string,
    timeEntryId: string
  ): Promise<void> {
    return this.delete(
      `/api/workspaces/${workspaceSlug}/projects/${projectId}/issues/${issueId}/time-entries/${timeEntryId}/`
    )
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async startTimer(
    workspaceSlug: string,
    projectId: string,
    issueId: string,
    note?: string,
    isBillable?: boolean
  ): Promise<ITimeEntry> {
    return this.post(
      `/api/workspaces/${workspaceSlug}/projects/${projectId}/issues/${issueId}/time-entries/timer/`,
      {
        note: note || "",
        is_billable: isBillable || false,
      }
    )
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async stopTimer(
    workspaceSlug: string,
    projectId: string,
    issueId: string
  ): Promise<ITimeEntry> {
    return this.delete(
      `/api/workspaces/${workspaceSlug}/projects/${projectId}/issues/${issueId}/time-entries/timer/`
    )
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async getActiveTimer(
    workspaceSlug: string,
    projectId: string,
    issueId: string
  ): Promise<{ active_timer: ITimeEntry | null }> {
    return this.get(
      `/api/workspaces/${workspaceSlug}/projects/${projectId}/issues/${issueId}/time-entries/active-timer/`
    )
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async getTimeEntrySummary(
    workspaceSlug: string,
    projectId: string,
    issueId: string
  ): Promise<ITimeEntrySummary> {
    return this.get(
      `/api/workspaces/${workspaceSlug}/projects/${projectId}/issues/${issueId}/time-entries/summary/`
    )
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async getTimeReports(
    workspaceSlug: string,
    params: ITimeEntryReportsParams
  ): Promise<ITimeEntryReportsResponse> {
    return this.get(`/api/workspaces/${workspaceSlug}/time-reports/`, {
      params,
    })
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async exportTimeEntries(
    workspaceSlug: string,
    params: ITimeEntryReportsParams
  ): Promise<Blob> {
    return this.get(`/api/workspaces/${workspaceSlug}/time-reports/export/`, {
      params,
      responseType: "blob",
    })
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }
}

