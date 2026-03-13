from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import StudentProfile, User
from organizations.models import Club, College, Department


class Command(BaseCommand):
    help = "Clear all users/events and create a full demo dataset for testing"

    def handle(self, *args, **kwargs):
        self.stdout.write("Clearing existing data...")
        # Import here to avoid circular imports at module level
        from certificates.models import Certificate
        from events.models import AttendanceRecord, Event, EventCategory, EventRegistration

        Certificate.objects.all().delete()
        AttendanceRecord.objects.all().delete()
        EventRegistration.objects.all().delete()
        Event.objects.all().delete()
        EventCategory.objects.all().delete()
        User.objects.all().delete()

        self.stdout.write("Setting up college, departments, and club...")
        college, _ = College.objects.get_or_create(name="Demo University")
        dept_cs, _ = Department.objects.get_or_create(college=college, name="Computer Science", defaults={"code": "CS"})
        dept_ec, _ = Department.objects.get_or_create(college=college, name="Electronics", defaults={"code": "EC"})
        club, _ = Club.objects.get_or_create(
            name="Tech Club",
            college=college,
            defaults={"description": "The official technology and innovation club."},
        )

        # ── Categories ──────────────────────────────────────────────────────
        cat_tech, _ = EventCategory.objects.get_or_create(name="Technology")
        cat_workshop, _ = EventCategory.objects.get_or_create(name="Workshop")
        cat_competition, _ = EventCategory.objects.get_or_create(name="Competition")
        cat_cultural, _ = EventCategory.objects.get_or_create(name="Cultural")

        # ── Users ────────────────────────────────────────────────────────────
        self.stdout.write("Creating users...")
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@campusconnect.demo",
            password="Admin@1234",
            first_name="Admin",
            last_name="User",
            role=User.Roles.ADMIN,
        )

        club_user = User.objects.create_user(
            username="clubrep",
            email="clubrep@campusconnect.demo",
            password="Club@1234",
            first_name="Alex",
            last_name="Rivera",
            role=User.Roles.CLUB,
        )
        club.representative = club_user
        club.save(update_fields=["representative"])

        student = User.objects.create_user(
            username="student",
            email="student@campusconnect.demo",
            password="Student@1234",
            first_name="Jordan",
            last_name="Smith",
            role=User.Roles.STUDENT,
        )
        StudentProfile.objects.create(
            user=student,
            college=college,
            department=dept_cs,
            batch="2024",
            roll_no="CS001",
            registration_no="2024CS001",
        )

        # ── Events ───────────────────────────────────────────────────────────
        self.stdout.write("Creating events...")
        now = timezone.now()

        # 1. Past completed event — student attended, certificate will be issued
        event_past_1 = Event.objects.create(
            club=club, college=college, category=cat_tech,
            title="Tech Summit 2024",
            description="An annual technology summit featuring talks on AI, cloud computing, and open source. Students got hands-on experience with cutting-edge tools and networked with industry professionals.",
            venue="Main Auditorium, Block A",
            start_datetime=now - timedelta(days=30),
            end_datetime=now - timedelta(days=30) + timedelta(hours=6),
            participant_limit=100,
            registration_deadline=now - timedelta(days=33),
            status=Event.Status.COMPLETED,
            created_by=club_user,
        )

        # 2. Past completed event — student attended, no certificate yet
        event_past_2 = Event.objects.create(
            club=club, college=college, category=cat_workshop,
            title="Python & Django Workshop",
            description="A full-day hands-on workshop covering Python fundamentals, Django web framework, REST APIs, and deployment. Participants built a mini project by the end of the day.",
            venue="CS Lab 3, Block B",
            start_datetime=now - timedelta(days=10),
            end_datetime=now - timedelta(days=10) + timedelta(hours=8),
            participant_limit=40,
            registration_deadline=now - timedelta(days=13),
            status=Event.Status.COMPLETED,
            created_by=club_user,
        )

        # 3. Upcoming event — student registered
        event_upcoming_1 = Event.objects.create(
            club=club, college=college, category=cat_competition,
            title="Hackathon 2025",
            description="A 24-hour hackathon open to all students. Build something innovative using any technology stack. Prizes include internship opportunities and cash awards. Teams of 2-4.",
            venue="Innovation Hub, Block C",
            start_datetime=now + timedelta(days=14),
            end_datetime=now + timedelta(days=15),
            participant_limit=80,
            registration_deadline=now + timedelta(days=10),
            status=Event.Status.PUBLISHED,
            created_by=club_user,
        )

        # 4. Upcoming event — open for registration
        event_upcoming_2 = Event.objects.create(
            club=club, college=college, category=cat_cultural,
            title="Annual Tech Fest",
            description="The biggest tech and cultural festival on campus. Features robotics competitions, coding contests, design showcases, and live performances. Open to all departments.",
            venue="Open Ground, Campus",
            start_datetime=now + timedelta(days=45),
            end_datetime=now + timedelta(days=46),
            participant_limit=200,
            registration_deadline=now + timedelta(days=40),
            status=Event.Status.PUBLISHED,
            created_by=club_user,
        )

        # ── Registrations ─────────────────────────────────────────────────
        self.stdout.write("Creating registrations and attendance...")

        reg1 = EventRegistration.objects.create(
            event=event_past_1, student=student, status=EventRegistration.Status.ATTENDED
        )
        reg2 = EventRegistration.objects.create(
            event=event_past_2, student=student, status=EventRegistration.Status.ATTENDED
        )
        reg3 = EventRegistration.objects.create(
            event=event_upcoming_1, student=student, status=EventRegistration.Status.REGISTERED
        )

        # Attendance records for attended events
        AttendanceRecord.objects.create(
            event=event_past_1, student=student, registration=reg1,
            marked_by=club_user, status=AttendanceRecord.Status.PRESENT,
        )
        AttendanceRecord.objects.create(
            event=event_past_2, student=student, registration=reg2,
            marked_by=club_user, status=AttendanceRecord.Status.PRESENT,
        )

        # ── Certificate ───────────────────────────────────────────────────
        self.stdout.write("Generating certificate for Tech Summit 2024...")
        from io import BytesIO

        from django.core.files.base import ContentFile
        from django.utils.text import slugify
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas

        cert_number = f"CC-{event_past_1.id}-{student.id}-DEMO2024"
        certificate = Certificate.objects.create(
            event=event_past_1,
            student=student,
            certificate_number=cert_number,
            is_issued=True,
        )

        # Build PDF
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        pdf.setTitle("CampusConnect Participation Certificate")
        pdf.setFont("Helvetica-Bold", 22)
        pdf.drawCentredString(width / 2, height - 1.5 * inch, "CampusConnect Participation Certificate")
        pdf.setFont("Helvetica", 14)
        pdf.drawCentredString(width / 2, height - 2.4 * inch, "This certifies that")
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawCentredString(width / 2, height - 3.1 * inch, student.get_full_name() or student.username)
        pdf.setFont("Helvetica", 12)
        pdf.drawCentredString(width / 2, height - 3.7 * inch, f"College: {college.name}")
        pdf.drawCentredString(width / 2, height - 3.98 * inch, f"Department: {dept_cs.name}")
        pdf.drawCentredString(width / 2, height - 4.26 * inch, f"Registration No: {student.student_profile.registration_no}")
        pdf.setFont("Helvetica", 14)
        body = (
            f"successfully participated in the event {event_past_1.title} organized by "
            f"{event_past_1.club.name}."
        )
        text = pdf.beginText(1.0 * inch, height - 5.0 * inch)
        text.setFont("Helvetica", 14)
        text.textLine(body)
        pdf.drawText(text)
        pdf.setFont("Helvetica", 12)
        pdf.drawString(1.0 * inch, 1.9 * inch, f"Event: {event_past_1.title}")
        pdf.drawString(1.0 * inch, 1.6 * inch, f"Club: {event_past_1.club.name}")
        pdf.drawString(1.0 * inch, 1.3 * inch, f"Certificate ID: {cert_number}")
        pdf.drawString(1.0 * inch, 1.0 * inch, f"Issue Date: {timezone.localdate(timezone.now()).strftime('%d %B %Y')}")
        pdf.save()
        buffer.seek(0)
        filename = f"certificate-{slugify(event_past_1.title)}-{student.id}.pdf"
        certificate.file.save(filename, ContentFile(buffer.getvalue()), save=True)

        self.stdout.write(self.style.SUCCESS("\n✓ Demo setup complete!"))
        self.stdout.write("")
        self.stdout.write("  Login credentials:")
        self.stdout.write("  ─────────────────────────────────────────")
        self.stdout.write("  Admin    →  username: admin     password: Admin@1234")
        self.stdout.write("  Club Rep →  username: clubrep   password: Club@1234")
        self.stdout.write("  Student  →  username: student   password: Student@1234")
        self.stdout.write("  ─────────────────────────────────────────")
        self.stdout.write("")
        self.stdout.write("  Events created:")
        self.stdout.write(f"  · Tech Summit 2024           (COMPLETED) — student attended, certificate issued")
        self.stdout.write(f"  · Python & Django Workshop   (COMPLETED) — student attended")
        self.stdout.write(f"  · Hackathon 2025             (UPCOMING)  — student registered")
        self.stdout.write(f"  · Annual Tech Fest           (UPCOMING)  — open for registration")
