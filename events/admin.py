from django.contrib import admin

from .models import AttendanceRecord, Event, EventCategory, EventRegistration


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "club", "college", "category", "start_datetime", "participant_limit", "status")
    list_filter = ("status", "college", "category")
    search_fields = ("title", "club__name", "college__name", "venue")
    date_hierarchy = "start_datetime"


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ("event", "student", "status", "registered_at")
    list_filter = ("status", "event")
    search_fields = ("event__title", "student__username", "student__first_name", "student__last_name")


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("event", "student", "status", "marked_by", "marked_at")
    list_filter = ("status", "event")
    search_fields = ("event__title", "student__username")
