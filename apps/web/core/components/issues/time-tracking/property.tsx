"use client";

import React, { useEffect, useState } from "react";
import { observer } from "mobx-react";
import { Timer, Play, Square, Plus, Edit2, Trash2, Clock } from "lucide-react";
import { useTranslation } from "@plane/i18n";
import { Button, TOAST_TYPE, setToast } from "@plane/ui";
import { TimeEntryService, type ITimeEntry, type ITimeEntrySummary } from "@/services/issue/time_entry.service";
import { useProject } from "@/hooks/store/use-project";
import { useUser } from "@/hooks/store/user";

type Props = {
  workspaceSlug: string;
  projectId: string;
  issueId: string;
  disabled: boolean;
};

const timeEntryService = new TimeEntryService();

export const IssueTimeTrackingProperty: React.FC<Props> = observer((props) => {
  const { workspaceSlug, projectId, issueId, disabled } = props;
  const { t } = useTranslation();
  const { getProjectById } = useProject();
  const { data: currentUser } = useUser();
  
  const [timeEntries, setTimeEntries] = useState<ITimeEntry[]>([]);
  const [summary, setSummary] = useState<ITimeEntrySummary | null>(null);
  const [activeTimer, setActiveTimer] = useState<ITimeEntry | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [manualDuration, setManualDuration] = useState("");
  const [manualNote, setManualNote] = useState("");
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  
  const project = getProjectById(projectId);
  const isTimeTrackingEnabled = project?.is_time_tracking_enabled ?? false;
  
  // Fetch data
  const fetchData = React.useCallback(async () => {
    if (!isTimeTrackingEnabled) return;
    
    setIsLoading(true);
    try {
      const [entriesData, summaryData, activeTimerData] = await Promise.all([
        timeEntryService.getTimeEntries(workspaceSlug, projectId, issueId).catch(() => []),
        timeEntryService.getTimeEntrySummary(workspaceSlug, projectId, issueId).catch(() => null),
        timeEntryService.getActiveTimer(workspaceSlug, projectId, issueId).catch(() => ({ active_timer: null })),
      ]);
      
      setTimeEntries(entriesData || []);
      setSummary(summaryData);
      setActiveTimer(activeTimerData?.active_timer || null);
    } catch (error: any) {
      // Only show toast for non-network errors
      if (error?.code !== "ERR_NETWORK" && error?.code !== "ERR_CONNECTION_RESET" && error?.code !== "ERR_SOCKET_NOT_CONNECTED") {
        setToast({
          type: TOAST_TYPE.ERROR,
          title: "Error",
          message: error?.error || "Failed to load time tracking data",
        });
      }
    } finally {
      setIsLoading(false);
    }
  }, [workspaceSlug, projectId, issueId, isTimeTrackingEnabled]);
  
  useEffect(() => {
    if (!isTimeTrackingEnabled) return;
    
    fetchData();
  }, [fetchData]);
  
  // Separate effect for polling active timer from backend (every 5 seconds)
  useEffect(() => {
    if (!isTimeTrackingEnabled || !activeTimer) return;
    
    const interval = setInterval(() => {
      timeEntryService.getActiveTimer(workspaceSlug, projectId, issueId).then((data) => {
        setActiveTimer(data.active_timer);
      }).catch(() => {
        // Silently fail polling if backend is unavailable
      });
    }, 5000);
    
    return () => clearInterval(interval);
  }, [workspaceSlug, projectId, issueId, isTimeTrackingEnabled, activeTimer?.id]);
  
  // Separate effect for updating elapsed time display every second (client-side)
  useEffect(() => {
    if (!isTimeTrackingEnabled || !activeTimer || !activeTimer.started_at) {
      setElapsedSeconds(0);
      return;
    }
    
    // Update immediately
    const startTime = new Date(activeTimer.started_at).getTime();
    const updateElapsed = () => {
      const now = Date.now();
      setElapsedSeconds(Math.floor((now - startTime) / 1000));
    };
    updateElapsed();
    
    // Update every second
    const interval = setInterval(updateElapsed, 1000);
    return () => clearInterval(interval);
  }, [isTimeTrackingEnabled, activeTimer?.id, activeTimer?.started_at]);
  
  const handleStartTimer = async () => {
    if (disabled || !isTimeTrackingEnabled) return;
    
    try {
      const timer = await timeEntryService.startTimer(workspaceSlug, projectId, issueId);
      setActiveTimer(timer);
      fetchData().catch(() => {
        // Silently handle fetch errors
      });
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Success",
        message: "Timer started",
      });
    } catch (error: any) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Error",
        message: error?.error || "Failed to start timer",
      });
    }
  };
  
  const handleStopTimer = async () => {
    if (disabled || !isTimeTrackingEnabled) return;
    
    try {
      await timeEntryService.stopTimer(workspaceSlug, projectId, issueId);
      setActiveTimer(null);
      fetchData().catch(() => {
        // Silently handle fetch errors
      });
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Success",
        message: "Timer stopped",
      });
    } catch (error: any) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Error",
        message: error?.error || "Failed to stop timer",
      });
    }
  };
  
  const handleAddManualEntry = async () => {
    if (disabled || !manualDuration || !isTimeTrackingEnabled) return;
    
    const durationSeconds = parseInt(manualDuration) * 60; // Convert minutes to seconds
    if (isNaN(durationSeconds) || durationSeconds <= 0) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Error",
        message: "Please enter a valid duration in minutes",
      });
      return;
    }
    
    try {
      await timeEntryService.createTimeEntry(workspaceSlug, projectId, issueId, {
        duration_seconds: durationSeconds,
        note: manualNote || undefined,
        is_billable: false,
      });
      
      setShowAddForm(false);
      setManualDuration("");
      setManualNote("");
      fetchData().catch(() => {
        // Silently handle fetch errors
      });
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Success",
        message: "Time entry added",
      });
    } catch (error: any) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Error",
        message: error?.error || "Failed to add time entry",
      });
    }
  };
  
  const handleDeleteEntry = async (entryId: string) => {
    if (disabled || !isTimeTrackingEnabled) return;
    
    if (!confirm("Are you sure you want to delete this time entry?")) return;
    
    try {
      await timeEntryService.deleteTimeEntry(workspaceSlug, projectId, issueId, entryId);
      fetchData().catch(() => {
        // Silently handle fetch errors
      });
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Success",
        message: "Time entry deleted",
      });
    } catch (error: any) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Error",
        message: error?.error || "Failed to delete time entry",
      });
    }
  };
  
  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };
  
  // Early return if time tracking is disabled
  if (!isTimeTrackingEnabled) {
    return null;
  }
  
  // Use elapsedSeconds state for real-time updates, fallback to computed value
  const currentElapsed = activeTimer && activeTimer.started_at ? elapsedSeconds : 0;
  
  return (
    <div className="flex min-h-8 gap-2">
      <div className="flex w-2/5 flex-shrink-0 gap-1 pt-2 text-sm text-custom-text-300">
        <Timer className="h-4 w-4 flex-shrink-0" />
        <span>Time Tracking</span>
      </div>
      <div className="w-3/5 flex-grow space-y-2">
        {/* Summary */}
        {summary && (
          <div className="space-y-1 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-custom-text-400">Total Logged:</span>
              <span className="font-medium">{formatDuration(summary.total_seconds)}</span>
            </div>
            {summary.estimated_time_minutes && (
              <div className="flex items-center justify-between">
                <span className="text-custom-text-400">Estimated:</span>
                <span className="font-medium">{formatDuration(summary.estimated_time_minutes * 60)}</span>
              </div>
            )}
          </div>
        )}
        
        {/* Active Timer */}
        {activeTimer && (
          <div className="rounded-md border border-custom-border-200 bg-custom-background-90 p-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
                <span className="text-xs font-medium">Timer Running</span>
              </div>
              <span className="text-xs font-mono">
                {formatDuration(currentElapsed)}
              </span>
            </div>
            {!disabled && (
              <Button
                variant="transparent"
                size="sm"
                className="mt-2 w-full"
                onClick={handleStopTimer}
              >
                <Square className="h-3 w-3" />
                Stop Timer
              </Button>
            )}
          </div>
        )}
        
        {/* Timer Controls */}
        {!activeTimer && !disabled && (
          <Button
            variant="outline-primary"
            size="sm"
            className="w-full"
            onClick={handleStartTimer}
          >
            <Play className="h-3 w-3" />
            Start Timer
          </Button>
        )}
        
        {/* Add Manual Entry */}
        {!disabled && (
          <>
            {!showAddForm ? (
              <Button
                variant="transparent"
                size="sm"
                className="w-full"
                onClick={() => setShowAddForm(true)}
              >
                <Plus className="h-3 w-3" />
                Add Time
              </Button>
            ) : (
              <div className="space-y-2 rounded-md border border-custom-border-200 bg-custom-background-90 p-2">
                <input
                  type="number"
                  placeholder="Minutes"
                  value={manualDuration}
                  onChange={(e) => setManualDuration(e.target.value)}
                  className="w-full rounded border border-custom-border-200 bg-custom-background-100 px-2 py-1 text-xs"
                />
                <input
                  type="text"
                  placeholder="Note (optional)"
                  value={manualNote}
                  onChange={(e) => setManualNote(e.target.value)}
                  className="w-full rounded border border-custom-border-200 bg-custom-background-100 px-2 py-1 text-xs"
                />
                <div className="flex gap-2">
                  <Button
                    variant="primary"
                    size="sm"
                    className="flex-1"
                    onClick={handleAddManualEntry}
                  >
                    Add
                  </Button>
                  <Button
                    variant="transparent"
                    size="sm"
                    onClick={() => {
                      setShowAddForm(false);
                      setManualDuration("");
                      setManualNote("");
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
        
        {/* Recent Entries */}
        {timeEntries.length > 0 && (
          <div className="mt-2 space-y-1">
            <div className="text-xs font-medium text-custom-text-300">Recent Entries</div>
            <div className="max-h-32 space-y-1 overflow-y-auto">
              {timeEntries.slice(0, 5).map((entry) => (
                <div
                  key={entry.id}
                  className="flex items-center justify-between rounded border border-custom-border-200 bg-custom-background-90 px-2 py-1 text-xs"
                >
                  <div className="flex-1 truncate">
                    <div className="font-medium">{formatDuration(entry.duration_seconds)}</div>
                    {entry.note && (
                      <div className="truncate text-custom-text-400">{entry.note}</div>
                    )}
                  </div>
                  {!disabled && entry.user === currentUser?.id && (
                    <Button
                      variant="transparent"
                      size="sm"
                      onClick={() => handleDeleteEntry(entry.id)}
                      className="ml-2"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
});

