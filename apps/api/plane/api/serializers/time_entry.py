# Django imports
from django.utils import timezone
from rest_framework import serializers

# Module imports
from plane.db.models import TimeEntry, TimeEntrySource, Issue, User
from .base import BaseSerializer
from .user import UserLiteSerializer
from .issue import IssueLiteSerializer


class TimeEntrySerializer(BaseSerializer):
    """
    Serializer for time tracking entries.
    
    Handles both timer-based and manual time entries with validation
    and automatic duration computation.
    """
    
    user_detail = UserLiteSerializer(source="user", read_only=True)
    issue_detail = IssueLiteSerializer(source="issue", read_only=True)
    duration_hours = serializers.FloatField(read_only=True)
    duration_minutes = serializers.FloatField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = TimeEntry
        fields = [
            "id",
            "workspace",
            "project",
            "issue",
            "issue_detail",
            "user",
            "user_detail",
            "started_at",
            "ended_at",
            "duration_seconds",
            "duration_hours",
            "duration_minutes",
            "source",
            "note",
            "is_billable",
            "is_active",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = [
            "id",
            "workspace",
            "project",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "duration_hours",
            "duration_minutes",
            "is_active",
        ]

    def validate(self, data):
        """
        Validate time entry data based on source type.
        """
        source = data.get("source", TimeEntrySource.MANUAL)
        started_at = data.get("started_at")
        ended_at = data.get("ended_at")
        duration_seconds = data.get("duration_seconds", 0)
        
        # For manual entries, duration_seconds is required
        if source == TimeEntrySource.MANUAL:
            if not duration_seconds or duration_seconds <= 0:
                raise serializers.ValidationError(
                    {"duration_seconds": "Duration in seconds is required for manual entries"}
                )
        
        # For timer entries, started_at is required
        if source == TimeEntrySource.TIMER:
            if not started_at:
                raise serializers.ValidationError(
                    {"started_at": "Started at is required for timer entries"}
                )
        
        # Validate date range
        if started_at and ended_at:
            if started_at > ended_at:
                raise serializers.ValidationError(
                    "Started at cannot be after ended at"
                )
            
            # Auto-compute duration if not provided
            if duration_seconds == 0:
                delta = ended_at - started_at
                data["duration_seconds"] = max(0, int(delta.total_seconds()))
        
        return data

    def to_representation(self, instance):
        """
        Compute derived fields: duration_hours, duration_minutes, and is_active.
        """
        representation = super().to_representation(instance)
        
        # Compute duration in hours and minutes
        duration_seconds = instance.duration_seconds or 0
        representation["duration_hours"] = round(duration_seconds / 3600.0, 2)
        representation["duration_minutes"] = round(duration_seconds / 60.0, 2)
        
        # Compute is_active: timer is active if started_at exists but ended_at is None
        representation["is_active"] = (
            instance.started_at is not None and 
            instance.ended_at is None and 
            instance.source == TimeEntrySource.TIMER
        )
        
        return representation
    
    def create(self, validated_data):
        """
        Create a time entry, ensuring workspace and project are set from issue.
        """
        issue = validated_data.get("issue")
        if issue:
            validated_data["workspace"] = issue.workspace
            validated_data["project"] = issue.project
        
        # Set user from request if not provided
        if "user" not in validated_data:
            validated_data["user"] = self.context["request"].user
        
        return super().create(validated_data)


class TimeEntryCreateSerializer(serializers.Serializer):
    """
    Simplified serializer for creating time entries.
    """
    issue_id = serializers.UUIDField(required=True)
    duration_seconds = serializers.IntegerField(required=False, min_value=0)
    started_at = serializers.DateTimeField(required=False, allow_null=True)
    ended_at = serializers.DateTimeField(required=False, allow_null=True)
    source = serializers.ChoiceField(
        choices=TimeEntrySource.choices,
        default=TimeEntrySource.MANUAL,
        required=False,
    )
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_billable = serializers.BooleanField(default=False, required=False)

    def validate(self, data):
        source = data.get("source", TimeEntrySource.MANUAL)
        
        if source == TimeEntrySource.MANUAL:
            if not data.get("duration_seconds"):
                raise serializers.ValidationError(
                    "duration_seconds is required for manual entries"
                )
        elif source == TimeEntrySource.TIMER:
            if not data.get("started_at"):
                data["started_at"] = timezone.now()
        
        return data


class TimeEntryUpdateSerializer(BaseSerializer):
    """
    Serializer for updating time entries.
    """
    
    class Meta:
        model = TimeEntry
        fields = [
            "duration_seconds",
            "started_at",
            "ended_at",
            "note",
            "is_billable",
        ]
    
    def validate(self, data):
        """
        Validate updated time entry data.
        """
        started_at = data.get("started_at") or self.instance.started_at
        ended_at = data.get("ended_at") or self.instance.ended_at
        duration_seconds = data.get("duration_seconds")
        
        # If both dates are present, validate and auto-compute duration
        if started_at and ended_at:
            if started_at > ended_at:
                raise serializers.ValidationError(
                    "Started at cannot be after ended at"
                )
            
            if duration_seconds is None or duration_seconds == 0:
                delta = ended_at - started_at
                data["duration_seconds"] = max(0, int(delta.total_seconds()))
        
        return data

