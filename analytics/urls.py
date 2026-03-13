from django.urls import path

from .views import admin_analytics_dashboard, club_analytics_dashboard

app_name = "analytics"

urlpatterns = [
    path("admin/", admin_analytics_dashboard, name="admin_dashboard"),
    path("club/", club_analytics_dashboard, name="club_dashboard"),
]
