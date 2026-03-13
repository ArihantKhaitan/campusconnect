from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from certificates.models import Certificate
from events.models import AttendanceRecord, Event, EventCategory, EventRegistration
from organizations.models import Club, College, Department
from accounts.models import StudentProfile


class Command(BaseCommand):
    help = "Populate the database with realistic CampusConnect demo data."

    def handle(self, *args, **options):
        User = get_user_model()
        now = timezone.now()

        Certificate.objects.all().delete()
        AttendanceRecord.objects.all().delete()
        EventRegistration.objects.all().delete()
        Event.objects.all().delete()
        Club.objects.all().delete()
        Department.objects.all().delete()
        College.objects.all().delete()
        StudentProfile.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()

        colleges = {}
        for name in ["MIT Manipal", "BITS Goa", "IIT Bombay"]:
            colleges[name] = College.objects.create(name=name)

        departments = {}
        for college in colleges.values():
            for dept_name in ["Computer Science", "AI & ML", "Electronics", "Mechanical"]:
                departments[(college.name, dept_name)] = Department.objects.create(college=college, name=dept_name)

        categories = {}
        for name in ["Workshop", "Hackathon", "Competition", "Seminar", "Bootcamp"]:
            categories[name] = EventCategory.objects.get_or_create(name=name)[0]

        admin = User.objects.create_superuser(username="admin", password="admin123", email="admin@campusconnect.test")
        admin.role = User.Roles.ADMIN
        admin.save(update_fields=["role"])

        club_specs = [
            ("club_coding", "Coding Club", colleges["MIT Manipal"]),
            ("club_ai", "AI Club", colleges["BITS Goa"]),
            ("club_robotics", "Robotics Club", colleges["IIT Bombay"]),
        ]
        clubs = {}
        for username, club_name, college in club_specs:
            user = User.objects.create_user(username=username, password="password123", email=f"{username}@campusconnect.test", role=User.Roles.CLUB)
            club = Club.objects.create(name=club_name, college=college, representative=user, contact_email=f"{username}@campusconnect.test")
            clubs[club_name] = club

        student_specs = [
            ("student1", "Aarav", "Sharma", "MIT Manipal", "Computer Science"),
            ("student2", "Diya", "Kapoor", "MIT Manipal", "AI & ML"),
            ("student3", "Rohan", "Mehta", "BITS Goa", "Computer Science"),
            ("student4", "Ishita", "Rao", "BITS Goa", "Electronics"),
            ("student5", "Kabir", "Nair", "IIT Bombay", "Mechanical"),
            ("student6", "Anaya", "Singh", "IIT Bombay", "AI & ML"),
        ]
        students = []
        for index, (username, first_name, last_name, college_name, dept_name) in enumerate(student_specs, start=1):
            user = User.objects.create_user(
                username=username,
                password="password123",
                email=f"{username}@campusconnect.test",
                first_name=first_name,
                last_name=last_name,
                role=User.Roles.STUDENT,
            )
            StudentProfile.objects.create(
                user=user,
                college=colleges[college_name],
                department=departments[(college_name, dept_name)],
                batch="2026",
                roll_no=f"ROLL{index:03d}",
                registration_no=f"REG{index:03d}",
            )
            students.append(user)

        event_specs = [
            (clubs["Coding Club"], categories["Hackathon"], "Hackathon", 3, 80),
            (clubs["Coding Club"], categories["Bootcamp"], "Python Bootcamp", 7, 60),
            (clubs["AI Club"], categories["Workshop"], "AI Workshop", 10, 50),
            (clubs["Robotics Club"], categories["Competition"], "Robotics Challenge", 14, 40),
            (clubs["AI Club"], categories["Seminar"], "Debate Competition", 18, 70),
        ]
        events = []
        for club, category, title, day_offset, limit in event_specs:
            start = now + timedelta(days=day_offset)
            event = Event.objects.create(
                club=club,
                college=club.college,
                category=category,
                title=title,
                description=f"{title} hosted by {club.name} for students interested in collaborative learning and campus activities.",
                venue=f"{club.college.name} Auditorium",
                start_datetime=start,
                end_datetime=start + timedelta(hours=3),
                participant_limit=limit,
                registration_deadline=start - timedelta(days=2),
                status=Event.Status.PUBLISHED,
                created_by=club.representative,
            )
            events.append(event)

        for idx, student in enumerate(students):
            event = events[idx % len(events)]
            registration = EventRegistration.objects.create(event=event, student=student, status=EventRegistration.Status.REGISTERED)
            if idx % 2 == 0:
                AttendanceRecord.objects.create(
                    event=event,
                    student=student,
                    registration=registration,
                    marked_by=event.club.representative,
                    status=AttendanceRecord.Status.PRESENT,
                )
                registration.status = EventRegistration.Status.ATTENDED
                registration.save(update_fields=["status"])
                Certificate.objects.create(
                    event=event,
                    student=student,
                    certificate_number=f"CC-SEED-{event.id}-{student.id}",
                    is_issued=True,
                )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
