from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import StudentProfile, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (("CampusConnect", {"fields": ("role",)}),)
    list_display = ("username", "email", "first_name", "last_name", "role", "is_staff")
    list_filter = BaseUserAdmin.list_filter + ("role",)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "college", "department", "batch", "roll_no", "registration_no")
    list_filter = ("college", "department", "batch")
    search_fields = ("user__username", "user__first_name", "user__last_name", "registration_no", "roll_no")
