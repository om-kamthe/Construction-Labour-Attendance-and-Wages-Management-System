"""
CONSTRUCTION LABOUR ATTENDANCE AND WAGES CALCULATION MANAGEMENT SYSTEM
Single-file starter project.

Technical stack retained from the reference project:
- Python
- Flask web application and render_template_string
- MySQL database using mysql-connector-python
- Embedded HTML + CSS dashboard
- Parameterized SQL queries
- Optional Tkinter desktop view
- Shared MySQL database for both interfaces

Install:
    pip install flask mysql-connector-python

Before running:
    1. Start MySQL Server.
    2. Set MYSQL_PASSWORD below.
    3. Run: python construction_labour_management.py
       Web dashboard: http://127.0.0.1:5000

Optional Tkinter desktop view:
    python construction_labour_management.py --desktop

Both interfaces use the same MySQL database.
"""

import sys
from datetime import date, datetime
from flask import Flask, request, redirect, url_for, flash, render_template_string
import mysql.connector
from mysql.connector import Error

# -------------------- MYSQL CONFIGURATION --------------------

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "YOUR_MYSQL_PASSWORD"
DATABASE_NAME = "construction_labour_db"

app = Flask(__name__)
app.secret_key = "ConstructionLabourApp_2026_SecureKey"

# -------------------- DATABASE SETUP --------------------

def server_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD
    )


def get_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=DATABASE_NAME
    )


def setup_database():
    conn = server_connection()
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}")
    cursor.close()
    conn.close()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labourers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            labour_name VARCHAR(100) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            labour_type VARCHAR(60) NOT NULL,
            daily_wage DECIMAL(10,2) NOT NULL,
            joining_date DATE NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            labour_id INT NOT NULL,
            attendance_date DATE NOT NULL,
            attendance_status VARCHAR(20) NOT NULL DEFAULT 'Present',
            overtime_hours DECIMAL(5,2) NOT NULL DEFAULT 0,
            remarks VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_labour_day (labour_id, attendance_date),
            FOREIGN KEY (labour_id) REFERENCES labourers(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wage_payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            labour_id INT NOT NULL,
            wage_month CHAR(7) NOT NULL,
            amount_paid DECIMAL(10,2) NOT NULL,
            payment_date DATE NOT NULL,
            remarks VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_labour_month (labour_id, wage_month),
            FOREIGN KEY (labour_id) REFERENCES labourers(id)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


# -------------------- DASHBOARD HTML + CSS --------------------

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BuildTrack | Labour Management Dashboard</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*{box-sizing:border-box}
body{margin:0;background:#081326;color:#edf3ff;font-family:Inter,Arial,sans-serif;font-size:14px}
.shell{display:flex;min-height:100vh}
.sidebar{width:235px;min-width:235px;background:#0c192d;border-right:1px solid #203451;padding:25px 14px;display:flex;flex-direction:column}
.brand{display:flex;gap:12px;align-items:center;padding:0 8px 35px}
.brand-icon{font-size:30px}.brand b{font-size:19px}
.brand small,.admin small{display:block;color:#91a5c6;font-size:10px;margin-top:5px}
nav{display:grid;gap:9px}
nav a{color:#c5d3eb;text-decoration:none;padding:13px;border-radius:9px;font-weight:600}
nav a:hover,nav a.active{background:#234bc0;color:white}
.side-note{margin-top:auto;text-align:center;border:1px solid #203451;border-radius:12px;padding:20px 12px;line-height:1.6}
.side-note div{font-size:28px}.side-note p{font-size:12px;color:#91a5c6}
main{width:calc(100% - 235px);max-width:1600px;padding:25px 28px;margin:auto}
header,.welcome,.panel-title{display:flex;justify-content:space-between;align-items:center}
header{border-bottom:1px solid #203451;padding-bottom:18px}
header small{display:block;color:#91a5c6;letter-spacing:2px}
header h1{font-size:23px;margin:5px 0}.admin{text-align:right}
.welcome{padding:22px 0}.welcome h2{margin:0 0 7px;font-size:21px}
.welcome p,.muted{color:#91a5c6}.welcome p{margin:0}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:20px}
.stat{border-radius:12px;padding:20px;min-height:120px;display:flex;align-items:center;gap:15px}
.stat-icon{font-size:26px;background:#ffffff25;border-radius:50%;width:50px;height:50px;display:grid;place-items:center}
.stat p{margin:0 0 8px}.stat strong{font-size:27px}.stat small{display:block;margin-top:7px}
.purple{background:linear-gradient(120deg,#713ff0,#542bd2)}
.green{background:linear-gradient(120deg,#0da77f,#087e70)}
.blue{background:linear-gradient(120deg,#2387ed,#1458cb)}
.orange{background:linear-gradient(120deg,#ee922d,#d65c1d)}
.grid{display:grid;grid-template-columns:1.2fr 1fr;gap:18px}
.lower{margin-top:18px}
.panel{background:#101f37;border:1px solid #203451;border-radius:12px;padding:18px;min-width:0}
.panel-title{margin-bottom:17px}.panel-title h3{font-size:15px;margin:0}
.site{position:relative;display:grid;grid-template-columns:1fr 95px;gap:10px;min-height:285px;padding:17px;border:1px solid #31496d;border-radius:8px;background:#09172b}
.worker-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;align-content:center}
.worker{min-height:65px;border-radius:9px;display:flex;flex-direction:column;justify-content:center;align-items:center;color:white;text-align:center;padding:5px}
.worker.present{background:#0fae82}.worker.absent{background:#e64e5c}.worker.half{background:#efa92e;color:#17243b}
.worker small{font-size:9px;margin-top:4px}
.site-office{border:1px solid #2c4263;border-radius:8px;display:grid;place-items:center;color:#8ea6ca;font-weight:700;text-align:center}
.entrance{position:absolute;bottom:-8px;left:42%;background:#101f37;padding:0 12px;color:#91a5c6;font-size:10px}
.booking{display:grid;grid-template-columns:78px 1fr 90px;gap:8px;align-items:center;padding:13px 0;border-bottom:1px solid #203451;font-size:11px}
.booking:last-child{border:0}.booking small{display:block;color:#91a5c6;margin-top:5px}
.time{background:#ffb632;color:#17243b;border-radius:20px;padding:8px 4px;text-align:center;font-weight:700}
select,input{width:100%;padding:9px;border:1px solid #31496b;border-radius:7px;background:#0b1930;color:white}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:13px}
.form-grid label{font-size:11px;color:#a9bbd7}
.form-grid input,.form-grid select{display:block;margin-top:6px}
.form-grid button{grid-column:1/-1;padding:13px;background:#2864f0;color:white;border:0;border-radius:7px;font-weight:700;cursor:pointer}
.quick{display:flex;flex-direction:column;gap:11px}
.quick a{padding:17px;text-align:center;text-decoration:none;color:white;background:#245fe7;border-radius:8px;font-weight:700}
.quick a:nth-of-type(2){background:#078c75}.quick a:nth-of-type(3){background:#6841dc}
.quick p{text-align:center;color:#8299bd;font-size:11px;margin-top:auto;padding-top:15px}
.alert{padding:11px;border-radius:7px}.alert.success{background:#0d654e}.alert.error{background:#7b2b38}
@media(max-width:1100px){.stats{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}}
@media(max-width:700px){.sidebar{width:175px;min-width:175px;padding:15px 8px}.brand{padding-bottom:22px}.brand-icon{font-size:23px}.brand b{font-size:15px}.brand small{font-size:9px}.side-note{display:none}
nav a{font-size:11px;padding:11px 8px}main{width:calc(100% - 175px);padding:14px 10px}
.stats{grid-template-columns:1fr}.booking{grid-template-columns:1fr 1fr}.form-grid{grid-template-columns:1fr}
.site{grid-template-columns:1fr 65px}.worker-grid{gap:7px}}
</style>
</head>
<body>
<div class="shell">
<aside class="sidebar">
 <div class="brand"><span class="brand-icon">🏗️</span><div><b>BuildTrack</b><small>Workforce • Wages • Progress</small></div></div>
 <nav>
  <a class="{{ 'active' if active_page == 'dashboard' else '' }}" href="{{ url_for('dashboard') }}">▦ &nbsp; Dashboard</a>
  <a class="{{ 'active' if active_page == 'labourers' else '' }}" href="{{ url_for('labourers_page') }}">♟ &nbsp; Labourers</a>
  <a class="{{ 'active' if active_page == 'attendance' else '' }}" href="{{ url_for('attendance_page') }}">▣ &nbsp; Attendance</a>
  <a class="{{ 'active' if active_page == 'wages' else '' }}" href="{{ url_for('wages_page') }}">₹ &nbsp; Wages & Payments</a>
 </nav>
 <div class="side-note"><div>👷</div><b>Smarter Site<br>Management</b><p>Manage workers, daily attendance and wage calculations in one place.</p></div>
</aside>
<main>
<header><div><small>CONSTRUCTION MANAGEMENT</small><h1>Dashboard</h1></div><div class="admin">● &nbsp; Admin<small>Site Manager</small></div></header>
<section class="welcome"><div><h2>Welcome Back, Admin! 👋</h2><p>Here's the workforce summary for your construction site.</p></div><span>📅 &nbsp; {{ today }}</span></section>
{% with messages = get_flashed_messages(with_categories=true) %}
{% if messages %}{% for category,message in messages %}<p class="alert {{ category }}">{{ message }}</p>{% endfor %}{% endif %}{% endwith %}
<section class="stats">
 <article class="stat purple"><span class="stat-icon">♟</span><div><p>Total Labourers</p><strong>{{ total_labourers }}</strong><small>Registered workers</small></div></article>
 <article class="stat green"><span class="stat-icon">✓</span><div><p>Present Today</p><strong>{{ present_today }}</strong><small>Full-day attendance</small></div></article>
 <article class="stat blue"><span class="stat-icon">◷</span><div><p>Attendance Today</p><strong>{{ attendance_today }}</strong><small>Attendance entries</small></div></article>
 <article class="stat orange"><span class="stat-icon">₹</span><div><p>Today's Wage Estimate</p><strong>₹{{ today_wages }}</strong><small>Based on attendance</small></div></article>
</section>
<section class="grid">
 <article class="panel"><div class="panel-title"><h3>👷 &nbsp; Today's Site Attendance</h3><div class="muted">🟢 Present &nbsp; 🔴 Absent &nbsp; 🟠 Half Day</div></div>
  <div class="site"><div class="worker-grid">
  {% for item in today_workers %}<div class="worker {% if item.attendance_status == 'Present' %}present{% elif item.attendance_status == 'Half Day' %}half{% else %}absent{% endif %}"><b>{{ item.labour_name }}</b><small>{{ item.attendance_status }}</small></div>{% endfor %}
  {% if not today_workers %}<p class="muted">No attendance marked for today.</p>{% endif %}
  </div><div class="site-office">SITE<br>OFFICE</div><div class="entrance">SITE ENTRANCE</div></div>
 </article>
 <article class="panel"><div class="panel-title"><h3>▣ &nbsp; Recent Attendance</h3></div>
 {% if recent_attendance %}{% for item in recent_attendance %}
 <div class="booking"><span class="time">{{ item.display_date }}</span><div><b>{{ item.labour_name }}</b><small>{{ item.labour_type }}</small></div><div>{{ item.attendance_status }}<small>₹{{ item.calculated_wage }}</small></div></div>
 {% endfor %}{% else %}<p class="muted">No attendance records yet.</p>{% endif %}
 </article>
</section>
<section class="grid lower">
 <article class="panel"><div class="panel-title"><h3>＋ &nbsp; Register New Labourer</h3></div>
 <form class="form-grid" method="POST" action="{{ url_for('add_labourer') }}">
  <label>Labourer name<input name="labour_name" placeholder="e.g. Ramesh Patil" required></label>
  <label>Phone number<input name="phone" type="tel" placeholder="Phone number" required></label>
  <label>Work category<input name="labour_type" placeholder="e.g. Mason / Helper" required></label>
  <label>Daily wage (₹)<input name="daily_wage" type="number" min="1" step="0.01" required></label>
  <label>Joining date<input name="joining_date" type="date" value="{{ today_iso }}" required></label>
  <button type="submit">＋ Register Labourer</button>
 </form></article>
 <article class="panel quick"><div class="panel-title"><h3>⚡ &nbsp; Quick Actions</h3></div><a href="{{ url_for('attendance_page') }}">＋ &nbsp; Mark Attendance</a><a href="{{ url_for('labourers_page') }}">♟ &nbsp; Manage Labourers</a><a href="{{ url_for('wages_page') }}">₹ &nbsp; View Wage Report</a><p>Accurate Attendance • Transparent Wages • Better Sites</p></article>
</section>
</main></div>
</body></html>
"""

# -------------------- COMMON MANAGEMENT PAGE HTML + CSS --------------------

MANAGEMENT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BuildTrack | {{ page_title }}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*{box-sizing:border-box}body{margin:0;background:#081326;color:#edf3ff;font-family:Inter,Arial,sans-serif;font-size:14px}
.shell{display:flex;min-height:100vh}.sidebar{width:235px;min-width:235px;background:#0c192d;border-right:1px solid #203451;padding:25px 14px;display:flex;flex-direction:column}
.brand{display:flex;gap:12px;align-items:center;padding:0 8px 35px}.brand-icon{font-size:30px}.brand b{font-size:19px}.brand small,.admin small{display:block;color:#91a5c6;font-size:10px;margin-top:5px}
nav{display:grid;gap:9px}nav a{color:#c5d3eb;text-decoration:none;padding:13px;border-radius:9px;font-weight:600}nav a:hover,nav a.active{background:#234bc0;color:white}
.side-note{margin-top:auto;text-align:center;border:1px solid #203451;border-radius:12px;padding:20px 12px;line-height:1.6}.side-note div{font-size:28px}.side-note p{font-size:12px;color:#91a5c6}
main{width:calc(100% - 235px);max-width:1500px;padding:25px 28px;margin:auto}header{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #203451;padding-bottom:18px}header small{display:block;color:#91a5c6;letter-spacing:2px}header h1{font-size:23px;margin:5px 0}.admin{text-align:right}
.panel{background:#101f37;border:1px solid #203451;border-radius:12px;padding:20px;margin-top:22px;overflow-x:auto}.muted{color:#91a5c6}.alert{padding:11px;border-radius:7px}.alert.success{background:#0d654e}.alert.error{background:#7b2b38}
table{width:100%;border-collapse:collapse;min-width:760px}th,td{text-align:left;padding:13px 10px;border-bottom:1px solid #203451}th{color:#91a5c6;font-size:12px}td{font-size:13px}
select,input{width:100%;padding:9px;border:1px solid #31496b;border-radius:7px;background:#0b1930;color:white}
button{padding:10px 14px;border:0;border-radius:7px;background:#2864f0;color:white;font-weight:700;cursor:pointer}button:hover{filter:brightness(1.12)}
.status-form{display:flex;gap:7px;min-width:180px}.status-form select{min-width:115px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px}.item-card{background:#0b1930;border:1px solid #31496b;border-radius:10px;padding:16px}.item-card h3{margin:0 0 7px}.item-card p{color:#91a5c6;margin:5px 0 12px}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.form-grid label{color:#a9bbd7;font-size:12px}.form-grid input,.form-grid select{display:block;margin-top:6px}.form-grid button{grid-column:1/-1;padding:13px}
.inline-form{display:flex;gap:8px;align-items:center;min-width:200px}.inline-form select{min-width:110px}
.toolbar{display:flex;gap:12px;align-items:end;flex-wrap:wrap;margin-bottom:18px}.toolbar label{color:#a9bbd7;font-size:12px}.toolbar input{display:block;margin-top:6px}
@media(max-width:700px){.sidebar{width:175px;min-width:175px;padding:15px 8px}.brand{padding-bottom:22px}.brand-icon{font-size:23px}.brand b{font-size:15px}.brand small{font-size:9px}.side-note{display:none}nav a{font-size:11px;padding:11px 8px}main{width:calc(100% - 175px);padding:14px 10px}.form-grid{grid-template-columns:1fr}}
</style></head><body><div class="shell"><aside class="sidebar">
<div class="brand"><span class="brand-icon">🏗️</span><div><b>BuildTrack</b><small>Workforce • Wages • Progress</small></div></div>
<nav>
<a class="{{ 'active' if active_page == 'dashboard' else '' }}" href="{{ url_for('dashboard') }}">▦ &nbsp; Dashboard</a>
<a class="{{ 'active' if active_page == 'labourers' else '' }}" href="{{ url_for('labourers_page') }}">♟ &nbsp; Labourers</a>
<a class="{{ 'active' if active_page == 'attendance' else '' }}" href="{{ url_for('attendance_page') }}">▣ &nbsp; Attendance</a>
<a class="{{ 'active' if active_page == 'wages' else '' }}" href="{{ url_for('wages_page') }}">₹ &nbsp; Wages & Payments</a>
</nav><div class="side-note"><div>👷</div><b>Smarter Site<br>Management</b><p>Manage workers, daily attendance and wage calculations in one place.</p></div>
</aside><main><header><div><small>CONSTRUCTION MANAGEMENT</small><h1>{{ page_title }}</h1></div><div class="admin">● &nbsp; Admin<small>Site Manager</small></div></header>
{% with messages = get_flashed_messages(with_categories=true) %}{% if messages %}{% for category,message in messages %}<p class="alert {{ category }}">{{ message }}</p>{% endfor %}{% endif %}{% endwith %}
{{ page_content|safe }}
</main></div></body></html>
"""


def render_management(page_title, page_content, active_page):
    return render_template_string(
        MANAGEMENT_HTML, page_title=page_title,
        page_content=page_content, active_page=active_page
    )


# -------------------- FLASK DASHBOARD ROUTE --------------------

@app.route("/")
def dashboard():
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT COUNT(*) AS total FROM labourers WHERE status='Active'")
        total_labourers = cur.fetchone()["total"]

        cur.execute("""
            SELECT COUNT(*) AS total FROM attendance
            WHERE attendance_date=CURDATE() AND attendance_status='Present'
        """)
        present_today = cur.fetchone()["total"]

        cur.execute("SELECT COUNT(*) AS total FROM attendance WHERE attendance_date=CURDATE()")
        attendance_today = cur.fetchone()["total"]

        cur.execute("""
            SELECT COALESCE(SUM(
                CASE a.attendance_status
                    WHEN 'Present' THEN l.daily_wage
                    WHEN 'Half Day' THEN l.daily_wage / 2
                    ELSE 0
                END + (a.overtime_hours * (l.daily_wage / 8))
            ),0) AS total
            FROM attendance a JOIN labourers l ON a.labour_id=l.id
            WHERE a.attendance_date=CURDATE()
        """)
        today_wages = float(cur.fetchone()["total"] or 0)

        cur.execute("""
            SELECT l.labour_name, a.attendance_status,
                   CASE WHEN a.attendance_status='Present' THEN l.daily_wage
                        WHEN a.attendance_status='Half Day' THEN l.daily_wage/2
                        ELSE 0 END + (a.overtime_hours*(l.daily_wage/8)) AS calculated_wage
            FROM attendance a JOIN labourers l ON a.labour_id=l.id
            WHERE a.attendance_date=CURDATE()
            ORDER BY l.labour_name LIMIT 16
        """)
        today_workers = cur.fetchall()

        cur.execute("""
            SELECT l.labour_name,l.labour_type,a.attendance_status,
                   DATE_FORMAT(a.attendance_date,'%d %b') AS display_date,
                   CASE WHEN a.attendance_status='Present' THEN l.daily_wage
                        WHEN a.attendance_status='Half Day' THEN l.daily_wage/2
                        ELSE 0 END + (a.overtime_hours*(l.daily_wage/8)) AS calculated_wage
            FROM attendance a JOIN labourers l ON a.labour_id=l.id
            ORDER BY a.attendance_date DESC,a.id DESC LIMIT 6
        """)
        recent_attendance = cur.fetchall()

        cur.close()
        conn.close()

        return render_template_string(
            DASHBOARD_HTML,
            total_labourers=total_labourers,
            present_today=present_today,
            attendance_today=attendance_today,
            today_wages=f"{today_wages:,.2f}",
            today_workers=today_workers,
            recent_attendance=recent_attendance,
            today=date.today().strftime("%d %b %Y"),
            today_iso=date.today().isoformat(),
            active_page="dashboard"
        )
    except Error as error:
        return (
            "<h2>Database connection error</h2>"
            "<p>Check MySQL is running and your password is correct in this file.</p>"
            f"<pre>{error}</pre>", 500
        )


# -------------------- LABOURER MANAGEMENT --------------------

@app.route("/labourers")
def labourers_page():
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT id,labour_name,phone,labour_type,daily_wage,joining_date,status
            FROM labourers ORDER BY id DESC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        content = render_template_string("""
        <section class="panel"><h2>Labourer Records</h2>
        <p class="muted">View registered workers and update their employment status.</p>
        {% if rows %}<table><thead><tr><th>ID</th><th>Name</th><th>Phone</th><th>Work Category</th><th>Daily Wage</th><th>Joining Date</th><th>Status</th><th>Action</th></tr></thead><tbody>
        {% for r in rows %}<tr><td>#{{ r.id }}</td><td>{{ r.labour_name }}</td><td>{{ r.phone }}</td><td>{{ r.labour_type }}</td><td>₹{{ r.daily_wage }}</td><td>{{ r.joining_date }}</td><td>{{ r.status }}</td>
        <td><form class="inline-form" method="POST" action="{{ url_for('update_labourer_status', labour_id=r.id) }}"><select name="status">{% for st in ['Active','Inactive'] %}<option value="{{ st }}" {% if r.status==st %}selected{% endif %}>{{ st }}</option>{% endfor %}</select><button>Save</button></form></td></tr>{% endfor %}
        </tbody></table>{% else %}<p class="muted">No labourers registered yet.</p>{% endif %}</section>
        """, rows=rows)
        return render_management("Labourer Management", content, "labourers")
    except Error as error:
        return f"<h2>Database error</h2><pre>{error}</pre>", 500


@app.route("/labourer/add", methods=["POST"])
def add_labourer():
    name = request.form.get("labour_name", "").strip()
    phone = request.form.get("phone", "").strip()
    labour_type = request.form.get("labour_type", "").strip()
    joining_date = request.form.get("joining_date")
    daily_wage = request.form.get("daily_wage", type=float)

    if not all([name, phone, labour_type, joining_date]) or not daily_wage or daily_wage <= 0:
        flash("Please enter valid details in every field.", "error")
        return redirect(url_for("dashboard"))

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO labourers (labour_name,phone,labour_type,daily_wage,joining_date)
            VALUES (%s,%s,%s,%s,%s)
        """, (name, phone, labour_type, daily_wage, joining_date))
        conn.commit()
        flash("Labourer registered successfully!", "success")
    except Error as error:
        conn.rollback()
        flash("Database error: " + str(error), "error")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("dashboard"))


@app.route("/labourer/<int:labour_id>/status", methods=["POST"])
def update_labourer_status(labour_id):
    status = request.form.get("status")
    if status not in {"Active", "Inactive"}:
        flash("Invalid labourer status.", "error")
        return redirect(url_for("labourers_page"))
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE labourers SET status=%s WHERE id=%s", (status, labour_id))
        conn.commit()
        flash("Labourer status updated successfully.", "success")
    except Error as error:
        conn.rollback()
        flash("Database error: " + str(error), "error")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("labourers_page"))


# -------------------- ATTENDANCE MANAGEMENT --------------------

@app.route("/attendance")
def attendance_page():
    selected_date = request.args.get("attendance_date") or date.today().isoformat()
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT l.id,l.labour_name,l.labour_type,l.daily_wage,
                   a.id AS attendance_id,a.attendance_status,a.overtime_hours,a.remarks
            FROM labourers l
            LEFT JOIN attendance a ON l.id=a.labour_id AND a.attendance_date=%s
            WHERE l.status='Active' ORDER BY l.labour_name
        """, (selected_date,))
        rows = cur.fetchall()

        cur.execute("""
            SELECT a.id,l.labour_name,a.attendance_status,a.overtime_hours,a.remarks
            FROM attendance a JOIN labourers l ON a.labour_id=l.id
            WHERE a.attendance_date=%s ORDER BY l.labour_name
        """, (selected_date,))
        marked = cur.fetchall()
        cur.close()
        conn.close()

        content = render_template_string("""
        <section class="panel"><h2>Daily Attendance Register</h2>
        <p class="muted">Select a date and mark each active labourer's attendance.</p>
        <form class="toolbar" method="GET"><label>Attendance date<input type="date" name="attendance_date" value="{{ selected_date }}" required></label><button>View Date</button></form>
        {% if rows %}<table><thead><tr><th>Labourer</th><th>Work Category</th><th>Daily Wage</th><th>Attendance</th><th>Overtime Hours</th><th>Remarks</th><th>Action</th></tr></thead><tbody>
        {% for r in rows %}<form id="attendance-{{ r.id }}" method="POST" action="{{ url_for('mark_attendance') }}"></form>
        <tr><input form="attendance-{{ r.id }}" type="hidden" name="labour_id" value="{{ r.id }}"><input form="attendance-{{ r.id }}" type="hidden" name="attendance_date" value="{{ selected_date }}">
        <td>{{ r.labour_name }}</td><td>{{ r.labour_type }}</td><td>₹{{ r.daily_wage }}</td>
        <td><select form="attendance-{{ r.id }}" name="attendance_status">{% for st in ['Present','Half Day','Absent'] %}<option value="{{ st }}" {% if r.attendance_status==st or (not r.attendance_status and st=='Present') %}selected{% endif %}>{{ st }}</option>{% endfor %}</select></td>
        <td><input form="attendance-{{ r.id }}" type="number" name="overtime_hours" min="0" max="12" step="0.5" value="{{ r.overtime_hours or 0 }}"></td>
        <td><input form="attendance-{{ r.id }}" name="remarks" value="{{ r.remarks or '' }}" placeholder="Optional"></td><td><button form="attendance-{{ r.id }}" type="submit">Save</button></td>
        </tr>{% endfor %}</tbody></table>{% else %}<p class="muted">Register labourers before marking attendance.</p>{% endif %}
        </section>
        <section class="panel"><h2>Attendance Summary — {{ selected_date }}</h2>
        {% if marked %}<table><thead><tr><th>Labourer</th><th>Status</th><th>Overtime</th><th>Remarks</th></tr></thead><tbody>
        {% for r in marked %}<tr><td>{{ r.labour_name }}</td><td>{{ r.attendance_status }}</td><td>{{ r.overtime_hours }}</td><td>{{ r.remarks or '-' }}</td></tr>{% endfor %}
        </tbody></table>{% else %}<p class="muted">No attendance has been saved for this date.</p>{% endif %}</section>
        """, rows=rows, marked=marked, selected_date=selected_date)
        return render_management("Attendance Management", content, "attendance")
    except Error as error:
        return f"<h2>Database error</h2><pre>{error}</pre>", 500


@app.route("/attendance/mark", methods=["POST"])
def mark_attendance():
    labour_id = request.form.get("labour_id", type=int)
    attendance_date = request.form.get("attendance_date")
    attendance_status = request.form.get("attendance_status")
    overtime_hours = request.form.get("overtime_hours", type=float) or 0
    remarks = request.form.get("remarks", "").strip()

    if (not labour_id or not attendance_date or
            attendance_status not in {"Present", "Half Day", "Absent"} or
            overtime_hours < 0 or overtime_hours > 12):
        flash("Please provide valid attendance details.", "error")
        return redirect(url_for("attendance_page"))

    if attendance_status == "Absent":
        overtime_hours = 0

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO attendance
                (labour_id,attendance_date,attendance_status,overtime_hours,remarks)
            VALUES (%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                attendance_status=VALUES(attendance_status),
                overtime_hours=VALUES(overtime_hours),
                remarks=VALUES(remarks)
        """, (labour_id, attendance_date, attendance_status, overtime_hours, remarks))
        conn.commit()
        flash("Attendance saved successfully.", "success")
    except Error as error:
        conn.rollback()
        flash("Database error: " + str(error), "error")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("attendance_page", attendance_date=attendance_date))


# -------------------- WAGE CALCULATION AND PAYMENT --------------------

@app.route("/wages")
def wages_page():
    wage_month = request.args.get("wage_month") or date.today().strftime("%Y-%m")
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT l.id,l.labour_name,l.labour_type,l.daily_wage,
                   COALESCE(SUM(CASE
                       WHEN a.attendance_status='Present' THEN 1
                       WHEN a.attendance_status='Half Day' THEN 0.5
                       ELSE 0 END),0) AS payable_days,
                   COALESCE(SUM(a.overtime_hours),0) AS overtime_hours,
                   COALESCE(SUM(CASE
                       WHEN a.attendance_status='Present' THEN l.daily_wage
                       WHEN a.attendance_status='Half Day' THEN l.daily_wage/2
                       ELSE 0 END + (a.overtime_hours*(l.daily_wage/8))),0) AS gross_wage,
                   COALESCE(p.amount_paid,0) AS amount_paid,
                   p.payment_date
            FROM labourers l
            LEFT JOIN attendance a ON l.id=a.labour_id
                AND DATE_FORMAT(a.attendance_date,'%Y-%m')=%s
            LEFT JOIN wage_payments p ON l.id=p.labour_id AND p.wage_month=%s
            WHERE l.status='Active'
            GROUP BY l.id,l.labour_name,l.labour_type,l.daily_wage,p.amount_paid,p.payment_date
            ORDER BY l.labour_name
        """, (wage_month, wage_month))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        for row in rows:
            row["gross_wage"] = float(row["gross_wage"] or 0)
            row["amount_paid"] = float(row["amount_paid"] or 0)
            row["balance"] = max(0, row["gross_wage"] - row["amount_paid"])

        total_wages = sum(r["gross_wage"] for r in rows)
        total_paid = sum(r["amount_paid"] for r in rows)
        total_balance = sum(r["balance"] for r in rows)

        content = render_template_string("""
        <section class="panel"><h2>Monthly Wage Calculation</h2>
        <p class="muted">Wages are calculated from attendance records for the selected month.</p>
        <form class="toolbar" method="GET"><label>Select month<input type="month" name="wage_month" value="{{ wage_month }}" required></label><button>Generate Report</button></form>
        <div class="cards">
          <article class="item-card"><p>Total Calculated Wages</p><h2>₹{{ '%.2f'|format(total_wages) }}</h2></article>
          <article class="item-card"><p>Total Paid</p><h2>₹{{ '%.2f'|format(total_paid) }}</h2></article>
          <article class="item-card"><p>Outstanding Balance</p><h2>₹{{ '%.2f'|format(total_balance) }}</h2></article>
        </div>
        {% if rows %}<table style="margin-top:20px"><thead><tr><th>Labourer</th><th>Category</th><th>Daily Wage</th><th>Payable Days</th><th>Overtime Hours</th><th>Gross Wage</th><th>Paid</th><th>Balance</th><th>Payment</th></tr></thead><tbody>
        {% for r in rows %}<tr><td>{{ r.labour_name }}</td><td>{{ r.labour_type }}</td><td>₹{{ r.daily_wage }}</td><td>{{ r.payable_days }}</td><td>{{ r.overtime_hours }}</td><td>₹{{ '%.2f'|format(r.gross_wage) }}</td><td>₹{{ '%.2f'|format(r.amount_paid) }}</td><td>₹{{ '%.2f'|format(r.balance) }}</td><td>
        {% if r.balance > 0 %}<form class="inline-form" method="POST" action="{{ url_for('record_payment') }}"><input type="hidden" name="labour_id" value="{{ r.id }}"><input type="hidden" name="wage_month" value="{{ wage_month }}"><input type="number" name="amount_paid" min="0.01" max="{{ '%.2f'|format(r.balance) }}" step="0.01" placeholder="Amount" required><button>Pay</button></form>{% else %}<span>Settled</span>{% endif %}
        </td></tr>{% endfor %}
        </tbody></table>{% else %}<p class="muted">No active labourers found.</p>{% endif %}
        <p class="muted">Calculation: Present = 1 daily wage; Half Day = 0.5 daily wage; Absent = 0. Overtime = daily wage ÷ 8 × overtime hours.</p>
        </section>
        """, rows=rows, wage_month=wage_month, total_wages=total_wages,
             total_paid=total_paid, total_balance=total_balance)
        return render_management("Wages & Payments", content, "wages")
    except Error as error:
        return f"<h2>Database error</h2><pre>{error}</pre>", 500


@app.route("/wages/payment", methods=["POST"])
def record_payment():
    labour_id = request.form.get("labour_id", type=int)
    wage_month = request.form.get("wage_month")
    amount_paid = request.form.get("amount_paid", type=float)

    if not labour_id or not wage_month or not amount_paid or amount_paid <= 0:
        flash("Enter a valid payment amount.", "error")
        return redirect(url_for("wages_page", wage_month=wage_month))

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT l.daily_wage,
                   COALESCE(SUM(CASE
                       WHEN a.attendance_status='Present' THEN l.daily_wage
                       WHEN a.attendance_status='Half Day' THEN l.daily_wage/2
                       ELSE 0 END + (a.overtime_hours*(l.daily_wage/8))),0) AS gross_wage
            FROM labourers l LEFT JOIN attendance a ON l.id=a.labour_id
                AND DATE_FORMAT(a.attendance_date,'%Y-%m')=%s
            WHERE l.id=%s GROUP BY l.id,l.daily_wage
        """, (wage_month, labour_id))
        wage_row = cur.fetchone()
        if not wage_row:
            flash("Labourer record was not found.", "error")
            return redirect(url_for("wages_page", wage_month=wage_month))

        cur.execute("""
            SELECT amount_paid FROM wage_payments
            WHERE labour_id=%s AND wage_month=%s
        """, (labour_id, wage_month))
        existing = cur.fetchone()
        already_paid = float(existing["amount_paid"]) if existing else 0
        balance = float(wage_row["gross_wage"]) - already_paid

        if amount_paid > balance + 0.001:
            flash("Payment cannot be greater than the outstanding wage balance.", "error")
            return redirect(url_for("wages_page", wage_month=wage_month))

        if existing:
            cur.execute("""
                UPDATE wage_payments
                SET amount_paid=amount_paid+%s,payment_date=%s
                WHERE labour_id=%s AND wage_month=%s
            """, (amount_paid, date.today(), labour_id, wage_month))
        else:
            cur.execute("""
                INSERT INTO wage_payments (labour_id,wage_month,amount_paid,payment_date)
                VALUES (%s,%s,%s,%s)
            """, (labour_id, wage_month, amount_paid, date.today()))
        conn.commit()
        flash("Wage payment recorded successfully.", "success")
    except Error as error:
        conn.rollback()
        flash("Database error: " + str(error), "error")
    finally:
        cur.close()
        conn.close()
    return redirect(url_for("wages_page", wage_month=wage_month))


# -------------------- OPTIONAL TKINTER DESKTOP MODE --------------------

def run_tkinter():
    import tkinter as tk
    from tkinter import ttk, messagebox

    class LabourDesktop:
        def __init__(self, root):
            self.root = root
            root.title("BuildTrack - Labour Attendance Admin")
            root.geometry("1050x620")
            root.configure(bg="#0b172a")

            tk.Label(
                root, text="BuildTrack | Labour Attendance & Wages",
                font=("Arial", 20, "bold"), bg="#0b172a", fg="white"
            ).pack(pady=15)

            columns = ("id", "name", "phone", "category", "wage", "date", "status")
            self.tree = ttk.Treeview(root, columns=columns, show="headings", height=17)
            headings = ["ID", "Labourer", "Phone", "Work Category", "Daily Wage", "Joining Date", "Status"]
            widths = [55, 170, 120, 150, 100, 120, 100]

            for col, heading, width in zip(columns, headings, widths):
                self.tree.heading(col, text=heading)
                self.tree.column(col, width=width, anchor="center")

            self.tree.pack(fill="both", expand=True, padx=18, pady=10)

            controls = tk.Frame(root, bg="#0b172a")
            controls.pack(pady=10)
            ttk.Button(controls, text="Refresh", command=self.load_data).pack(side="left", padx=6)
            ttk.Button(
                controls, text="Mark Selected Present Today",
                command=self.mark_selected_present
            ).pack(side="left", padx=6)

            self.load_data()

        def load_data(self):
            for row in self.tree.get_children():
                self.tree.delete(row)
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT id,labour_name,phone,labour_type,daily_wage,joining_date,status
                    FROM labourers ORDER BY labour_name
                """)
                for row in cur.fetchall():
                    self.tree.insert("", "end", values=row)
                cur.close()
                conn.close()
            except Error as error:
                messagebox.showerror("Database error", str(error))

        def mark_selected_present(self):
            selected = self.tree.selection()
            if not selected:
                messagebox.showinfo("Select labourer", "Please select a labourer first.")
                return
            labour_id = self.tree.item(selected[0], "values")[0]
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO attendance (labour_id,attendance_date,attendance_status)
                    VALUES (%s,%s,'Present')
                    ON DUPLICATE KEY UPDATE attendance_status='Present'
                """, (labour_id, date.today()))
                conn.commit()
                cur.close()
                conn.close()
                messagebox.showinfo("Updated", "Labourer marked Present for today.")
            except Error as error:
                messagebox.showerror("Database error", str(error))

    root = tk.Tk()
    LabourDesktop(root)
    root.mainloop()


# -------------------- START PROGRAM --------------------

if __name__ == "__main__":
    try:
        setup_database()
        print("MySQL database and tables are ready.")
        if "--desktop" in sys.argv:
            run_tkinter()
        else:
            print("Starting Flask dashboard at http://127.0.0.1:5000")
            app.run(debug=True)
    except Error as error:
        print("Could not connect to MySQL.")
        print("Check MYSQL_PASSWORD, MYSQL_USER and make sure MySQL Server is running.")
        print("Details:", error)
