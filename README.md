# CampusCare – Smart Campus Complaint and Maintenance Management System (CA-05)

CampusCare is a full-stack web application designed for universities and campus facilities to streamline maintenance complaints, automate task assignment, track repair workflows in real time, and notify students instantly when status changes occur.

---

## 🌟 Key Features

### 1. Multi-Role Authentication & Access Control
- **Student**:
  - Self-registration and secure login.
  - Submit maintenance complaints with categorization (Electrical, Plumbing, Furniture, Network, Equipment, Other) and precise campus locations.
  - Track complaint lifecycle with chronological status history and timeline.
  - Receive automatic in-app notifications upon status transitions.
  - Mark notifications as read or mark all as read.
  - Profile management.
- **Administrator**:
  - Secure management dashboard with system-wide analytics.
  - View all complaints and filter by status/category.
  - Queue of complaints waiting for assignment.
  - Assign qualified technicians to open complaints with custom notes.
  - Close resolved complaints after verification.
  - View user directory (Students & Technicians).
  - Analytical reports with interactive charts (Status Breakdown, Category Distribution, Technician Task Performance).
- **Technician**:
  - Dedicated technician task board.
  - View assigned complaints.
  - Transition tasks from **Assigned** $\rightarrow$ **In Progress** $\rightarrow$ **Resolved** with progress notes.
  - Complete history of past resolved assignments.

---

## 📐 Architecture & Design Pattern

### 1. Four-Layer Architecture
- **Presentation Layer**: Django templates (Bootstrap 5, dark teal theme), forms, views, and URL routing.
- **Application Layer** (`complaints/services.py`): Business use-case coordination, complaint submission, technician assignment, status transition enforcement, and event publishing.
- **Domain Layer** (`complaints/models.py`, `accounts/models.py`): Core entities (`User`, `Complaint`, `StatusHistory`, `Notification`), validation rules, and lifecycle states.
- **Infrastructure Layer** (`complaints/repositories.py`, `complaints/events.py`, Django ORM): Repository data access and event publishing infrastructure.

### 2. Observer Design Pattern
Implemented in:
- `complaints/events.py`: `EventPublisher` with `subscribe()`, `unsubscribe()`, and `publish()`.
- `complaints/observers.py`: `NotificationObserver` and `LoggingObserver` adhering to the abstract `Observer` contract.
- Whenever a complaint status is transitioned:
  1. Status updated in database.
  2. Status change recorded in `StatusHistory`.
  3. A `ComplaintStatusChangedEvent` is published to `EventPublisher`.
  4. `NotificationObserver` generates an in-app notification for the student.

---

## 🚀 Running the Project

The Django development server is currently active and listening on:
**[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

### To run manually from terminal:
```bash
# 1. Activate Python environment
python manage.py migrate

# 2. Seed initial demo data (if starting fresh)
python manage.py seed_data

# 3. Start server
python manage.py runserver 127.0.0.1:8000
```

---

## 🔑 Demo Login Credentials

| Role | Username | Password | Dashboard URL |
|---|---|---|---|
| **Administrator** | `admin` | `admin123` | `http://127.0.0.1:8000/accounts/dashboard/admin/` |
| **Student 1** | `student1` | `student123` | `http://127.0.0.1:8000/accounts/dashboard/student/` |
| **Student 2** | `student2` | `student123` | `http://127.0.0.1:8000/accounts/dashboard/student/` |
| **Student 3** | `student3` | `student123` | `http://127.0.0.1:8000/accounts/dashboard/student/` |
| **Technician 1** | `tech1` | `tech123` | `http://127.0.0.1:8000/accounts/dashboard/technician/` |
| **Technician 2** | `tech2` | `tech123` | `http://127.0.0.1:8000/accounts/dashboard/technician/` |
| **Technician 3** | `tech3` | `tech123` | `http://127.0.0.1:8000/accounts/dashboard/technician/` |

---

## 🧪 Testing

To execute the automated test suite:
```bash
python manage.py test complaints
```
Tests cover:
- Student registration & password hashing
- Role-based dashboard protection & negative access authorization
- Complaint submission & student isolation
- Admin assignment & technician transition workflow
- Observer pattern event publishing & student in-app notifications
- Analytics & reporting metrics

