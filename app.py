from flask import Flask, render_template, request, redirect, session
import sqlite3
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "secret_key"


def get_db():
    return sqlite3.connect("database.db")


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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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


def predict_delay(case_type, total):
    if total >= 3 or case_type.lower() == "criminal":
        return "Delayed"
    return "On Time"


# ✅ FULL MULTI-LANGUAGE PROFESSIONAL EMAIL
def send_email(to_email, case_id, judge, date, time, status, next_date, next_time, language):

    lang = language.lower()

    if lang == "hindi":
        subject = "अदालत सुनवाई सूचना"
        body = f"""
प्रिय ग्राहक,

आपकी अदालत की सुनवाई निर्धारित की गई है।

केस आईडी: {case_id}
न्यायाधीश: {judge}

मूल तारीख: {date}
मूल समय: {time}

स्थिति: {status}

नई सुनवाई:
नई तारीख: {next_date}
नया समय: {next_time}

कृपया समय पर उपस्थित रहें।

सादर,
कोर्ट शेड्यूलिंग सिस्टम
"""

    elif lang == "kannada":
        subject = "ನ್ಯಾಯಾಲಯ ವಿಚಾರಣೆ ಮಾಹಿತಿ"
        body = f"""
ಪ್ರಿಯ ಗ್ರಾಹಕರೇ,

ನಿಮ್ಮ ನ್ಯಾಯಾಲಯ ವಿಚಾರಣೆ ನಿಗದಿಯಾಗಿದೆ.

ಕೇಸ್ ಐಡಿ: {case_id}
ನ್ಯಾಯಾಧೀಶ: {judge}

ಮೂಲ ದಿನಾಂಕ: {date}
ಮೂಲ ಸಮಯ: {time}

ಸ್ಥಿತಿ: {status}

ಹೊಸ ವಿಚಾರಣೆ:
ಹೊಸ ದಿನಾಂಕ: {next_date}
ಹೊಸ ಸಮಯ: {next_time}

ದಯವಿಟ್ಟು ಸಮಯಕ್ಕೆ ಬನ್ನಿ.

ಧನ್ಯವಾದಗಳು,
ಕೋರ್ಟ್ ಶೆಡ್ಯೂಲಿಂಗ್ ಸಿಸ್ಟಮ್
"""

    elif lang == "telugu":
        subject = "కోర్టు విచారణ సమాచారం"
        body = f"""
ప్రియమైన వినియోగదారుడు,

మీ కోర్టు విచారణ షెడ్యూల్ చేయబడింది.

కేసు ఐడి: {case_id}
న్యాయమూర్తి: {judge}

మూల తేదీ: {date}
మూల సమయం: {time}

స్థితి: {status}

కొత్త విచారణ:
కొత్త తేదీ: {next_date}
కొత్త సమయం: {next_time}

దయచేసి సమయానికి హాజరుకండి.

ధన్యవాదాలు,
కోర్టు షెడ్యూలింగ్ సిస్టమ్
"""

    elif lang == "tamil":
        subject = "நீதிமன்ற விசாரணை தகவல்"
        body = f"""
அன்பார்ந்த பயனர்,

உங்கள் நீதிமன்ற விசாரணை திட்டமிடப்பட்டுள்ளது.

வழக்கு ஐடி: {case_id}
நீதிபதி: {judge}

மூல தேதி: {date}
மூல நேரம்: {time}

நிலை: {status}

புதிய விசாரணை:
புதிய தேதி: {next_date}
புதிய நேரம்: {next_time}

தயவுசெய்து நேரத்திற்கு வருக.

நன்றி,
நீதிமன்ற திட்ட அமைப்பு
"""

    else:
        subject = "Court Hearing Notification"
        body = f"""
Dear Client,

Your court hearing has been scheduled.

Case ID: {case_id}
Judge: {judge}

Original Date: {date}
Original Time: {time}

Status: {status}

Rescheduled Hearing:
New Date: {next_date}
New Time: {next_time}

Please be present on time.

Regards,
Court Scheduling System
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "Ktejasvitha26@gmail.com"
    msg["To"] = to_email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login("Ktejasvitha26@gmail.com", "lvms irgb fwra yzfu")
    server.send_message(msg)
    server.quit()


@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "1234":
            session["user"] = "admin"
            return redirect("/dashboard")
        return "Invalid Login"
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM hearings")
    hearings = cur.fetchall()
    db.close()

    msg = request.args.get("msg")
    return render_template("dashboard.html", hearings=hearings, msg=msg)


@app.route("/add_case", methods=["GET","POST"])
def add_case():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        db = get_db()
        cur = db.cursor()

        case_id = request.form["case_id"]

        cur.execute("SELECT * FROM cases WHERE case_id=?", (case_id,))
        if cur.fetchone():
            db.close()
            return "Case ID already exists"

        cur.execute("INSERT INTO cases VALUES(?,?,?,?,?)", (
            case_id,
            request.form["case_type"],
            request.form["lawyer_email"],
            request.form["client_email"],
            request.form["language"]
        ))

        db.commit()
        db.close()

        return redirect("/dashboard?msg=case_added")

    return render_template("add_case.html")


@app.route("/schedule", methods=["GET","POST"])
def schedule():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        db = get_db()
        cur = db.cursor()

        case_id = request.form["case_id"]

        cur.execute("SELECT * FROM cases WHERE case_id=?", (case_id,))
        case = cur.fetchone()

        if not case:
            db.close()
            return "Case ID not found"

        case_type = case[1]
        lawyer_email = case[2]
        client_email = case[3]
        language = case[4]

        cur.execute("SELECT COUNT(*) FROM hearings")
        total = cur.fetchone()[0]

        status = predict_delay(case_type, total)

        date = request.form["date"]
        time = request.form["time"]

        next_date = date
        next_time = time

        if status == "Delayed":
            d = datetime.strptime(date, "%Y-%m-%d")
            next_date = (d + timedelta(days=7)).strftime("%Y-%m-%d")

        judge = request.form["judge"]

        cur.execute("""
        INSERT INTO hearings(case_id,judge,hearing_date,hearing_time,status,next_date,next_time)
        VALUES(?,?,?,?,?,?,?)
        """, (
            case_id,
            judge,
            date,
            time,
            status,
            next_date,
            next_time
        ))

        db.commit()
        db.close()

        # SEND EMAILS
        send_email(lawyer_email, case_id, judge, date, time, status, next_date, next_time, language)
        send_email(client_email, case_id, judge, date, time, status, next_date, next_time, language)

        return redirect("/dashboard?msg=hearing_scheduled")

    return render_template("schedule.html")


if __name__ == "__main__":
    create_tables()
    app.run(debug=True)