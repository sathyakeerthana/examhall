from flask import Flask, render_template, request, redirect, url_for, session, render_template_string
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "super_secret_key"  # Change this in production

# Dummy Admin Credentials (Use a secure method in production)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"

# Dataset file (Make sure this exists)
DATASET_FILE = "dataset.csv"

# Ensure dataset file exists
if not os.path.exists(DATASET_FILE):
    df = pd.DataFrame(columns=["Roll Number", "Student Name", "Exam Hall"])
    df.to_csv(DATASET_FILE, index=False)


# ---------------- Login Route (Changed to "/login") ----------------
@app.route("/login", methods=["GET", "POST"])  # Changed from "/"
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials!")

    return render_template("login.html")

@app.route('/exam_timetable')
def exam_timetable():
    return render_template('exam_timetable.html')


# ---------------- Home Route (Changed to "/home") ----------------
@app.route('/')  # Changed from "/"
def home():
    return render_template('main.html')  # Home page


# ---------------- Dashboard Route ----------------
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect(url_for("login"))

    df = pd.read_csv(DATASET_FILE)
    return render_template("dashboard.html", data=df.to_dict(orient="records"))


# ---------------- Edit Data Route ----------------
@app.route("/edit", methods=["POST"])
def edit_data():
    if not session.get("admin"):
        return redirect(url_for("login"))

    data = request.form.to_dict()
    df = pd.read_csv(DATASET_FILE)

    for i, row in df.iterrows():
        if str(row["Roll Number"]) == data["roll_number"]:
            df.at[i, "Student Name"] = data["student_name"]
            df.at[i, "Exam Hall"] = data["exam_hall"]
            df.at[i, "Result"] = data["result"]
            df.to_csv(DATASET_FILE, index=False)
            break

    return redirect(url_for("dashboard"))


# ---------------- Delete Data Route ----------------
@app.route("/delete/<roll_number>")
def delete_data(roll_number):
    if not session.get("admin"):
        return redirect(url_for("login"))

    df = pd.read_csv(DATASET_FILE)
    df = df[df["Roll Number"].astype(str) != roll_number]
    df.to_csv(DATASET_FILE, index=False)

    return redirect(url_for("dashboard"))


# ---------------- Logout Route ----------------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("login"))


# ---------------- Hall Allocation Routes ----------------
from attendance_data import attendance_data, exam_halls, calculate_attendance_percentage, allocate_halls

@app.route('/hall_a')
def hall_a():
    allocated_students = [student for student in exam_halls["Hall A"]["allocated"]]
    return render_template('Hall A Allocation.html', students=allocated_students)

@app.route('/hall_b')
def hall_b():
    allocated_students = [student for student in exam_halls["Hall B"]["allocated"]]
    return render_template('Hall B Allocation.html', students=allocated_students)

@app.route('/hall_c')
def hall_c():
    allocated_students = [student for student in exam_halls["Hall C"]["allocated"]]
    return render_template('Hall C Allocation.html', students=allocated_students)

@app.route('/not_allocated')
def not_allocated():
    not_allocated_students = [student for student in attendance_data if student not in [s for hall in exam_halls.values() for s in hall["allocated"]]]
    return render_template('NOT ALLOCATED STUDENTS.html', students=not_allocated_students)


# ---------------- Search Route ----------------
@app.route('/search')
def search():
    query = request.args.get('query', '').strip().lower()
    results = []

    if query:
        for student in attendance_data:
            roll_no_str = str(student["Roll No."]).lower()
            student_name = student["Student Name"].lower()

            if roll_no_str == query or query in student_name:
                student_hall = "Not Allocated"
                for hall_name, hall_data in exam_halls.items():
                    if student in hall_data["allocated"]:
                        student_hall = hall_name
                        break
                
                student_with_hall = student.copy()
                student_with_hall["Exam Hall"] = student_hall

                results.append(student_with_hall)

    return render_template('search_results.html', students=results)


if __name__ == '__main__':
    for student in attendance_data:
        student["Attendance Percentage"] = calculate_attendance_percentage(student["Attendance"])

    allocate_halls(attendance_data, exam_halls)

    app.run(debug=True)
