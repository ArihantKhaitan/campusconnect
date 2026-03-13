from django.contrib import admin

from .models import Club, College, Department


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "created_at")
    search_fields = ("name", "code")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "college", "code")
    list_filter = ("college",)
    search_fields = ("name", "code", "college__name")


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("name", "college", "representative", "contact_email", "created_at")
    list_filter = ("college",)
    search_fields = ("name", "college__name", "representative__username")
