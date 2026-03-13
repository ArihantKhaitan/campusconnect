from django.urls import path

from .views import (
    EventAttendanceUpdateView,
    EventCalendarFeedView,
    EventCalendarView,
    EventCancelRegistrationView,
    EventCreateView,
    EventDeleteView,
    EventDetailView,
    EventListView,
    EventParticipantsView,
    EventRegisterView,
    EventUpdateView,
)

app_name = "events"

urlpatterns = [
    path("", EventListView.as_view(), name="event_list"),
    path("calendar/", EventCalendarView.as_view(), name="event_calendar"),
    path("calendar/feed/", EventCalendarFeedView.as_view(), name="event_calendar_feed"),
    path("create/", EventCreateView.as_view(), name="event_create"),
    path("<int:pk>/", EventDetailView.as_view(), name="event_detail"),
    path("<int:pk>/edit/", EventUpdateView.as_view(), name="event_update"),
    path("<int:pk>/delete/", EventDeleteView.as_view(), name="event_delete"),
    path("<int:pk>/register/", EventRegisterView.as_view(), name="event_register"),
    path("<int:pk>/cancel/", EventCancelRegistrationView.as_view(), name="event_cancel"),
    path("<int:pk>/participants/", EventParticipantsView.as_view(), name="event_participants"),
    path("<int:pk>/attendance/", EventAttendanceUpdateView.as_view(), name="event_attendance_update"),
]
