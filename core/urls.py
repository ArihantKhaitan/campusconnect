from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/club/", views.club_dashboard, name="club_dashboard"),
    path("dashboard/student/", views.student_dashboard, name="student_dashboard"),
    path("admin/users/", views.admin_users, name="admin_users"),
    path("admin/events/", views.admin_events, name="admin_events"),
    path("admin/certificates/", views.admin_certificates, name="admin_certificates"),
]
