from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from accounts.decorators import club_required, student_required
from certificates.models import Certificate
from .forms import EventForm
from .models import AttendanceRecord, Event, EventCategory, EventRegistration
from organizations.models import Club, College


class EventListView(LoginRequiredMixin, ListView):
    login_url = reverse_lazy("accounts:auth")
    model = Event
    template_name = "events/event_list.html"
    context_object_name = "events"

    def get_queryset(self):
        queryset = Event.objects.select_related("club", "college", "category").annotate(
            registered_count=Count("registrations", filter=Q(registrations__status__in=[EventRegistration.Status.REGISTERED, EventRegistration.Status.ATTENDED]))
        ).all()

        college = self.request.GET.get("college")
        category = self.request.GET.get("category")
        time_filter = self.request.GET.get("time", "upcoming")
        search = self.request.GET.get("q", "").strip()
        date_filter = self.request.GET.get("date")
        now = timezone.now()

        if college:
            queryset = queryset.filter(college_id=college)
        if category:
            queryset = queryset.filter(category_id=category)
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(club__name__icontains=search) | Q(college__name__icontains=search))
        if date_filter:
            queryset = queryset.filter(start_datetime__date=date_filter)
        if time_filter == "past":
            queryset = queryset.filter(end_datetime__lt=now)
        elif time_filter == "upcoming":
            queryset = queryset.filter(end_datetime__gte=now)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "colleges": College.objects.all(),
                "categories": EventCategory.objects.all(),
                "selected_college": self.request.GET.get("college", ""),
                "selected_category": self.request.GET.get("category", ""),
                "selected_time": self.request.GET.get("time", "upcoming"),
                "search_query": self.request.GET.get("q", ""),
                "selected_date": self.request.GET.get("date", ""),
                "now": timezone.now(),
            }
        )
        return context


class EventDetailView(LoginRequiredMixin, DetailView):
    login_url = reverse_lazy("accounts:auth")
    model = Event
    template_name = "events/event_detail.html"
    context_object_name = "event"

    def get_queryset(self):
        return Event.objects.select_related("club", "college", "category", "created_by").annotate(
            registered_count=Count("registrations", filter=Q(registrations__status__in=[EventRegistration.Status.REGISTERED, EventRegistration.Status.ATTENDED]))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        registration = None
        if user.is_authenticated and getattr(user, "role", None) == "STUDENT":
            registration = EventRegistration.objects.filter(event=self.object, student=user).first()

        context.update(
            {
                "can_manage": bool(
                    user.is_authenticated
                    and user.role == "CLUB"
                    and self.object.club.representative_id == user.id
                ),
                "student_registration": registration,
                "is_full": self.object.seats_remaining <= 0,
                "registration_open": self.object.registration_is_open(),
            }
        )
        return context


@method_decorator(club_required, name="dispatch")
class ClubOwnedEventMixin(LoginRequiredMixin):
    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"

    def get_user_club(self):
        club = Club.objects.filter(representative=self.request.user).select_related("college").first()
        if not club:
            raise PermissionDenied("No club is assigned to this account.")
        return club

    def get_queryset(self):
        return Event.objects.filter(club__representative=self.request.user).select_related("club", "college", "category")

    def form_valid(self, form):
        club = self.get_user_club()
        form.instance.club = club
        form.instance.college = club.college
        if not form.instance.created_by_id:
            form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method in ("POST", "PUT"):
            kwargs["files"] = self.request.FILES
        return kwargs


class EventCreateView(ClubOwnedEventMixin, CreateView):
    success_url = reverse_lazy("core:club_dashboard")


class EventUpdateView(ClubOwnedEventMixin, UpdateView):
    success_url = reverse_lazy("core:club_dashboard")


@method_decorator(club_required, name="dispatch")
class EventDeleteView(LoginRequiredMixin, DeleteView):
    model = Event
    template_name = "events/event_confirm_delete.html"
    success_url = reverse_lazy("core:club_dashboard")

    def get_queryset(self):
        return Event.objects.filter(club__representative=self.request.user)


@method_decorator(student_required, name="dispatch")
class EventRegisterView(LoginRequiredMixin, View):
    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        existing = EventRegistration.objects.filter(event=event, student=request.user).first()

        if existing and existing.status != EventRegistration.Status.CANCELLED:
            messages.error(request, "You are already registered for this event.")
            return redirect("events:event_detail", pk=event.pk)

        if event.registration_deadline and timezone.now() > event.registration_deadline:
            messages.error(request, "Registration is closed for this event.")
            return redirect("events:event_detail", pk=event.pk)

        if event.status != Event.Status.PUBLISHED:
            messages.error(request, "This event is not open for registration.")
            return redirect("events:event_detail", pk=event.pk)

        if event.seats_remaining <= 0:
            messages.error(request, "This event is full.")
            return redirect("events:event_detail", pk=event.pk)

        if existing and existing.status == EventRegistration.Status.CANCELLED:
            existing.status = EventRegistration.Status.REGISTERED
            existing.registered_at = timezone.now()
            existing.save(update_fields=["status", "registered_at"])
        else:
            EventRegistration.objects.create(
                event=event,
                student=request.user,
                status=EventRegistration.Status.REGISTERED,
            )

        messages.success(request, "You have been registered for this event.")
        return redirect("events:event_detail", pk=event.pk)


@method_decorator(student_required, name="dispatch")
class EventCancelRegistrationView(LoginRequiredMixin, View):
    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        registration = EventRegistration.objects.filter(event=event, student=request.user).first()

        if not registration or registration.status == EventRegistration.Status.CANCELLED:
            messages.error(request, "You do not have an active registration for this event.")
            return redirect("events:event_detail", pk=event.pk)

        registration.status = EventRegistration.Status.CANCELLED
        registration.save(update_fields=["status"])
        messages.success(request, "Your registration has been canceled.")
        return redirect("events:event_detail", pk=event.pk)


@method_decorator(club_required, name="dispatch")
class EventParticipantsView(LoginRequiredMixin, TemplateView):
    template_name = "events/event_participants.html"

    def get_event(self):
        return get_object_or_404(
            Event.objects.select_related("club", "college", "category"),
            pk=self.kwargs["pk"],
            club__representative=self.request.user,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_event()
        registrations = (
            EventRegistration.objects.filter(
                event=event,
                status__in=[
                    EventRegistration.Status.REGISTERED,
                    EventRegistration.Status.ATTENDED,
                    EventRegistration.Status.ABSENT,
                ],
            )
            .select_related("student", "student__student_profile", "student__student_profile__college", "student__student_profile__department")
            .prefetch_related("attendance_record")
            .order_by("student__first_name", "student__username")
        )
        issued_student_ids = set(Certificate.objects.filter(event=event, is_issued=True).values_list("student_id", flat=True))
        context.update({"event": event, "registrations": registrations, "issued_student_ids": issued_student_ids})
        return context


class EventCalendarView(LoginRequiredMixin, TemplateView):
    template_name = "events/event_calendar.html"
    login_url = reverse_lazy("accounts:auth")


class EventCalendarFeedView(LoginRequiredMixin, View):
    login_url = reverse_lazy("accounts:auth")

    def get(self, request):
        now = timezone.now()
        events = Event.objects.select_related("club", "college").annotate(
            registered_count=Count(
                "registrations",
                filter=Q(registrations__status__in=[
                    EventRegistration.Status.REGISTERED,
                    EventRegistration.Status.ATTENDED,
                ]),
            )
        ).all()

        result = []
        for event in events:
            seats_remaining = max(event.participant_limit - event.registered_count, 0)
            if event.end_datetime < now:
                color = "#94a3b8"  # gray — past
                text_color = "#ffffff"
            elif seats_remaining <= 0:
                color = "#f97316"  # orange — full
                text_color = "#ffffff"
            else:
                color = "#3b82f6"  # blue — upcoming
                text_color = "#ffffff"

            result.append({
                "id": event.id,
                "title": event.title,
                "start": event.start_datetime.isoformat(),
                "end": event.end_datetime.isoformat(),
                "url": reverse_lazy("events:event_detail", kwargs={"pk": event.pk}),
                "color": color,
                "textColor": text_color,
            })

        return JsonResponse(result, safe=False)


class EventAttendanceUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk, club__representative=request.user)
        registration = get_object_or_404(
            EventRegistration,
            event=event,
            student_id=request.POST.get("student_id"),
            status__in=[
                EventRegistration.Status.REGISTERED,
                EventRegistration.Status.ATTENDED,
                EventRegistration.Status.ABSENT,
            ],
        )

        status = request.POST.get("status")
        if status not in [AttendanceRecord.Status.PRESENT, AttendanceRecord.Status.ABSENT]:
            messages.error(request, "Invalid attendance status.")
            return redirect("events:event_participants", pk=event.pk)

        attendance, created = AttendanceRecord.objects.update_or_create(
            event=event,
            student=registration.student,
            defaults={
                "registration": registration,
                "marked_by": request.user,
                "marked_at": timezone.now(),
                "status": status,
            },
        )

        registration.status = (
            EventRegistration.Status.ATTENDED
            if status == AttendanceRecord.Status.PRESENT
            else EventRegistration.Status.ABSENT
        )
        registration.save(update_fields=["status"])

        messages.success(
            request,
            f"Attendance marked as {attendance.get_status_display()} for {registration.student}.",
        )
        return redirect("events:event_participants", pk=event.pk)
