from flask import Flask, render_template, request, redirect, session
import psycopg2
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import random
import os
import urllib.parse as up

app = Flask(__name__)
app.secret_key = "secret_key"


# ✅ DATABASE CONNECTION (ONLY POSTGRES FOR RENDER)
def get_db():
    up.uses_netloc.append("postgres")
    url = up.urlparse(os.environ.get("DATABASE_URL"))

    return psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )


# ✅ CREATE TABLES
def create_tables():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS cases(
        case_id TEXT PRIMARY KEY,
        case_type TEXT,
        lawyer_email TEXT,
        client_email TEXT,
        language TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS hearings(
        id SERIAL PRIMARY KEY,
        case_id TEXT,
        judge TEXT,
        hearing_date TEXT,
        hearing_time TEXT,
        status TEXT,
        next_date TEXT,
        next_time TEXT
    )
    """)

    db.commit()
    db.close()


# ✅ AI PREDICTION
def predict_delay(case_type, total):
    score = 0

    if case_type.lower() == "criminal":
        score += 3
    else:
        score += 1

    if total > 5:
        score += 3
    elif total > 2:
        score += 2
    else:
        score += 1

    score += random.randint(0, 2)

    return "Delayed" if score >= 6 else "On Time"


# ✅ EMAIL FUNCTION (UNCHANGED)
def send_email(to_email, case_id, judge, date, time, status, next_date, next_time, language):

    if language.lower() == "english":
        if status == "Delayed":
            subject = "Court Hearing Notification"
            body = f"""
Dear Client,

Your court hearing has been scheduled.

Case ID: {case_id}
Judge: {judge}

Original Date: {date}
Original Time: {time}

Status: Delayed

Rescheduled Hearing:
New Date: {next_date}
New Time: {next_time}
"""
        else:
            subject = "Court Hearing Confirmed"
            body = f"""
Dear Client,

Your hearing is CONFIRMED.

Case ID: {case_id}
Judge: {judge}

Date: {date}
Time: {time}

Status: On Time
"""

    elif language.lower() == "telugu":
        subject = "కోర్టు విచారణ సమాచారం"
        body = f"""
కేసు ఐడి: {case_id}
న్యాయమూర్తి: {judge}
తేదీ: {date}
సమయం: {time}
స్థితి: {status}
"""

    elif language.lower() == "hindi":
        subject = "कोर्ट सुनवाई सूचना"
        body = f"""
केस आईडी: {case_id}
जज: {judge}
तारीख: {date}
समय: {time}
स्थिति: {status}
"""

    elif language.lower() == "kannada":
        subject = "ನ್ಯಾಯಾಲಯ ವಿಚಾರಣೆ ಮಾಹಿತಿ"
        body = f"""
ಕೇಸ್ ಐಡಿ: {case_id}
ನ್ಯಾಯಾಧೀಶರು: {judge}
ದಿನಾಂಕ: {date}
ಸಮಯ: {time}
ಸ್ಥಿತಿ: {status}
"""

    else:
        subject = "Court Notification"
        body = f"""
Case ID: {case_id}
Judge: {judge}
Date: {date}
Time: {time}
Status: {status}
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "your_email@gmail.com"
    msg["To"] = to_email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login("Ktejasvitha26@gmail.com", "lvms irgb fwra yzfu")
    server.send_message(msg)
    server.quit()


# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "court_ai_system" and request.form["password"] == "AI@Court9900":
            session["user"] = "admin"
            return redirect("/dashboard")
        return "Invalid Login"
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM hearings")
    hearings = cur.fetchall()
    db.close()

    msg = session.pop("msg", None)
    return render_template("dashboard.html", hearings=hearings, msg=msg)


# DELETE
@app.route("/delete/<int:id>")
def delete(id):
    if "user" not in session:
        return redirect("/")

    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM hearings WHERE id=%s", (id,))
    db.commit()
    db.close()

    session["msg"] = "Deleted successfully"
    return redirect("/dashboard")


# ADD CASE
@app.route("/add_case", methods=["GET", "POST"])
def add_case():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        db = get_db()
        cur = db.cursor()

        case_id = request.form["case_id"]

        cur.execute("SELECT * FROM cases WHERE case_id=%s", (case_id,))
        if cur.fetchone():
            db.close()
            return "Case already exists"

        cur.execute("INSERT INTO cases VALUES(%s,%s,%s,%s,%s)", (
            case_id,
            request.form["case_type"],
            request.form["lawyer_email"],
            request.form["client_email"],
            request.form["language"]
        ))

        db.commit()
        db.close()

        session["msg"] = "Case added"
        return redirect("/dashboard")

    return render_template("add_case.html")


# SCHEDULE
@app.route("/schedule", methods=["GET", "POST"])
def schedule():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        db = get_db()
        cur = db.cursor()

        case_id = request.form["case_id"]
        cur.execute("SELECT * FROM cases WHERE case_id=%s", (case_id,))
        case = cur.fetchone()

        if not case:
            return "Case not found"

        case_type, lawyer_email, client_email, language = case[1:]

        cur.execute("SELECT COUNT(*) FROM hearings")
        total = cur.fetchone()[0]

        status = predict_delay(case_type, total)

        date = request.form["date"]
        time = request.form["time"]
        judge = request.form["judge"]

        next_date = date
        next_time = time

        if status == "Delayed":
            d = datetime.strptime(date, "%Y-%m-%d")
            next_date = (d + timedelta(days=7)).strftime("%Y-%m-%d")

        cur.execute("""
        INSERT INTO hearings(case_id, judge, hearing_date,
        hearing_time, status, next_date, next_time)
        VALUES(%s,%s,%s,%s,%s,%s,%s)
        """, (case_id, judge, date, time, status, next_date, next_time))

        db.commit()
        db.close()

        send_email(lawyer_email, case_id, judge, date, time, status, next_date, next_time, language)
        send_email(client_email, case_id, judge, date, time, status, next_date, next_time, language)

        session["msg"] = "Scheduled successfully"
        return redirect("/dashboard")

    return render_template("schedule.html")
