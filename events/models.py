from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class EventCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "event categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Event(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        CANCELLED = "CANCELLED", "Cancelled"
        COMPLETED = "COMPLETED", "Completed"

    club = models.ForeignKey("organizations.Club", on_delete=models.CASCADE, related_name="events")
    college = models.ForeignKey("organizations.College", on_delete=models.CASCADE, related_name="events")
    category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="events")
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to="events/", blank=True, null=True)
    venue = models.CharField(max_length=255)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    participant_limit = models.PositiveIntegerField()
    registration_deadline = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_datetime", "title"]

    def clean(self):
        if self.end_datetime <= self.start_datetime:
            raise ValidationError("Event end time must be after start time.")
        if self.registration_deadline and self.registration_deadline > self.start_datetime:
            raise ValidationError("Registration deadline must be before the event start time.")
        if self.club_id and self.college_id and self.club.college_id != self.college_id:
            raise ValidationError("Event college must match the club college.")

    @property
    def seats_taken(self):
        return self.registrations.filter(status__in=[EventRegistration.Status.REGISTERED, EventRegistration.Status.ATTENDED]).count()

    @property
    def seats_remaining(self):
        return max(self.participant_limit - self.seats_taken, 0)

    def registration_is_open(self):
        if self.status != self.Status.PUBLISHED:
            return False
        if self.registration_deadline and timezone.now() > self.registration_deadline:
            return False
        return self.seats_remaining > 0

    def __str__(self):
        return self.title


class EventRegistration(models.Model):
    class Status(models.TextChoices):
        REGISTERED = "REGISTERED", "Registered"
        WAITLISTED = "WAITLISTED", "Waitlisted"
        CANCELLED = "CANCELLED", "Cancelled"
        ATTENDED = "ATTENDED", "Attended"
        ABSENT = "ABSENT", "Absent"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="event_registrations")
    registered_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REGISTERED)

    class Meta:
        ordering = ["-registered_at"]
        constraints = [
            models.UniqueConstraint(fields=["event", "student"], name="unique_event_student_registration")
        ]

    def __str__(self):
        return f"{self.student} -> {self.event}"


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="attendance_records")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendance_records")
    registration = models.OneToOneField(EventRegistration, on_delete=models.CASCADE, related_name="attendance_record")
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="marked_attendance_records")
    marked_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=Status.choices)

    class Meta:
        ordering = ["-marked_at"]
        constraints = [
            models.UniqueConstraint(fields=["event", "student"], name="unique_event_student_attendance")
        ]

    def clean(self):
        if self.registration.event_id != self.event_id or self.registration.student_id != self.student_id:
            raise ValidationError("Attendance registration must match the selected event and student.")

    def __str__(self):
        return f"{self.student} - {self.event} - {self.status}"
