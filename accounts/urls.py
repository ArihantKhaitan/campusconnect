from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("auth/", views.AuthPageView.as_view(), name="auth"),
    path("login/", views.CampusLoginView.as_view(), name="login"),
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("logout/", views.CampusLogoutView.as_view(), name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/setup/", views.profile_setup, name="profile_setup"),
    path("dashboard/", views.dashboard_redirect, name="dashboard_redirect"),
]
