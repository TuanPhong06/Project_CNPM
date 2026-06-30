from auth import hash_password
from database import get_connection, init_db


def seed_demo_data():
    """Insert demo users and class data if database is empty."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    user_count = cursor.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
    if user_count > 0:
        conn.close()
        return

    users = [
        ("student01", hash_password("123456"), "Nguyen Van An", "student01@university.edu.vn", "student"),
        ("student02", hash_password("123456"), "Tran Thi Binh", "student02@university.edu.vn", "student"),
        ("lecturer01", hash_password("123456"), "Dr. Le Minh", "lecturer01@university.edu.vn", "lecturer"),
        ("admin01", hash_password("123456"), "Academic Staff", "admin01@university.edu.vn", "admin"),
    ]
    cursor.executemany(
        "INSERT INTO users(username, password_hash, full_name, email, role) VALUES (?, ?, ?, ?, ?)",
        users,
    )

    student01_user_id = cursor.execute("SELECT id FROM users WHERE username='student01'").fetchone()["id"]
    student02_user_id = cursor.execute("SELECT id FROM users WHERE username='student02'").fetchone()["id"]
    lecturer_user_id = cursor.execute("SELECT id FROM users WHERE username='lecturer01'").fetchone()["id"]

    cursor.execute(
        "INSERT INTO students(user_id, student_code, major) VALUES (?, ?, ?)",
        (student01_user_id, "SV001", "Software Engineering"),
    )
    cursor.execute(
        "INSERT INTO students(user_id, student_code, major) VALUES (?, ?, ?)",
        (student02_user_id, "SV002", "Software Engineering"),
    )
    cursor.execute(
        "INSERT INTO lecturers(user_id, lecturer_code, department) VALUES (?, ?, ?)",
        (lecturer_user_id, "GV001", "Information Technology"),
    )

    cursor.execute(
        "INSERT INTO courses(course_code, course_name) VALUES (?, ?)",
        ("SE101", "Software Engineering"),
    )

    course_id = cursor.execute("SELECT id FROM courses WHERE course_code='SE101'").fetchone()["id"]
    lecturer_id = cursor.execute("SELECT id FROM lecturers WHERE lecturer_code='GV001'").fetchone()["id"]
    cursor.execute(
        """
        INSERT INTO class_sections(course_id, lecturer_id, section_code, room, start_time, end_time)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (course_id, lecturer_id, "SE101-N2", "A305", "07:00", "09:30"),
    )

    section_id = cursor.execute("SELECT id FROM class_sections WHERE section_code='SE101-N2'").fetchone()["id"]
    student_ids = cursor.execute("SELECT id FROM students").fetchall()
    for student in student_ids:
        cursor.execute(
            "INSERT INTO enrollments(section_id, student_id) VALUES (?, ?)",
            (section_id, student["id"]),
        )

    conn.commit()
    conn.close()
