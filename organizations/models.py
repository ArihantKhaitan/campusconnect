from django.conf import settings
from django.db import models
from django.utils.text import slugify


class College(models.Model):
    name = models.CharField(max_length=255, unique=True)
    code = models.SlugField(max_length=50, unique=True, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name)[:50]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Department(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["college__name", "name"]
        unique_together = ("college", "name")

    def __str__(self):
        return f"{self.name} ({self.college.code})"


class Club(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name="clubs")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    representative = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="managed_clubs")
    contact_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["college__name", "name"]
        unique_together = ("college", "name")

    def __str__(self):
        return f"{self.name} - {self.college.name}"
