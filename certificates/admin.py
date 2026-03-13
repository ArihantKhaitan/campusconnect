from django.contrib import admin

from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("certificate_number", "event", "student", "is_issued", "generated_at")
    list_filter = ("is_issued", "event")
    search_fields = ("certificate_number", "event__title", "student__username")
