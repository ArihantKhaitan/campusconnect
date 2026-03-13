from django.contrib import admin

from .models import AnalyticsSnapshot


@admin.register(AnalyticsSnapshot)
class AnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = ("metric_name", "metric_date", "created_at")
    list_filter = ("metric_name", "metric_date")
    search_fields = ("metric_name",)
