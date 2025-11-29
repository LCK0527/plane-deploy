# Generated migration for Time Tracking feature

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0107_migrate_filters_to_rich_filters'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='estimated_time_minutes',
            field=models.PositiveIntegerField(blank=True, help_text='Estimated time budget for this work item in minutes', null=True, verbose_name='Estimated Time (minutes)'),
        ),
        migrations.CreateModel(
            name='TimeEntry',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Last Modified At')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Deleted At')),
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('started_at', models.DateTimeField(blank=True, help_text='When the timer started (for timer entries) or when work began (for manual entries)', null=True, verbose_name='Started At')),
                ('ended_at', models.DateTimeField(blank=True, help_text='When the timer stopped (for timer entries) or when work ended (for manual entries)', null=True, verbose_name='Ended At')),
                ('duration_seconds', models.PositiveIntegerField(default=0, help_text='Total duration in seconds. For timer entries, computed when stopped.', verbose_name='Duration (seconds)')),
                ('source', models.CharField(choices=[('timer', 'Timer'), ('manual', 'Manual')], default='manual', help_text='Whether this entry was created via timer or manual input', max_length=20, verbose_name='Source')),
                ('note', models.TextField(blank=True, help_text='Optional note about what was worked on', null=True, verbose_name='Note')),
                ('is_billable', models.BooleanField(default=False, help_text='Whether this time entry is billable', verbose_name='Billable')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('issue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='time_entries', to='db.issue', verbose_name='Work Item')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_%(class)s', to='db.project')),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='Last Modified By')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='time_entries', to=settings.AUTH_USER_MODEL, verbose_name='User')),
                ('workspace', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workspace_%(class)s', to='db.workspace')),
            ],
            options={
                'verbose_name': 'Time Entry',
                'verbose_name_plural': 'Time Entries',
                'db_table': 'time_entries',
                'ordering': ('-created_at',),
            },
        ),
        migrations.AddIndex(
            model_name='timeentry',
            index=models.Index(fields=['issue', 'user'], name='time_entry_issue_user_idx'),
        ),
        migrations.AddIndex(
            model_name='timeentry',
            index=models.Index(fields=['started_at'], name='time_entry_started_at_idx'),
        ),
        migrations.AddIndex(
            model_name='timeentry',
            index=models.Index(fields=['created_at'], name='time_entry_created_at_idx'),
        ),
    ]

