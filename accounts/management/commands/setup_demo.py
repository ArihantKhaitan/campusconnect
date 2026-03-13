from django.core.management.base import BaseCommand

from accounts.models import StudentProfile, User
from organizations.models import Club, College, Department


class Command(BaseCommand):
    help = "Clear all users and create demo accounts for testing"

    def handle(self, *args, **kwargs):
        self.stdout.write("Clearing all users...")
        User.objects.all().delete()

        self.stdout.write("Setting up demo college, department, and club...")
        college, _ = College.objects.get_or_create(name="Demo University")
        dept_cs, _ = Department.objects.get_or_create(college=college, name="Computer Science", defaults={"code": "CS"})
        dept_ec, _ = Department.objects.get_or_create(college=college, name="Electronics", defaults={"code": "EC"})
        club, _ = Club.objects.get_or_create(name="Tech Club", college=college, defaults={"description": "The official technology and innovation club."})

        self.stdout.write("Creating admin user...")
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@campusconnect.demo",
            password="Admin@1234",
            first_name="Admin",
            last_name="User",
            role=User.Roles.ADMIN,
        )

        self.stdout.write("Creating club representative user...")
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

        self.stdout.write("Creating student user...")
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

        self.stdout.write(self.style.SUCCESS("\n✓ Demo setup complete!"))
        self.stdout.write("")
        self.stdout.write("  Login credentials:")
        self.stdout.write("  ─────────────────────────────────────────")
        self.stdout.write("  Admin    →  username: admin     password: Admin@1234")
        self.stdout.write("  Club Rep →  username: clubrep   password: Club@1234")
        self.stdout.write("  Student  →  username: student   password: Student@1234")
        self.stdout.write("  ─────────────────────────────────────────")
