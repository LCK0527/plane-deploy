# Django imports
from django.db.models import Q, Sum, Count, F, Value, CharField
from django.db.models.functions import TruncDate, Coalesce, Concat
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime, timedelta
import csv
from io import StringIO
from rest_framework import status
from rest_framework.response import Response

# Module imports
from plane.app.permissions import ROLE, allow_permission
from plane.api.serializers.time_entry import (
    TimeEntrySerializer,
    TimeEntryCreateSerializer,
    TimeEntryUpdateSerializer,
)
from plane.db.models import (
    TimeEntry,
    TimeEntrySource,
    Issue,
    Project,
    ModuleIssue,
    CycleIssue,
)
from plane.app.views.base import BaseAPIView, BaseViewSet


class TimeEntryViewSet(BaseViewSet):
    """
    ViewSet for managing time entries.
    
    Provides CRUD operations for time entries with proper permission checks
    and feature toggle validation.
    """
    
    model = TimeEntry
    serializer_class = TimeEntrySerializer
    
    def get_queryset(self):
        """
        Get queryset filtered by workspace, project, and issue.
        """
        workspace_slug = self.kwargs.get("slug")
        project_id = self.kwargs.get("project_id")
        issue_id = self.kwargs.get("issue_id")
        
        queryset = TimeEntry.objects.filter(
            workspace__slug=workspace_slug,
            project_id=project_id,
        )
        
        if issue_id:
            queryset = queryset.filter(issue_id=issue_id)
        
        return queryset.select_related("user", "issue", "project", "workspace")
    
    def _check_time_tracking_enabled(self, project_id):
        """
        Check if time tracking is enabled for the project.
        """
        try:
            project = Project.objects.get(id=project_id)
            if not project.is_time_tracking_enabled:
                return Response(
                    {"error": "Time tracking is not enabled for this project"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return None
    
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST])
    def list(self, request, slug, project_id, issue_id):
        """
        List all time entries for a specific issue.
        """
        # Check if time tracking is enabled
        error_response = self._check_time_tracking_enabled(project_id)
        if error_response:
            return error_response
        
        queryset = self.get_queryset()
        
        # Filter by user if provided
        user_id = request.GET.get("user_id")
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Order by created_at descending
        queryset = queryset.order_by("-created_at")
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER])
    def create(self, request, slug, project_id, issue_id):
        """
        Create a manual time entry.
        """
        # Check if time tracking is enabled
        error_response = self._check_time_tracking_enabled(project_id)
        if error_response:
            return error_response
        
        # Verify issue exists and belongs to project
        try:
            issue = Issue.objects.get(id=issue_id, project_id=project_id, workspace__slug=slug)
        except Issue.DoesNotExist:
            return Response(
                {"error": "Issue not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        serializer = TimeEntryCreateSerializer(data=request.data)
        if serializer.is_valid():
            time_entry_data = serializer.validated_data
            time_entry_data["issue"] = issue
            time_entry_data["user"] = request.user
            time_entry_data["workspace"] = issue.workspace
            time_entry_data["project"] = issue.project
            time_entry_data["source"] = TimeEntrySource.MANUAL
            
            time_entry = TimeEntry.objects.create(**time_entry_data)
            response_serializer = TimeEntrySerializer(time_entry)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER])
    def partial_update(self, request, slug, project_id, issue_id, pk):
        """
        Update a time entry.
        Only the creator or project admins can update.
        """
        # Check if time tracking is enabled
        error_response = self._check_time_tracking_enabled(project_id)
        if error_response:
            return error_response
        
        try:
            time_entry = self.get_queryset().get(pk=pk)
        except TimeEntry.DoesNotExist:
            return Response(
                {"error": "Time entry not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Check permissions: creator or admin
        if time_entry.user != request.user:
            # Check if user is project admin
            from plane.db.models import ProjectMember
            is_admin = ProjectMember.objects.filter(
                project_id=project_id,
                member=request.user,
                role=ROLE.ADMIN,
                is_active=True,
            ).exists()
            if not is_admin:
                return Response(
                    {"error": "You don't have permission to update this time entry"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        
        serializer = TimeEntryUpdateSerializer(time_entry, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            response_serializer = TimeEntrySerializer(time_entry)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER])
    def destroy(self, request, slug, project_id, issue_id, pk):
        """
        Delete a time entry.
        Only the creator or project admins can delete.
        """
        # Check if time tracking is enabled
        error_response = self._check_time_tracking_enabled(project_id)
        if error_response:
            return error_response
        
        try:
            time_entry = self.get_queryset().get(pk=pk)
        except TimeEntry.DoesNotExist:
            return Response(
                {"error": "Time entry not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Check permissions: creator or admin
        if time_entry.user != request.user:
            # Check if user is project admin
            from plane.db.models import ProjectMember
            is_admin = ProjectMember.objects.filter(
                project_id=project_id,
                member=request.user,
                role=ROLE.ADMIN,
                is_active=True,
            ).exists()
            if not is_admin:
                return Response(
                    {"error": "You don't have permission to delete this time entry"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        
        time_entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TimeEntryTimerEndpoint(BaseAPIView):
    """
    Endpoint for timer operations (start/stop).
    """
    
    def _check_time_tracking_enabled(self, project_id):
        """
        Check if time tracking is enabled for the project.
        """
        try:
            project = Project.objects.get(id=project_id)
            if not project.is_time_tracking_enabled:
                return Response(
                    {"error": "Time tracking is not enabled for this project"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return None
    
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER])
    def post(self, request, slug, project_id, issue_id):
        """
        Start a timer for the current user on the specified issue.
        If the user has an active timer on another issue, it will be stopped first.
        """
        # Check if time tracking is enabled
        error_response = self._check_time_tracking_enabled(project_id)
        if error_response:
            return error_response
        
        # Verify issue exists
        try:
            issue = Issue.objects.get(id=issue_id, project_id=project_id, workspace__slug=slug)
        except Issue.DoesNotExist:
            return Response(
                {"error": "Issue not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Check if user already has an active timer on this issue
        active_timer = TimeEntry.objects.filter(
            issue_id=issue_id,
            user=request.user,
            started_at__isnull=False,
            ended_at__isnull=True,
        ).first()
        
        if active_timer:
            return Response(
                {"error": "You already have an active timer on this issue"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Stop any other active timers for this user
        other_active_timers = TimeEntry.objects.filter(
            user=request.user,
            started_at__isnull=False,
            ended_at__isnull=True,
        ).exclude(issue_id=issue_id)
        
        now = timezone.now()
        for timer in other_active_timers:
            timer.ended_at = now
            if timer.started_at:
                delta = now - timer.started_at
                timer.duration_seconds = max(0, int(delta.total_seconds()))
            timer.save()
        
        # Create new timer entry
        time_entry = TimeEntry.objects.create(
            issue=issue,
            user=request.user,
            workspace=issue.workspace,
            project=issue.project,
            started_at=now,
            source=TimeEntrySource.TIMER,
            note=request.data.get("note", ""),
            is_billable=request.data.get("is_billable", False),
        )
        
        serializer = TimeEntrySerializer(time_entry)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER])
    def delete(self, request, slug, project_id, issue_id):
        """
        Stop the active timer for the current user on the specified issue.
        """
        # Check if time tracking is enabled
        error_response = self._check_time_tracking_enabled(project_id)
        if error_response:
            return error_response
        
        # Find active timer
        active_timer = TimeEntry.objects.filter(
            issue_id=issue_id,
            user=request.user,
            started_at__isnull=False,
            ended_at__isnull=True,
        ).first()
        
        if not active_timer:
            return Response(
                {"error": "No active timer found for this issue"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Stop the timer
        now = timezone.now()
        active_timer.ended_at = now
        if active_timer.started_at:
            delta = now - active_timer.started_at
            active_timer.duration_seconds = max(0, int(delta.total_seconds()))
        active_timer.save()
        
        serializer = TimeEntrySerializer(active_timer)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TimeEntryActiveTimerEndpoint(BaseAPIView):
    """
    Endpoint to get the active timer for the current user on an issue.
    """
    
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST])
    def get(self, request, slug, project_id, issue_id):
        """
        Get the active timer for the current user on the specified issue.
        """
        active_timer = TimeEntry.objects.filter(
            issue_id=issue_id,
            user=request.user,
            started_at__isnull=False,
            ended_at__isnull=True,
        ).first()
        
        if not active_timer:
            return Response({"active_timer": None}, status=status.HTTP_200_OK)
        
        serializer = TimeEntrySerializer(active_timer)
        return Response({"active_timer": serializer.data}, status=status.HTTP_200_OK)


class TimeEntrySummaryEndpoint(BaseAPIView):
    """
    Endpoint to get time entry summary for an issue.
    """
    
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST])
    def get(self, request, slug, project_id, issue_id):
        """
        Get time entry summary for an issue:
        - Total time logged
        - Total time by user
        - Estimated time (if set)
        """
        # Check if time tracking is enabled
        try:
            project = Project.objects.get(id=project_id)
            if not project.is_time_tracking_enabled:
                return Response(
                    {"error": "Time tracking is not enabled for this project"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Verify issue exists
        try:
            issue = Issue.objects.get(id=issue_id, project_id=project_id, workspace__slug=slug)
        except Issue.DoesNotExist:
            return Response(
                {"error": "Issue not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Get total time logged
        total_seconds = TimeEntry.objects.filter(
            issue_id=issue_id,
            ended_at__isnull=False,  # Only count completed entries
        ).aggregate(total=Sum("duration_seconds"))["total"] or 0
        
        # Get time by user
        time_by_user = (
            TimeEntry.objects.filter(
                issue_id=issue_id,
                ended_at__isnull=False,
            )
            .values("user_id", "user__email", "user__display_name")
            .annotate(
                total_seconds=Sum("duration_seconds"),
                entry_count=Count("id"),
            )
            .order_by("-total_seconds")
        )
        
        # Format time by user
        time_by_user_list = [
            {
                "user_id": str(item["user_id"]),
                "user_email": item["user__email"],
                "user_display_name": item["user__display_name"],
                "total_seconds": item["total_seconds"],
                "total_hours": round(item["total_seconds"] / 3600.0, 2),
                "entry_count": item["entry_count"],
            }
            for item in time_by_user
        ]
        
        response_data = {
            "total_seconds": total_seconds,
            "total_hours": round(total_seconds / 3600.0, 2),
            "estimated_time_minutes": issue.estimated_time_minutes,
            "time_by_user": time_by_user_list,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class TimeEntryReportsEndpoint(BaseAPIView):
    """
    Endpoint for time tracking reports/analytics.
    Supports grouping by user, work item, project, or module.
    """
    
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST])
    def get(self, request, slug):
        """
        Get time tracking reports grouped by user, work item, project, or module.
        
        Query parameters:
        - group_by: 'user', 'work_item', 'project', or 'module'
        - from: Start date (YYYY-MM-DD)
        - to: End date (YYYY-MM-DD)
        - project_id: Filter by project (optional)
        - user_id: Filter by user (optional)
        """
        group_by = request.GET.get("group_by", "user")
        from_date = request.GET.get("from")
        to_date = request.GET.get("to")
        project_id = request.GET.get("project_id")
        user_id = request.GET.get("user_id")
        
        # Validate group_by
        valid_group_by = ["user", "work_item", "project", "module"]
        if group_by not in valid_group_by:
            return Response(
                {"error": f"group_by must be one of: {', '.join(valid_group_by)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Build base queryset
        queryset = TimeEntry.objects.filter(
            workspace__slug=slug,
            ended_at__isnull=False,  # Only completed entries
        )
        
        # Apply project filter if provided
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        # Apply user filter if provided
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Apply date range filter
        if from_date:
            try:
                from_date_obj = datetime.strptime(from_date, "%Y-%m-%d").date()
                queryset = queryset.filter(created_at__date__gte=from_date_obj)
            except ValueError:
                return Response(
                    {"error": "Invalid from date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        if to_date:
            try:
                to_date_obj = datetime.strptime(to_date, "%Y-%m-%d").date()
                queryset = queryset.filter(created_at__date__lte=to_date_obj)
            except ValueError:
                return Response(
                    {"error": "Invalid to date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        # Group by user
        if group_by == "user":
            results = (
                queryset.values("user_id", "user__email", "user__display_name")
                .annotate(
                    total_seconds=Sum("duration_seconds"),
                    entry_count=Count("id"),
                )
                .order_by("-total_seconds")
            )
            report_data = [
                {
                    "user_id": str(item["user_id"]),
                    "user_email": item["user__email"],
                    "user_display_name": item["user__display_name"],
                    "total_seconds": item["total_seconds"],
                    "total_hours": round(item["total_seconds"] / 3600.0, 2),
                    "entry_count": item["entry_count"],
                }
                for item in results
            ]
        
        # Group by work item
        elif group_by == "work_item":
            results = (
                queryset.values(
                    "issue_id",
                    "issue__name",
                    "issue__sequence_id",
                    "project_id",
                    "project__identifier",
                    "project__name",
                )
                .annotate(
                    total_seconds=Sum("duration_seconds"),
                    entry_count=Count("id"),
                )
                .order_by("-total_seconds")
            )
            report_data = [
                {
                    "issue_id": str(item["issue_id"]),
                    "issue_name": item["issue__name"],
                    "issue_sequence_id": item["issue__sequence_id"],
                    "project_id": str(item["project_id"]),
                    "project_identifier": item["project__identifier"],
                    "project_name": item["project__name"],
                    "total_seconds": item["total_seconds"],
                    "total_hours": round(item["total_seconds"] / 3600.0, 2),
                    "entry_count": item["entry_count"],
                }
                for item in results
            ]
        
        # Group by project
        elif group_by == "project":
            results = (
                queryset.values("project_id", "project__identifier", "project__name")
                .annotate(
                    total_seconds=Sum("duration_seconds"),
                    entry_count=Count("id"),
                )
                .order_by("-total_seconds")
            )
            report_data = [
                {
                    "project_id": str(item["project_id"]),
                    "project_identifier": item["project__identifier"],
                    "project_name": item["project__name"],
                    "total_seconds": item["total_seconds"],
                    "total_hours": round(item["total_seconds"] / 3600.0, 2),
                    "entry_count": item["entry_count"],
                }
                for item in results
            ]
        
        # Group by module
        elif group_by == "module":
            # Get module information via ModuleIssue
            results = (
                queryset.values(
                    "issue_id",
                    "issue__name",
                    "project_id",
                    "project__identifier",
                )
                .annotate(
                    total_seconds=Sum("duration_seconds"),
                    entry_count=Count("id"),
                )
            )
            
            # Get module info for each issue
            report_data = []
            for item in results:
                module_issue = ModuleIssue.objects.filter(
                    issue_id=item["issue_id"]
                ).select_related("module").first()
                
                module_info = {
                    "module_id": str(module_issue.module_id) if module_issue else None,
                    "module_name": module_issue.module.name if module_issue else None,
                } if module_issue else {"module_id": None, "module_name": None}
                
                report_data.append({
                    "issue_id": str(item["issue_id"]),
                    "issue_name": item["issue__name"],
                    "project_id": str(item["project_id"]),
                    "project_identifier": item["project__identifier"],
                    **module_info,
                    "total_seconds": item["total_seconds"],
                    "total_hours": round(item["total_seconds"] / 3600.0, 2),
                    "entry_count": item["entry_count"],
                })
            
            # Aggregate by module
            module_aggregates = {}
            for item in report_data:
                module_id = item["module_id"]
                if module_id:
                    if module_id not in module_aggregates:
                        module_aggregates[module_id] = {
                            "module_id": module_id,
                            "module_name": item["module_name"],
                            "total_seconds": 0,
                            "entry_count": 0,
                        }
                    module_aggregates[module_id]["total_seconds"] += item["total_seconds"]
                    module_aggregates[module_id]["entry_count"] += item["entry_count"]
            
            report_data = [
                {
                    **agg,
                    "total_hours": round(agg["total_seconds"] / 3600.0, 2),
                }
                for agg in module_aggregates.values()
            ]
            report_data.sort(key=lambda x: x["total_seconds"], reverse=True)
        
        return Response(
            {
                "group_by": group_by,
                "from_date": from_date,
                "to_date": to_date,
                "data": report_data,
            },
            status=status.HTTP_200_OK,
        )


class TimeEntryExportEndpoint(BaseAPIView):
    """
    Endpoint for exporting time entries as CSV.
    """
    
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER])
    def get(self, request, slug):
        """
        Export time entries as CSV.
        
        Query parameters:
        - from: Start date (YYYY-MM-DD)
        - to: End date (YYYY-MM-DD)
        - project_id: Filter by project (optional)
        - user_id: Filter by user (optional)
        """
        from_date = request.GET.get("from")
        to_date = request.GET.get("to")
        project_id = request.GET.get("project_id")
        user_id = request.GET.get("user_id")
        
        # Build queryset
        queryset = TimeEntry.objects.filter(
            workspace__slug=slug,
            ended_at__isnull=False,  # Only completed entries
        ).select_related("user", "issue", "project")
        
        # Apply filters
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        if from_date:
            try:
                from_date_obj = datetime.strptime(from_date, "%Y-%m-%d").date()
                queryset = queryset.filter(created_at__date__gte=from_date_obj)
            except ValueError:
                return Response(
                    {"error": "Invalid from date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        if to_date:
            try:
                to_date_obj = datetime.strptime(to_date, "%Y-%m-%d").date()
                queryset = queryset.filter(created_at__date__lte=to_date_obj)
            except ValueError:
                return Response(
                    {"error": "Invalid to date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Date",
            "User",
            "User Email",
            "Project",
            "Work Item",
            "Work Item Key",
            "Module",
            "Duration (hours)",
            "Duration (seconds)",
            "Source",
            "Billable",
            "Note",
        ])
        
        # Write data
        for entry in queryset.order_by("-created_at"):
            # Get module name if available
            module_issue = ModuleIssue.objects.filter(
                issue_id=entry.issue_id
            ).select_related("module").first()
            module_name = module_issue.module.name if module_issue else ""
            
            writer.writerow([
                entry.created_at.strftime("%Y-%m-%d"),
                entry.user.display_name or entry.user.email,
                entry.user.email,
                entry.project.name,
                entry.issue.name,
                f"{entry.project.identifier}-{entry.issue.sequence_id}",
                module_name,
                round(entry.duration_seconds / 3600.0, 2),
                entry.duration_seconds,
                entry.source,
                "Yes" if entry.is_billable else "No",
                entry.note or "",
            ])
        
        # Create HTTP response
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        filename = f"time_entries_{slug}_{datetime.now().strftime('%Y%m%d')}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        
        return response

