from io import BytesIO

from django.contrib import messages
from django.core.files.base import ContentFile
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views import View
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from accounts.decorators import club_required, student_required
from events.models import AttendanceRecord, Event, EventRegistration

from .models import Certificate


class CertificateBuilderMixin:
    def get_certificate_number(self, event, student):
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
        return f"CC-{event.id}-{student.id}-{timestamp}"

    def issue_certificate(self, event, student):
        attendance = AttendanceRecord.objects.filter(
            event=event,
            student=student,
            status=AttendanceRecord.Status.PRESENT,
        ).first()
        registration = EventRegistration.objects.filter(
            event=event,
            student=student,
            status=EventRegistration.Status.ATTENDED,
        ).first()

        if not attendance or not registration:
            raise Http404("Certificate is not available for this event.")

        certificate = Certificate.objects.filter(event=event, student=student).first()
        if certificate and certificate.file:
            return certificate

        if not certificate:
            certificate = Certificate.objects.create(
                event=event,
                student=student,
                certificate_number=self.get_certificate_number(event, student),
                is_issued=True,
            )
        else:
            certificate.is_issued = True
            if not certificate.certificate_number:
                certificate.certificate_number = self.get_certificate_number(event, student)
            certificate.save(update_fields=["is_issued", "certificate_number"])

        pdf_bytes = self.build_pdf(certificate)
        filename = f"certificate-{slugify(event.title)}-{student.id}.pdf"
        certificate.file.save(filename, ContentFile(pdf_bytes.getvalue()), save=True)
        return certificate

    def build_pdf(self, certificate):
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        event = certificate.event
        student = certificate.student
        issue_date = timezone.localdate(certificate.generated_at if certificate.generated_at else timezone.now())
        event_date = timezone.localtime(event.start_datetime).strftime("%d %B %Y")
        profile = getattr(student, "student_profile", None)

        pdf.setTitle("CampusConnect Participation Certificate")
        pdf.setFont("Helvetica-Bold", 22)
        pdf.drawCentredString(width / 2, height - 1.5 * inch, "CampusConnect Participation Certificate")

        if getattr(student, "profile_picture", None):
            try:
                pdf.drawImage(ImageReader(student.profile_picture), width - 2.1 * inch, height - 3.0 * inch, width=1.1 * inch, height=1.1 * inch, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass

        pdf.setFont("Helvetica", 14)
        pdf.drawCentredString(width / 2, height - 2.4 * inch, "This certifies that")

        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawCentredString(width / 2, height - 3.1 * inch, student.get_full_name() or student.username)

        details_y = height - 3.7 * inch
        pdf.setFont("Helvetica", 12)
        pdf.drawCentredString(width / 2, details_y, f"College: {getattr(getattr(profile, 'college', None), 'name', 'N/A')}")
        pdf.drawCentredString(width / 2, details_y - 0.28 * inch, f"Department: {getattr(getattr(profile, 'department', None), 'name', 'N/A')}")
        pdf.drawCentredString(width / 2, details_y - 0.56 * inch, f"Registration No: {getattr(profile, 'registration_no', '') or 'N/A'}")

        pdf.setFont("Helvetica", 14)
        body = (
            f"successfully participated in the event {event.title} organized by "
            f"{event.club.name} on {event_date}."
        )
        text = pdf.beginText(1.0 * inch, height - 5.0 * inch)
        text.setFont("Helvetica", 14)
        for line in ["", body]:
            text.textLine(line)
        pdf.drawText(text)

        pdf.setFont("Helvetica", 12)
        pdf.drawString(1.0 * inch, 1.9 * inch, f"Event: {event.title}")
        pdf.drawString(1.0 * inch, 1.6 * inch, f"Club: {event.club.name}")
        pdf.drawString(1.0 * inch, 1.3 * inch, f"Certificate ID: {certificate.certificate_number}")
        pdf.drawString(1.0 * inch, 1.0 * inch, f"Issue Date: {issue_date.strftime('%d %B %Y')}")
        pdf.save()
        buffer.seek(0)
        return buffer



@method_decorator(student_required, name="dispatch")
class CertificateGenerateView(CertificateBuilderMixin, View):
    def get(self, request, event_id):
        event = get_object_or_404(Event.objects.select_related("club", "college"), pk=event_id)
        certificate = get_object_or_404(Certificate, event=event, student=request.user, is_issued=True)
        if not certificate.file:
            certificate = self.issue_certificate(event, request.user)
        return FileResponse(certificate.file.open("rb"), as_attachment=False, filename=certificate.file.name.rsplit('/', 1)[-1])


@method_decorator(club_required, name="dispatch")
class CertificateIssueView(CertificateBuilderMixin, View):
    def post(self, request, event_id, student_id):
        event = get_object_or_404(Event.objects.select_related("club", "college"), pk=event_id, club__representative=request.user)
        registration = get_object_or_404(
            EventRegistration.objects.select_related("student", "student__student_profile", "student__student_profile__college", "student__student_profile__department"),
            event=event,
            student_id=student_id,
        )
        if registration.status != EventRegistration.Status.ATTENDED:
            messages.error(request, "Certificate can only be generated for attended students.")
            return redirect("events:event_participants", pk=event.pk)

        self.issue_certificate(event, registration.student)
        messages.success(request, f"Certificate generated for {registration.student.get_full_name() or registration.student.username}.")
        return redirect("events:event_participants", pk=event.pk)
