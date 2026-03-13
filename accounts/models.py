from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        CLUB = "CLUB", "Club Representative"
        STUDENT = "STUDENT", "Student"

    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.STUDENT)
    profile_picture = models.ImageField(upload_to="profile_pics/", blank=True, null=True)

    def __str__(self):
        return self.get_full_name() or self.username


class StudentProfile(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="student_profile")
    college = models.ForeignKey("organizations.College", on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    department = models.ForeignKey("organizations.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    batch = models.CharField(max_length=20, blank=True)
    roll_no = models.CharField(max_length=50, blank=True)
    registration_no = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return f"Student Profile: {self.user}"
