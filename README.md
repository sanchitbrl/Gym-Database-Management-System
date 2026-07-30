# SwasthaZone Gym Management System

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

These steps work on **Linux, macOS, and Windows**. Platform-specific notes are called out where they differ.

### 1. Install PostgreSQL (if you don't already have it)

- **Linux:** `sudo apt install postgresql` (Debian/Ubuntu) or your distro's equivalent.
- **macOS:** Either the [EDB PostgreSQL installer](https://www.postgresql.org/download/macos/) (a `.dmg` wizard — this is what most Mac users end up using) or Homebrew (`brew install postgresql@16`). **The two behave differently — see the macOS notes below.**
- **Windows (WSL):** treat it as Linux inside your WSL distro.

Check it's running:
```bash
pg_isready
```

### 2. Create the Database and Tables

Run the schema file with `psql`. This also creates the `gym_db` database itself:
```bash
psql -U postgres -d postgres -f schema.sql
```
> Always connect to a *different* database first (`-d postgres`), not `gym_db` — the script starts with `DROP DATABASE IF EXISTS gym_db`, and that fails if `psql` is already sitting inside `gym_db`.

You'll be prompted for the password of the `postgres` role (see macOS/Linux notes below for what that means for you).

This creates the `gym_db` database, all tables, ENUM types, and inserts sample data.

### 3. Install Python Dependencies
```bash
cd gym_management
pip install -r requirements.txt
```

> **macOS + Python 3.13 users:** `psycopg2-binary==2.9.9` has no prebuilt wheel for Python 3.13 and will try to compile from source — this fails with an `_PyInterpreterState_Get` error on newer clang. Use `pip install "psycopg2-binary>=2.9.10"` instead (already reflected in `requirements.txt` below). If you're on Anaconda, `conda install -c conda-forge psycopg2` is a solid alternative that skips compiling entirely.

### 4. Configure Database Credentials

Open `app.py` in a **text editor** (not the terminal!) and update the `DB_CONFIG` dictionary near the top with your PostgreSQL username/password:
```python
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "your_postgres_password",
    "dbname": "gym_db"
}
```
Save the file after editing — this code lives in `app.py`, it doesn't get typed into your terminal.

**Where does the password come from?**
- **macOS (EDB installer):** the password you set in the installer wizard when you first installed PostgreSQL. The `postgres` role already exists with this setup, so `user: "postgres"` works as-is.
- **macOS (Homebrew):** Homebrew doesn't create a `postgres` role by default — it creates one matching your Mac username instead, usually with no password needed (`"password": ""`). Either run `createuser -s postgres` once to make a `postgres` role, or just set `"user"` to your own Mac username in `DB_CONFIG`.
- **Linux:** if you're using peer authentication locally (common default on Debian/Ubuntu), you can usually leave `"password": ""` when connecting as your OS user, or set a password for the `postgres` role with `sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'yourpassword';"`.

### 5. Run the App
```bash
python3 app.py
```
> On macOS/Linux, `python` isn't always aliased to Python 3 — use `python3` explicitly to be safe. If you're inside an activated Anaconda/conda environment, `python` usually resolves correctly too.

Visit **http://127.0.0.1:5000** in your browser.

> **macOS note:** if the page won't load, something else may already be using port 5000 — macOS's AirPlay Receiver commonly does. Either disable it (System Settings → General → AirDrop & Handoff → AirPlay Receiver) or change the port at the bottom of `app.py`: `app.run(debug=True, port=5001)`.

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

- **"database gym_db already exists" error on re-run:** the schema drops and recreates the DB automatically, but if `psql` is currently connected to `gym_db` itself when you run the script, the DROP will fail. Connect to a different database first: `psql -U postgres -d postgres -f schema.sql`.
- **Connection refused:** confirm Postgres is listening on port 5432 and that `host`/`port` in `DB_CONFIG` match.
  - Linux: `sudo systemctl status postgresql`
  - macOS (Homebrew): `brew services list`
  - macOS (EDB installer): check Activity Monitor for a `postgres` process, or use the PostgreSQL app installed alongside it.
- **Password authentication failed:** double-check the password in `DB_CONFIG` matches the one your `psql` connection actually accepts. On Linux, check `pg_hba.conf` — for local dev it's common to set the method to `trust` or `md5` for the `postgres` user.
- **`role "postgres" does not exist` (macOS, Homebrew installs):** Homebrew doesn't create this role automatically. Run `createuser -s postgres` once, or use your Mac username instead throughout (`-U yourusername` and in `DB_CONFIG`).
- **`psycopg2-binary` fails to build from source:** you're likely on Python 3.13 with an old pin. Run `pip install "psycopg2-binary>=2.9.10"` to get a prebuilt wheel instead of compiling.
- **`zsh: parse error near '}'`:** this means Python code (like the `DB_CONFIG` dictionary) got pasted directly into the terminal instead of into `app.py`. Only shell commands (`pip install ...`, `python3 app.py`, etc.) go in the terminal — Python code edits go in the file itself, opened with a text editor (`open -e app.py` on macOS, or any code editor).
- **`psql: command not found` (macOS, EDB installer):** the installer doesn't always add `psql` to your PATH. Either add `/Library/PostgreSQL/<version>/bin` to your PATH, or call it directly, e.g. `/Library/PostgreSQL/18/bin/psql -U postgres -d postgres -f schema.sql`.

## Security Note

`DB_CONFIG` in `app.py` holds a real database password in plaintext. That's fine for local dev on a college project, but **don't commit real credentials to a public repo** — either keep a placeholder in version control and set the real password locally only, or load it from an environment variable (`os.environ.get("DB_PASSWORD")`) instead.

## Ideas for Extending (bonus marks)
- Add login/authentication (admin vs staff roles)
- Auto-calculate membership expiry from `join_date` + plan duration
- Add SQL views, triggers, or stored procedures/functions for extra DBMS credit
  (e.g., a trigger to auto-log a payment when a member is created)
- Add charts (Chart.js) to the dashboard for revenue trends
- Export member/payment reports to PDF or CSV
