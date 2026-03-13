import json
from collections import OrderedDict

from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import admin_required, club_required
from events.models import AttendanceRecord, Event, EventRegistration


@admin_required
def admin_analytics_dashboard(request):
    top_events = list(
        Event.objects.annotate(registration_count=Count("registrations"))
        .select_related("club", "college")
        .order_by("-registration_count", "title")[:5]
    )

    department_distribution = list(
        EventRegistration.objects.filter(status__in=[
            EventRegistration.Status.REGISTERED,
            EventRegistration.Status.ATTENDED,
            EventRegistration.Status.ABSENT,
        ])
        .values("student__student_profile__department__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    college_engagement = list(
        EventRegistration.objects.filter(status__in=[
            EventRegistration.Status.REGISTERED,
            EventRegistration.Status.ATTENDED,
            EventRegistration.Status.ABSENT,
        ])
        .values("event__college__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    monthly_trend_qs = (
        EventRegistration.objects.filter(status__in=[
            EventRegistration.Status.REGISTERED,
            EventRegistration.Status.ATTENDED,
            EventRegistration.Status.ABSENT,
        ])
        .order_by("registered_at")
    )
    month_buckets = OrderedDict()
    for reg in monthly_trend_qs:
        label = timezone.localtime(reg.registered_at).strftime("%Y-%m")
        month_buckets[label] = month_buckets.get(label, 0) + 1

    registration_vs_attendance = list(
        Event.objects.annotate(
            registration_count=Count("registrations", filter=Q(registrations__status__in=[
                EventRegistration.Status.REGISTERED,
                EventRegistration.Status.ATTENDED,
                EventRegistration.Status.ABSENT,
            ])),
            attendance_count=Count("attendance_records", filter=Q(attendance_records__status=AttendanceRecord.Status.PRESENT)),
        )
        .order_by("title")[:10]
    )

    context = {
        "top_events": top_events,
        "top_events_labels": json.dumps([event.title for event in top_events]),
        "top_events_values": json.dumps([event.registration_count for event in top_events]),
        "department_labels": json.dumps([item["student__student_profile__department__name"] or "Unknown" for item in department_distribution]),
        "department_values": json.dumps([item["total"] for item in department_distribution]),
        "college_labels": json.dumps([item["event__college__name"] or "Unknown" for item in college_engagement]),
        "college_values": json.dumps([item["total"] for item in college_engagement]),
        "trend_labels": json.dumps(list(month_buckets.keys())),
        "trend_values": json.dumps(list(month_buckets.values())),
        "comparison_labels": json.dumps([event.title for event in registration_vs_attendance]),
        "comparison_registration_values": json.dumps([event.registration_count for event in registration_vs_attendance]),
        "comparison_attendance_values": json.dumps([event.attendance_count for event in registration_vs_attendance]),
    }
    return render(request, "analytics/admin_dashboard.html", context)


@club_required
def club_analytics_dashboard(request):
    club = request.user.managed_clubs.first()
    events = list(
        Event.objects.filter(club=club)
        .annotate(
            registration_count=Count("registrations", filter=Q(registrations__status__in=[
                EventRegistration.Status.REGISTERED,
                EventRegistration.Status.ATTENDED,
                EventRegistration.Status.ABSENT,
            ])),
            attendance_count=Count("attendance_records", filter=Q(attendance_records__status=AttendanceRecord.Status.PRESENT)),
        )
        .order_by("start_datetime", "title")
    )

    context = {
        "club": club,
        "events": events,
        "event_labels": json.dumps([event.title for event in events]),
        "registration_values": json.dumps([event.registration_count for event in events]),
        "attendance_values": json.dumps([event.attendance_count for event in events]),
        "trend_labels": json.dumps([timezone.localtime(event.start_datetime).strftime("%Y-%m-%d") for event in events]),
        "trend_values": json.dumps([event.registration_count for event in events]),
    }
    return render(request, "analytics/club_dashboard.html", context)
