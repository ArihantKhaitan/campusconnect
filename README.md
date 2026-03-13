# CampusConnect

A full-stack college event management platform built with Django. Students can browse and register for events, clubs manage their events and attendance, and admins oversee the entire platform with automatic PDF certificate generation on completion.

---

## Features

**Student**
- Browse and register for upcoming events
- View registration status and event details
- Download participation certificates (PDF) once issued

**Club Representative**
- Create and manage events (draft → published → completed)
- View participant list with registration status
- Mark attendance for registered students
- Issue certificates to attended students
- Analytics dashboard — registrations per event, attendance trends

**Admin**
- Platform-wide dashboard with key statistics
- Manage users, events, colleges, clubs, and certificates
- Analytics — top events, department-wise participation, monthly trends, registration vs attendance comparison

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Django 4.2 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| REST API | Django REST Framework 3.16 |
| PDF generation | ReportLab 4.4 |
| Frontend | Bootstrap 5.3.3, Bootstrap Icons 1.11.3 |
| Charts | Chart.js (CDN) |
| Fonts | Inter (Google Fonts) |
| Image handling | Pillow |

---

## Project Structure

```
campusconnect/
├── accounts/          # Custom User model (ADMIN / CLUB / STUDENT roles), StudentProfile
│   └── management/commands/setup_demo.py   # Demo data seeder
├── analytics/         # Analytics views + Chart.js dashboards
├── certificates/      # Certificate model, PDF generation, download
├── core/              # Home, dashboards, admin management views
├── events/            # Event, EventRegistration, AttendanceRecord models
├── organizations/     # College, Department, Club models
├── static/css/app.css # All custom CSS (design tokens, dark mode)
├── templates/         # All HTML templates
│   ├── layouts/       # base.html, dashboard_base.html
│   ├── dashboards/    # Per-role dashboard pages
│   ├── analytics/     # Chart.js analytics pages
│   ├── events/        # Event list, detail, form, participants
│   └── accounts/      # Login, signup, profile
└── manage.py
```

---

## Setup

```bash
# 1. Clone the repo
git clone <repo-url>
cd campusconnect

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply database migrations
python manage.py migrate

# 5. Load demo data (creates 3 accounts + 4 events with full flow pre-seeded)
python manage.py setup_demo

# 6. Start the development server
python manage.py runserver
```

Visit [http://localhost:8000](http://localhost:8000)

> **Note:** A `.env` file is optional for local development. If you have one, place it in the project root:
> ```env
> SECRET_KEY=your-secret-key-here
> DEBUG=True
> ALLOWED_HOSTS=localhost,127.0.0.1
> ```

### Demo accounts (created by `setup_demo`)

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@1234` |
| Club Rep | `clubrep` | `Club@1234` |
| Student | `student` | `Student@1234` |

**Events pre-loaded:**
- **Tech Summit 2024** — completed, student attended, certificate pre-generated and downloadable
- **Python & Django Workshop** — completed, student attended (club can issue certificate)
- **Hackathon 2025** — upcoming, student registered
- **Annual Tech Fest** — upcoming, open for registration

---

## User Flows

### Full demo flow (end-to-end)

1. **Login as `clubrep`** → go to Participants for *Python & Django Workshop* → mark student attended → issue certificate
2. **Login as `student`** → go to Dashboard → download the certificate for *Tech Summit 2024* (pre-generated)
3. **Login as `admin`** → view Analytics for system-wide stats and charts

### Event lifecycle

```
DRAFT → PUBLISHED → COMPLETED
                ↘ CANCELLED
```

- Students can register only while status is `PUBLISHED` and registration deadline has not passed
- Attendance can only be marked for registered students
- Certificates can only be issued after attendance is marked `PRESENT`

---

## Models Overview

```
User (AbstractUser)
├── role: ADMIN | CLUB | STUDENT
└── StudentProfile (1:1)
    ├── college → College
    └── department → Department

College
├── Department (1:N)
└── Club (1:N)
    └── representative → User

Event
├── club → Club
├── college → College
├── category → EventCategory
├── EventRegistration (1:N) → student
└── AttendanceRecord (1:N) → student

Certificate
├── event → Event
└── student → User
```

---

## API

The project includes a Django REST Framework API. Endpoints are under `/api/`.

To explore: run the server and visit `/api/` (browsable API) or check `*/urls.py` files across each app.

---

## Django Admin

Available at `/admin/` (login with the `admin` account).

The custom CampusConnect admin dashboard at `/dashboard/admin/` provides a more user-friendly interface for the same data.

---

## Dark Mode

Built-in dark mode toggle in the dashboard header. Preference is stored in `localStorage` and persists across sessions.

---

## License

MIT
