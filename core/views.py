from itertools import chain

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.decorators import admin_required, club_required, student_required
from accounts.models import User
from certificates.models import Certificate
from events.models import Event, EventRegistration
from organizations.models import Club, College


def home(request):
    if not request.user.is_authenticated:
        return redirect("accounts:auth")
    return redirect("accounts:dashboard_redirect")


@admin_required
def admin_dashboard(request):
    context = {
        "total_users": User.objects.count(),
        "total_events": Event.objects.count(),
        "total_students": User.objects.filter(role=User.Roles.STUDENT).count(),
        "total_registrations": EventRegistration.objects.count(),
        "total_colleges": College.objects.count(),
        "total_clubs": Club.objects.count(),
        "total_certificates": Certificate.objects.filter(is_issued=True).count(),
        "recent_events": Event.objects.select_related("club", "college").order_by("-created_at")[:8],
        "recent_certificates": Certificate.objects.select_related("student", "event").order_by("-generated_at")[:8],
    }
    return render(request, "dashboards/admin_dashboard.html", context)


@club_required
def club_dashboard(request):
    club = request.user.managed_clubs.first()
    managed_events = club.events.annotate(
        registered_count=Count("registrations", filter=Q(registrations__status__in=[EventRegistration.Status.REGISTERED, EventRegistration.Status.ATTENDED]))
    ) if club else Event.objects.none()
    registrations_count = EventRegistration.objects.filter(event__club=club).count() if club else 0
    attendance_count = EventRegistration.objects.filter(event__club=club, status=EventRegistration.Status.ATTENDED).count() if club else 0
    return render(
        request,
        "dashboards/club_dashboard.html",
        {
            "managed_events": managed_events,
            "total_events": managed_events.count() if club else 0,
            "registrations_count": registrations_count,
            "attendance_count": attendance_count,
        },
    )


@admin_required
def admin_users(request):
    users = User.objects.order_by("username")
    return render(request, "dashboards/admin_users.html", {"users": users})


@admin_required
def admin_events(request):
    events = Event.objects.select_related("club", "college", "created_by").order_by("-start_datetime")
    return render(request, "dashboards/admin_events.html", {"events": events})


@admin_required
def admin_certificates(request):
    certificates = Certificate.objects.select_related("student", "event", "event__club").order_by("-generated_at")
    return render(request, "dashboards/admin_certificates.html", {"certificates": certificates})


@student_required
def student_dashboard(request):
    registrations = EventRegistration.objects.filter(student=request.user).select_related("event", "event__club", "event__college")
    now = timezone.now()
    upcoming_registrations = registrations.filter(
        status=EventRegistration.Status.REGISTERED,
        event__end_datetime__gte=now,
    ).order_by("event__start_datetime")
    certificates = Certificate.objects.filter(student=request.user, is_issued=True).select_related("event").order_by("-generated_at")
    attendance_records = request.user.attendance_records.select_related("event").order_by("-marked_at")
    timeline_items = sorted(
        chain(
            [{"type": "registration", "title": f"Registered for {reg.event.title}", "timestamp": reg.registered_at} for reg in registrations],
            [{"type": "attendance", "title": f"Attendance marked {record.get_status_display()} for {record.event.title}", "timestamp": record.marked_at} for record in attendance_records],
            [{"type": "certificate", "title": f"Certificate generated for {cert.event.title}", "timestamp": cert.generated_at} for cert in certificates],
        ),
        key=lambda item: item["timestamp"],
        reverse=True,
    )[:12]
    context = {
        "upcoming_registrations": upcoming_registrations,
        "past_attended_registrations": registrations.filter(
            status=EventRegistration.Status.ATTENDED,
        ).order_by("-event__start_datetime"),
        "registration_history": registrations.order_by("-registered_at"),
        "certificates": certificates,
        "upcoming_events_count": upcoming_registrations.count(),
        "registration_count": registrations.exclude(status=EventRegistration.Status.CANCELLED).count(),
        "certificate_count": certificates.count(),
        "timeline_items": timeline_items,
    }
    return render(request, "dashboards/student_dashboard.html", context)
