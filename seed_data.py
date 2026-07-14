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
        ("admin01", "123456", "Academic Admin", "admin01@gmail.com", "", "admin"),
        ("lecturer01", "123456", "Dr. Henry", "Henry@gmail.com", "0900000001", "lecturer"),
        ("lecturer02", "123456", "Dr. Jane", "Jane@gmail.com", "0900000002", "lecturer"),
        ("lecturer03", "123456", "Dr. John", "John@gmail.com", "0900000003", "lecturer"),
        ("student01", "123456", "John Doe", "john@gmail.com", "0900000002", "student"),
        ("student02", "123456", "Bob Smith", "bob@gmail.com", "0900000003", "student"),
        ("student03", "123456", "Alice Johnson", "alice@gmail.com", "0900000004", "student"),
        ("student04", "123456", "Charlie Brown", "charlie@gmail.com", "0900000005", "student"),
        ("student05", "123456", "Diana Prince", "diana@gmail.com", "0900000006", "student"),
        ("student06", "123456", "Eve Wilson", "eve@gmail.com", "0900000007", "student"),
        ("student07", "123456", "Frank Miller", "frank@gmail.com", "0900000008", "student"),
        ("student08", "123456", "Grace Lee", "grace@gmail.com", "0900000009", "student"),
        ("student09", "123456", "Henry Davis", "henry@gmail.com", "0900000010", "student"),
        ("student10", "123456", "Ivy Chen", "ivy@gmail.com", "0900000011", "student"),
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
        (user_ids["lecturer01"], "GV001", "Software Engineering"),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO lecturers(user_id, lecturer_code, department) VALUES (?, ?, ?)",
        (user_ids["lecturer02"], "GV002", "Database Systems"),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO lecturers(user_id, lecturer_code, department) VALUES (?, ?, ?)",
        (user_ids["lecturer03"], "GV003", "Mathematics"),
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO students(user_id, student_code, major)
        VALUES (?, ?, ?)
        """,
        (user_ids["student01"], "SV001", "Software Engineering"),
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO students(user_id, student_code, major)
        VALUES (?, ?, ?)
        """,
        (user_ids["student02"], "SV002", "Software Engineering"),
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO students(user_id, student_code, major)
        VALUES (?, ?, ?)
        """,
        (user_ids["student03"], "SV003", "Software Engineering"),
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO students(user_id, student_code, major)
        VALUES (?, ?, ?)
        """,
        (user_ids["student04"], "SV004", "Database Systems"),
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO students(user_id, student_code, major)
        VALUES (?, ?, ?)
        """,
        (user_ids["student05"], "SV005", "Database Systems"),
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO students(user_id, student_code, major)
        VALUES (?, ?, ?)
        """,
        (user_ids["student06"], "SV006", "Database Systems" ),
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO students(user_id, student_code, major)
        VALUES (?, ?, ?)
        """,
        (user_ids["student07"], "SV007", "Mathematics"),
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO students(user_id, student_code, major)
        VALUES (?, ?, ?)
        """,
        (user_ids["student08"], "SV008", "Mathematics"),
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO students(user_id, student_code, major)
        VALUES (?, ?, ?)
        """,
        (user_ids["student09"], "SV009", "Mathematics"),
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO students(user_id, student_code, major)
        VALUES (?, ?, ?)
        """,
        (user_ids["student10"], "SV010", "Software Engineering"),
    )
   
    courses = [
        ("SE101", "Software Engineering", 3),
        ("DB101", "Database Systems", 3),
        ("MA101", "Mathematics", 3),
    ]
    for course_code, course_name, credits in courses:
        cursor.execute(
            "INSERT OR IGNORE INTO courses(course_code, course_name, credits) VALUES (?, ?, ?)",
            (course_code, course_name, credits),
        )

    course = cursor.execute("SELECT id FROM courses WHERE course_code = 'SE101'").fetchone()
    lecturer = cursor.execute("SELECT id FROM lecturers WHERE lecturer_code = 'GV001'").fetchone()
    course = cursor.execute("SELECT id FROM courses WHERE course_code = 'DB101'").fetchone()
    lecturer = cursor.execute("SELECT id FROM lecturers WHERE lecturer_code = 'GV002'").fetchone()
    course = cursor.execute("SELECT id FROM courses WHERE course_code = 'MA101'").fetchone()
    lecturer = cursor.execute("SELECT id FROM lecturers WHERE lecturer_code = 'GV003'").fetchone()
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
            "DB101-01",
            "Room B2.2",
            "Semester 1",
            "2026-2027",
            "10:00",
            "12:00",
            "not_opened",
        ),
    )
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
            "MA101-01",
            "Room C3.3",
            "Semester 1",
            "2026-2027",
            "13:00",
            "15:00",
            "not_opened",
        ),
    )

    section = cursor.execute("SELECT id FROM class_sections WHERE section_code = 'SE101-01'").fetchone()
    students = cursor.execute("SELECT id FROM students ORDER BY student_code").fetchall()
    today = datetime.now().strftime("%Y-%m-%d")
    section = cursor.execute("SELECT id FROM class_sections WHERE section_code = 'DB101-01'").fetchone()
    students = cursor.execute("SELECT id FROM students ORDER BY student_code").fetchall()
    today = datetime.now().strftime("%Y-%m-%d")
    section = cursor.execute("SELECT id FROM class_sections WHERE section_code = 'MA101-01'").fetchone()
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
