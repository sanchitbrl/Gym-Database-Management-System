# FitZone Gym Management System

A full-stack DBMS college project built with:
- **Frontend:** HTML, CSS, Bootstrap 5, JavaScript
- **Backend:** Python Flask
- **Database:** PostgreSQL

## Features
- Dashboard with live stats (members, trainers, revenue, equipment)
- Members management (CRUD) with plan & trainer assignment
- Trainers management (CRUD)
- Membership plans (CRUD)
- Payments tracking
- Equipment inventory
- Attendance log
- Uses JOINs, foreign keys, ENUM types, and aggregate queries — great for demonstrating DBMS concepts

## Database Design (ER Overview)
- `members` — links to `membership_plans` and `trainers` (many-to-one each)
- `payments` — links to `members` (many-to-one)
- `attendance` — links to `members` (many-to-one)
- `trainers` — one trainer can have many members
- `equipment` — standalone inventory table

## Setup Instructions

### 1. Make sure PostgreSQL is running
Check with:
```
pg_isready
```

### 2. Create the Database and Tables
Run the schema file with psql (this also creates the `gym_db` database itself):
```
psql -U postgres -f schema.sql
```
If your local Postgres user isn't `postgres`, substitute your own username. You'll be prompted for a password if one is set.

This creates the `gym_db` database, all tables, ENUM types, and inserts sample data.

### 3. Install Python Dependencies
```
cd gym_management
pip install -r requirements.txt
```

### 4. Configure Database Credentials
Open `app.py` and update the `DB_CONFIG` dictionary with your PostgreSQL username/password:
```python
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "your_postgres_password",
    "dbname": "gym_db"
}
```
If you're using peer authentication locally with no password, you can usually leave `password` blank (`""`).

### 5. Run the App
```
python app.py
```
Visit **http://127.0.0.1:5000** in your browser.

## Project Structure
```
gym_management/
├── app.py                 # Flask application (routes + DB logic)
├── schema.sql              # PostgreSQL schema + sample data
├── requirements.txt
├── static/
│   └── css/style.css
└── templates/
    ├── base.html            # Shared layout & navbar
    ├── dashboard.html
    ├── members.html / member_form.html
    ├── trainers.html / trainer_form.html
    ├── plans.html / plan_form.html
    ├── payments.html / payment_form.html
    ├── equipment.html / equipment_form.html
    └── attendance.html / attendance_form.html
```

## Troubleshooting
- **"database gym_db already exists" error on re-run:** the schema drops and recreates the DB automatically, but if `psql` is currently connected to `gym_db` itself when you run the script, the DROP will fail. Connect to a different database first, e.g. `psql -U postgres -d postgres -f schema.sql`.
- **Connection refused:** confirm Postgres is listening on port 5432 (`sudo systemctl status postgresql` on Linux) and that `host`/`port` in `DB_CONFIG` match.
- **Password authentication failed:** check `pg_hba.conf` — for local dev it's common to set the method to `trust` or `md5` for the `postgres` user.

## Ideas for Extending (bonus marks)
- Add login/authentication (admin vs staff roles)
- Auto-calculate membership expiry from `join_date` + plan duration
- Add SQL views, triggers, or stored procedures/functions for extra DBMS credit
  (e.g., a trigger to auto-log a payment when a member is created)
- Add charts (Chart.js) to the dashboard for revenue trends
- Export member/payment reports to PDF or CSV
