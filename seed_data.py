from datetime import datetime
from auth import hash_password
from database import get_connection, init_db


def table_is_empty(table_name: str) -> bool:
    conn = get_connection()
    row = conn.execute(f"SELECT COUNT(*) AS total FROM {table_name}").fetchone()
    conn.close()
    return row["total"] == 0


def seed_if_empty():
    init_db()
    if table_is_empty("users"):
        seed_data(reset=False)


def seed_data(reset: bool = True):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    if reset:
        cursor.executescript(
            """
            DELETE FROM notifications;
            DELETE FROM attendance_records;
            DELETE FROM attendance_sessions;
            DELETE FROM enrollments;
            DELETE FROM class_sections;
            DELETE FROM courses;
            DELETE FROM lecturers;
            DELETE FROM students;
            DELETE FROM users;
            DELETE FROM sqlite_sequence WHERE name IN (
                'notifications', 'attendance_records', 'attendance_sessions',
                'enrollments', 'class_sections', 'courses',
                'lecturers', 'students', 'users'
            );
            """
        )

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    users = [
        ("admin01", "123456", "Academic Admin", "admin01@school.edu.vn", "", "admin"),
        ("lecturer01", "123456", "Dr. Nguyen Van A", "lecturer01@school.edu.vn", "0900000001", "lecturer"),
        ("student01", "123456", "Tran Van B", "student01@student.edu.vn", "0900000002", "student"),
        ("student02", "123456", "Tran Van C", "student02@student.edu.vn", "0900000003", "student"),
    ]

    user_ids = {}
    for username, password, full_name, email, phone, role in users:
        cursor.execute(
            """
            INSERT OR IGNORE INTO users(username, password_hash, full_name, email, phone, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (username, hash_password(password), full_name, email, phone, role, created_at),
        )
        row = cursor.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        user_ids[username] = row["id"]

    cursor.execute(
        "INSERT OR IGNORE INTO lecturers(user_id, lecturer_code, department) VALUES (?, ?, ?)",
        (user_ids["lecturer01"], "GV001", "Information Technology"),
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO students(user_id, student_code, major, face_template)
        VALUES (?, ?, ?, ?)
        """,
        (user_ids["student01"], "SV001", "Software Engineering", "face_template_sv001_demo"),
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO students(user_id, student_code, major, face_template)
        VALUES (?, ?, ?, ?)
        """,
        (user_ids["student02"], "SV002", "Software Engineering", "face_template_sv002_demo"),
    )

    courses = [
        ("SE101", "Software Engineering", 3),
        ("DB101", "Database Systems", 3),
    ]
    for course_code, course_name, credits in courses:
        cursor.execute(
            "INSERT OR IGNORE INTO courses(course_code, course_name, credits) VALUES (?, ?, ?)",
            (course_code, course_name, credits),
        )

    course = cursor.execute("SELECT id FROM courses WHERE course_code = 'SE101'").fetchone()
    lecturer = cursor.execute("SELECT id FROM lecturers WHERE lecturer_code = 'GV001'").fetchone()

    cursor.execute(
        """
        INSERT OR IGNORE INTO class_sections(
            course_id, lecturer_id, section_code, room, semester, academic_year,
            start_time, end_time, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            course["id"],
            lecturer["id"],
            "SE101-01",
            "Room A1.1",
            "Semester 1",
            "2026-2027",
            "07:30",
            "09:30",
            "not_opened",
        ),
    )

    section = cursor.execute("SELECT id FROM class_sections WHERE section_code = 'SE101-01'").fetchone()
    students = cursor.execute("SELECT id FROM students ORDER BY student_code").fetchall()
    today = datetime.now().strftime("%Y-%m-%d")

    for student in students:
        cursor.execute(
            """
            INSERT OR IGNORE INTO enrollments(section_id, student_id, enrolled_date, status)
            VALUES (?, ?, ?, ?)
            """,
            (section["id"], student["id"], today, "active"),
        )

    conn.commit()
    conn.close()
    print("Sample data seeded successfully.")


if __name__ == "__main__":
    seed_data(reset=True)
