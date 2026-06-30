from datetime import datetime
from database import get_connection

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def now_text() -> str:
    return datetime.now().strftime(TIME_FORMAT)


def classify_status(opened_at_text: str) -> str:
    """
    Business rule:
    - First 15 minutes: Present
    - Minute 16 to 30: Late
    - After 30 minutes: Absent
    """
    opened_at = datetime.strptime(opened_at_text, TIME_FORMAT)
    elapsed_minutes = (datetime.now() - opened_at).total_seconds() / 60

    if elapsed_minutes <= 15:
        return "Present"
    if elapsed_minutes <= 30:
        return "Late"
    return "Absent"


def generate_session_code(section_code: str) -> str:
    """Generate a simple session code for demo."""
    return section_code.replace("-", "")[-4:].upper() + datetime.now().strftime("%M%S")


def get_student_id_by_user(user_id: int):
    conn = get_connection()
    row = conn.execute("SELECT id FROM students WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return row["id"] if row else None


def get_lecturer_id_by_user(user_id: int):
    conn = get_connection()
    row = conn.execute("SELECT id FROM lecturers WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return row["id"] if row else None


def get_lecturer_sections(user_id: int):
    lecturer_id = get_lecturer_id_by_user(user_id)
    if lecturer_id is None:
        return []

    conn = get_connection()
    rows = conn.execute(
        """
        SELECT cs.*, c.course_code, c.course_name
        FROM class_sections cs
        JOIN courses c ON c.id = cs.course_id
        WHERE cs.lecturer_id = ?
        ORDER BY cs.section_code
        """,
        (lecturer_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def open_session(section_id: int) -> str:
    conn = get_connection()
    section = conn.execute("SELECT * FROM class_sections WHERE id = ?", (section_id,)).fetchone()
    if section is None:
        conn.close()
        raise ValueError("Class section not found")

    session_code = generate_session_code(section["section_code"])
    conn.execute(
        """
        UPDATE class_sections
        SET status = 'open', session_code = ?, opened_at = ?, closed_at = NULL
        WHERE id = ?
        """,
        (session_code, now_text(), section_id),
    )
    conn.commit()
    conn.close()
    return session_code


def close_session(section_id: int):
    conn = get_connection()
    conn.execute(
        """
        UPDATE class_sections
        SET status = 'closed', closed_at = ?
        WHERE id = ?
        """,
        (now_text(), section_id),
    )
    conn.commit()
    conn.close()


def check_in(student_user_id: int, session_code: str):
    student_id = get_student_id_by_user(student_user_id)
    if student_id is None:
        return False, "Student profile not found."

    conn = get_connection()
    section = conn.execute(
        """
        SELECT * FROM class_sections
        WHERE session_code = ? AND status = 'open'
        """,
        (session_code.strip(),),
    ).fetchone()

    if section is None:
        conn.close()
        return False, "Invalid code or attendance session is not open."

    enrolled = conn.execute(
        """
        SELECT 1 FROM enrollments
        WHERE section_id = ? AND student_id = ?
        """,
        (section["id"], student_id),
    ).fetchone()

    if enrolled is None:
        conn.close()
        return False, "You are not enrolled in this class section."

    status = classify_status(section["opened_at"])
    checkin_time = now_text()

    conn.execute(
        """
        INSERT INTO attendance_records(section_id, student_id, checkin_time, method, status, updated_at)
        VALUES (?, ?, ?, 'Attendance Session Code', ?, ?)
        ON CONFLICT(section_id, student_id)
        DO UPDATE SET checkin_time = excluded.checkin_time,
                      status = excluded.status,
                      updated_at = excluded.updated_at
        """,
        (section["id"], student_id, checkin_time, status, checkin_time),
    )
    conn.commit()
    conn.close()
    return True, f"Attendance recorded successfully. Status: {status}."


def get_student_history(user_id: int):
    student_id = get_student_id_by_user(user_id)
    if student_id is None:
        return []

    conn = get_connection()
    rows = conn.execute(
        """
        SELECT c.course_code, c.course_name, cs.section_code, ar.checkin_time, ar.status, ar.method
        FROM attendance_records ar
        JOIN class_sections cs ON cs.id = ar.section_id
        JOIN courses c ON c.id = cs.course_id
        WHERE ar.student_id = ?
        ORDER BY ar.checkin_time DESC
        """,
        (student_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_section_attendance(section_id: int):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT
            s.id AS student_id,
            s.student_code,
            u.full_name,
            COALESCE(ar.status, 'Absent') AS status,
            ar.checkin_time,
            ar.method
        FROM enrollments e
        JOIN students s ON s.id = e.student_id
        JOIN users u ON u.id = s.user_id
        LEFT JOIN attendance_records ar
            ON ar.section_id = e.section_id AND ar.student_id = e.student_id
        WHERE e.section_id = ?
        ORDER BY s.student_code
        """,
        (section_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_attendance_status(section_id: int, student_id: int, status: str, edited_by_user_id: int):
    conn = get_connection()
    time_text = now_text()
    conn.execute(
        """
        INSERT INTO attendance_records(section_id, student_id, checkin_time, method, status, edited_by, updated_at)
        VALUES (?, ?, NULL, 'Manual Edit', ?, ?, ?)
        ON CONFLICT(section_id, student_id)
        DO UPDATE SET status = excluded.status,
                      method = 'Manual Edit',
                      edited_by = excluded.edited_by,
                      updated_at = excluded.updated_at
        """,
        (section_id, student_id, status, edited_by_user_id, time_text),
    )
    conn.commit()
    conn.close()
