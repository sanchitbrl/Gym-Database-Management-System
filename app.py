from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import psycopg2
import psycopg2.extras
import json

app = Flask(__name__)
app.secret_key = "gym_secret_key_change_me"

# ---------------------------------------------
# Database configuration - EDIT THESE VALUES
# ---------------------------------------------
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "admin",   # <-- change this
    "dbname": "gym_db"
}


def get_db_connection():
    """Create and return a new database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None


def dict_cursor(conn):
    """Return a cursor that yields rows as dicts (like mysql's dictionary=True)."""
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def archive_before_delete(conn, entity_type, table, id_column, id_value):
    """
    Snapshot a row into deleted_history before it gets deleted.
    This is why old member/plan/trainer IDs still make sense after
    deletion -- the record isn't just gone, it's archived.
    """
    cursor = dict_cursor(conn)
    cursor.execute(f"SELECT * FROM {table} WHERE {id_column} = %s", (id_value,))
    row = cursor.fetchone()
    cursor.close()

    if row:
        row_dict = dict(row)
        archive_cursor = conn.cursor()
        archive_cursor.execute(
            """
            INSERT INTO deleted_history (entity_type, original_id, data)
            VALUES (%s, %s, %s)
            """,
            (entity_type, id_value, json.dumps(row_dict, default=str))
        )
        archive_cursor.close()
    return row


# ============================================
# DASHBOARD
# ============================================
@app.route("/")
def dashboard():
    conn = get_db_connection()
    stats = {"members": 0, "trainers": 0, "revenue": 0, "equipment": 0}
    recent_payments = []

    if conn:
        cursor = dict_cursor(conn)
        cursor.execute("SELECT COUNT(*) AS c FROM members")
        stats["members"] = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) AS c FROM trainers")
        stats["trainers"] = cursor.fetchone()["c"]

        cursor.execute("SELECT COALESCE(SUM(amount),0) AS s FROM payments")
        stats["revenue"] = cursor.fetchone()["s"]

        cursor.execute("SELECT COUNT(*) AS c FROM equipment")
        stats["equipment"] = cursor.fetchone()["c"]

        cursor.execute("""
            SELECT p.payment_id, m.name AS member_name, p.amount, p.payment_date, p.payment_mode
            FROM payments p
            JOIN members m ON p.member_id = m.member_id
            ORDER BY p.payment_date DESC LIMIT 5
        """)
        recent_payments = cursor.fetchall()

        cursor.close()
        conn.close()

    return render_template("dashboard.html", stats=stats, recent_payments=recent_payments)


# ============================================
# MEMBERS - CRUD
# ============================================
@app.route("/members")
def members():
    conn = get_db_connection()
    member_list = []
    if conn:
        cursor = dict_cursor(conn)
        cursor.execute("""
            SELECT mem.*, mp.plan_name, t.name AS trainer_name
            FROM members mem
            LEFT JOIN membership_plans mp ON mem.plan_id = mp.plan_id
            LEFT JOIN trainers t ON mem.trainer_id = t.trainer_id
            ORDER BY mem.member_id DESC
        """)
        member_list = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template("members.html", members=member_list)


@app.route("/members/add", methods=["GET", "POST"])
def add_member():
    conn = get_db_connection()
    plans, trainers = [], []
    if conn:
        cursor = dict_cursor(conn)
        cursor.execute("SELECT * FROM membership_plans")
        plans = cursor.fetchall()
        cursor.execute("SELECT * FROM trainers")
        trainers = cursor.fetchall()

        if request.method == "POST":
            data = (
                request.form["name"], request.form["age"], request.form["gender"],
                request.form["phone"], request.form["email"], request.form["address"],
                request.form["join_date"], request.form["plan_id"] or None,
                request.form["trainer_id"] or None
            )
            insert_cursor = conn.cursor()
            insert_cursor.execute("""
                INSERT INTO members (name, age, gender, phone, email, address, join_date, plan_id, trainer_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, data)
            conn.commit()
            insert_cursor.close()
            cursor.close()
            conn.close()
            flash("Member added successfully!", "success")
            return redirect(url_for("members"))

        cursor.close()
        conn.close()
    return render_template("member_form.html", plans=plans, trainers=trainers, member=None)


@app.route("/members/edit/<int:member_id>", methods=["GET", "POST"])
def edit_member(member_id):
    conn = get_db_connection()
    plans, trainers, member = [], [], None
    if conn:
        cursor = dict_cursor(conn)

        if request.method == "POST":
            data = (
                request.form["name"], request.form["age"], request.form["gender"],
                request.form["phone"], request.form["email"], request.form["address"],
                request.form["join_date"], request.form["plan_id"] or None,
                request.form["trainer_id"] or None, member_id
            )
            update_cursor = conn.cursor()
            update_cursor.execute("""
                UPDATE members SET name=%s, age=%s, gender=%s, phone=%s, email=%s,
                address=%s, join_date=%s, plan_id=%s, trainer_id=%s
                WHERE member_id=%s
            """, data)
            conn.commit()
            update_cursor.close()
            cursor.close()
            conn.close()
            flash("Member updated successfully!", "success")
            return redirect(url_for("members"))

        cursor.execute("SELECT * FROM membership_plans")
        plans = cursor.fetchall()
        cursor.execute("SELECT * FROM trainers")
        trainers = cursor.fetchall()
        cursor.execute("SELECT * FROM members WHERE member_id=%s", (member_id,))
        member = cursor.fetchone()
        cursor.close()
        conn.close()
    return render_template("member_form.html", plans=plans, trainers=trainers, member=member)


@app.route("/members/delete/<int:member_id>")
def delete_member(member_id):
    conn = get_db_connection()
    if conn:
        archive_before_delete(conn, "member", "members", "member_id", member_id)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM members WHERE member_id=%s", (member_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Member deleted (saved to history).", "info")
    return redirect(url_for("members"))


# ============================================
# TRAINERS - CRUD
# ============================================
@app.route("/trainers")
def trainers():
    conn = get_db_connection()
    trainer_list = []
    if conn:
        cursor = dict_cursor(conn)
        cursor.execute("""
            SELECT t.*, COUNT(m.member_id) AS member_count
            FROM trainers t
            LEFT JOIN members m ON t.trainer_id = m.trainer_id
            GROUP BY t.trainer_id
            ORDER BY t.trainer_id DESC
        """)
        trainer_list = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template("trainers.html", trainers=trainer_list)


@app.route("/trainers/add", methods=["GET", "POST"])
def add_trainer():
    if request.method == "POST":
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            data = (
                request.form["name"], request.form["specialization"], request.form["phone"],
                request.form["email"], request.form["salary"], request.form["joining_date"]
            )
            cursor.execute("""
                INSERT INTO trainers (name, specialization, phone, email, salary, joining_date)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, data)
            conn.commit()
            cursor.close()
            conn.close()
            flash("Trainer added successfully!", "success")
        return redirect(url_for("trainers"))
    return render_template("trainer_form.html", trainer=None)


@app.route("/trainers/edit/<int:trainer_id>", methods=["GET", "POST"])
def edit_trainer(trainer_id):
    conn = get_db_connection()
    trainer = None
    if conn:
        cursor = dict_cursor(conn)
        if request.method == "POST":
            data = (
                request.form["name"], request.form["specialization"], request.form["phone"],
                request.form["email"], request.form["salary"], request.form["joining_date"], trainer_id
            )
            upd_cursor = conn.cursor()
            upd_cursor.execute("""
                UPDATE trainers SET name=%s, specialization=%s, phone=%s, email=%s, salary=%s, joining_date=%s
                WHERE trainer_id=%s
            """, data)
            conn.commit()
            upd_cursor.close()
            cursor.close()
            conn.close()
            flash("Trainer updated successfully!", "success")
            return redirect(url_for("trainers"))

        cursor.execute("SELECT * FROM trainers WHERE trainer_id=%s", (trainer_id,))
        trainer = cursor.fetchone()
        cursor.close()
        conn.close()
    return render_template("trainer_form.html", trainer=trainer)


@app.route("/trainers/delete/<int:trainer_id>")
def delete_trainer(trainer_id):
    conn = get_db_connection()
    if conn:
        archive_before_delete(conn, "trainer", "trainers", "trainer_id", trainer_id)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM trainers WHERE trainer_id=%s", (trainer_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Trainer deleted (saved to history).", "info")
    return redirect(url_for("trainers"))


# ============================================
# MEMBERSHIP PLANS
# ============================================
@app.route("/plans")
def plans():
    conn = get_db_connection()
    plan_list = []
    if conn:
        cursor = dict_cursor(conn)
        cursor.execute("SELECT * FROM membership_plans ORDER BY plan_id")
        plan_list = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template("plans.html", plans=plan_list)


@app.route("/plans/add", methods=["GET", "POST"])
def add_plan():
    if request.method == "POST":
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            data = (
                request.form["plan_name"], request.form["duration_months"],
                request.form["price"], request.form["description"]
            )
            cursor.execute("""
                INSERT INTO membership_plans (plan_name, duration_months, price, description)
                VALUES (%s,%s,%s,%s)
            """, data)
            conn.commit()
            cursor.close()
            conn.close()
            flash("Plan added successfully!", "success")
        return redirect(url_for("plans"))
    return render_template("plan_form.html")


@app.route("/plans/delete/<int:plan_id>")
def delete_plan(plan_id):
    conn = get_db_connection()
    if conn:
        archive_before_delete(conn, "plan", "membership_plans", "plan_id", plan_id)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM membership_plans WHERE plan_id=%s", (plan_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Plan deleted (saved to history).", "info")
    return redirect(url_for("plans"))


# ============================================
# PAYMENTS
# ============================================
@app.route("/payments")
def payments():
    conn = get_db_connection()
    payment_list = []
    if conn:
        cursor = dict_cursor(conn)
        cursor.execute("""
            SELECT p.*, m.name AS member_name
            FROM payments p
            JOIN members m ON p.member_id = m.member_id
            ORDER BY p.payment_date DESC
        """)
        payment_list = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template("payments.html", payments=payment_list)


@app.route("/payments/add", methods=["GET", "POST"])
def add_payment():
    conn = get_db_connection()
    members_list = []
    if conn:
        cursor = dict_cursor(conn)
        cursor.execute("SELECT member_id, name FROM members")
        members_list = cursor.fetchall()

        if request.method == "POST":
            data = (
                request.form["member_id"], request.form["amount"],
                request.form["payment_date"], request.form["payment_mode"]
            )
            ins_cursor = conn.cursor()
            ins_cursor.execute("""
                INSERT INTO payments (member_id, amount, payment_date, payment_mode)
                VALUES (%s,%s,%s,%s)
            """, data)
            conn.commit()
            ins_cursor.close()
            cursor.close()
            conn.close()
            flash("Payment recorded successfully!", "success")
            return redirect(url_for("payments"))

        cursor.close()
        conn.close()
    return render_template("payment_form.html", members=members_list)


# ============================================
# EQUIPMENT
# ============================================
@app.route("/equipment")
def equipment():
    conn = get_db_connection()
    equipment_list = []
    if conn:
        cursor = dict_cursor(conn)
        cursor.execute("SELECT * FROM equipment ORDER BY equipment_id DESC")
        equipment_list = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template("equipment.html", equipment=equipment_list)


@app.route("/equipment/add", methods=["GET", "POST"])
def add_equipment():
    if request.method == "POST":
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            data = (
                request.form["name"], request.form["category"], request.form["quantity"],
                request.form["purchase_date"], request.form["condition_status"]
            )
            cursor.execute("""
                INSERT INTO equipment (name, category, quantity, purchase_date, condition_status)
                VALUES (%s,%s,%s,%s,%s)
            """, data)
            conn.commit()
            cursor.close()
            conn.close()
            flash("Equipment added successfully!", "success")
        return redirect(url_for("equipment"))
    return render_template("equipment_form.html")


@app.route("/equipment/delete/<int:equipment_id>")
def delete_equipment(equipment_id):
    conn = get_db_connection()
    if conn:
        archive_before_delete(conn, "equipment", "equipment", "equipment_id", equipment_id)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM equipment WHERE equipment_id=%s", (equipment_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Equipment removed (saved to history).", "info")
    return redirect(url_for("equipment"))


# ============================================
# ATTENDANCE
# ============================================
@app.route("/attendance")
def attendance():
    conn = get_db_connection()
    attendance_list = []
    if conn:
        cursor = dict_cursor(conn)
        cursor.execute("""
            SELECT a.*, m.name AS member_name
            FROM attendance a
            JOIN members m ON a.member_id = m.member_id
            ORDER BY a.check_in_date DESC, a.check_in_time DESC
        """)
        attendance_list = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template("attendance.html", attendance=attendance_list)


@app.route("/attendance/add", methods=["GET", "POST"])
def add_attendance():
    conn = get_db_connection()
    members_list = []
    if conn:
        cursor = dict_cursor(conn)
        cursor.execute("SELECT member_id, name FROM members")
        members_list = cursor.fetchall()

        if request.method == "POST":
            data = (
                request.form["member_id"], request.form["check_in_date"],
                request.form["check_in_time"], request.form["check_out_time"] or None
            )
            ins_cursor = conn.cursor()
            ins_cursor.execute("""
                INSERT INTO attendance (member_id, check_in_date, check_in_time, check_out_time)
                VALUES (%s,%s,%s,%s)
            """, data)
            conn.commit()
            ins_cursor.close()
            cursor.close()
            conn.close()
            flash("Attendance recorded!", "success")
            return redirect(url_for("attendance"))

        cursor.close()
        conn.close()
    return render_template("attendance_form.html", members=members_list)


# ============================================
# HISTORY (archived / deleted records)
# ============================================
@app.route("/history")
def history():
    conn = get_db_connection()
    history_list = []
    filter_type = request.args.get("type", "all")

    if conn:
        cursor = dict_cursor(conn)
        if filter_type != "all":
            cursor.execute(
                "SELECT * FROM deleted_history WHERE entity_type=%s ORDER BY deleted_at DESC",
                (filter_type,)
            )
        else:
            cursor.execute("SELECT * FROM deleted_history ORDER BY deleted_at DESC")
        history_list = cursor.fetchall()
        cursor.close()
        conn.close()

    return render_template("history.html", history=history_list, filter_type=filter_type)


if __name__ == "__main__":
    app.run(debug=True)
