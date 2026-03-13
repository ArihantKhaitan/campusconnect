from django.urls import path

from .views import CertificateGenerateView, CertificateIssueView

app_name = "certificates"

urlpatterns = [
    path("<int:event_id>/download/", CertificateGenerateView.as_view(), name="certificate_download"),
    path("<int:event_id>/issue/<int:student_id>/", CertificateIssueView.as_view(), name="certificate_issue"),
]
