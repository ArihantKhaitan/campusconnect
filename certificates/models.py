from django.conf import settings
from django.db import models


class Certificate(models.Model):
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE, related_name="certificates")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates")
    certificate_number = models.CharField(max_length=100, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to="certificates/", blank=True)
    is_issued = models.BooleanField(default=False)

    class Meta:
        ordering = ["-generated_at"]
        constraints = [
            models.UniqueConstraint(fields=["event", "student"], name="unique_event_student_certificate")
        ]

    def __str__(self):
        return f"{self.certificate_number}"
