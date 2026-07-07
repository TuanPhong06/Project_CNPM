from datetime import datetime
import random
import string
from database import get_connection

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
ACTIVE_STATUSES = ["Present", "Late"]
ABSENT_STATUS = "Unexcused Absence"
EXCUSED_STATUS = "Excused Absence"


def now_text() -> str:
    return datetime.now().strftime(TIME_FORMAT)


def classify_status(opened_at_text: str) -> str:
    if not opened_at_text:
        return "Present"

    try:
        opened_at = datetime.strptime(opened_at_text, TIME_FORMAT)
    except ValueError:
        opened_at = datetime.fromisoformat(opened_at_text)

    elapsed_minutes = (datetime.now() - opened_at).total_seconds() / 60

    if elapsed_minutes <= 15:
        return "Present"
    if elapsed_minutes <= 30:
        return "Late"
    return ABSENT_STATUS


def generate_session_code(section_code: str, length: int = 6) -> str:
    prefix = section_code.replace("-", "").upper()[:2]
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return f"{prefix}{suffix}"


def create_notification(user_id: int, title: str, message: str):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO notifications(user_id, title, message, created_at, is_read)
        VALUES (?, ?, ?, ?, 0)
        """,
        (user_id, title, message, now_text()),
    )
    conn.commit()
    conn.close()


def get_notifications(user_id: int):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT * FROM notifications
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def mark_notifications_read(user_id: int):
    conn = get_connection()
    conn.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


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
        SELECT
            cs.*,
            c.course_code,
            c.course_name
        FROM class_sections cs
        JOIN courses c ON c.id = cs.course_id
        WHERE cs.lecturer_id = ?
        ORDER BY cs.section_code
        """,
        (lecturer_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_latest_session(section_id: int):
    conn = get_connection()
    row = conn.execute(
        """
        SELECT * FROM attendance_sessions
        WHERE section_id = ?
        ORDER BY opened_at DESC, id DESC
        LIMIT 1
        """,
        (section_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_active_session(section_id: int):
    conn = get_connection()
    row = conn.execute(
        """
        SELECT * FROM attendance_sessions
        WHERE section_id = ? AND status = 'open'
        ORDER BY opened_at DESC, id DESC
        LIMIT 1
        """,
        (section_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_section_sessions(section_id: int):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT * FROM attendance_sessions
        WHERE section_id = ?
        ORDER BY opened_at DESC, id DESC
        """,
        (section_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def open_session(section_id: int, created_by_user_id: int = None) -> str:
    conn = get_connection()
    section = conn.execute("SELECT * FROM class_sections WHERE id = ?", (section_id,)).fetchone()

    if section is None:
        conn.close()
        raise ValueError("Class section not found.")

    active = conn.execute(
        """
        SELECT * FROM attendance_sessions
        WHERE section_id = ? AND status = 'open'
        ORDER BY opened_at DESC, id DESC
        LIMIT 1
        """,
        (section_id,),
    ).fetchone()

    if active is not None:
        conn.close()
        return active["session_code"]

    session_code = generate_session_code(section["section_code"])
    while conn.execute("SELECT 1 FROM attendance_sessions WHERE session_code = ?", (session_code,)).fetchone():
        session_code = generate_session_code(section["section_code"])

    opened_at = now_text()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO attendance_sessions(section_id, session_code, opened_at, status, created_by)
        VALUES (?, ?, ?, 'open', ?)
        """,
        (section_id, session_code, opened_at, created_by_user_id),
    )
    session_id = cursor.lastrowid

    conn.execute(
        """
        UPDATE class_sections
        SET status = 'open', session_code = ?, opened_at = ?, closed_at = NULL,
            current_session_id = ?
        WHERE id = ?
        """,
        (session_code, opened_at, session_id, section_id),
    )

    conn.commit()
    conn.close()
    return session_code


def close_session(section_id: int):
    conn = get_connection()
    session = conn.execute(
        """
        SELECT * FROM attendance_sessions
        WHERE section_id = ? AND status = 'open'
        ORDER BY opened_at DESC, id DESC
        LIMIT 1
        """,
        (section_id,),
    ).fetchone()

    closed_at = now_text()
    if session is not None:
        enrolled_students = conn.execute(
            """
            SELECT e.student_id, s.user_id
            FROM enrollments e
            JOIN students s ON s.id = e.student_id
            WHERE e.section_id = ? AND e.status = 'active'
            """,
            (section_id,),
        ).fetchall()

        for student in enrolled_students:
            existing = conn.execute(
                """
                SELECT 1 FROM attendance_records
                WHERE session_id = ? AND student_id = ?
                """,
                (session["id"], student["student_id"]),
            ).fetchone()
            if existing is None:
                conn.execute(
                    """
                    INSERT INTO attendance_records(
                        session_id, section_id, student_id, checkin_time, method, status, updated_at
                    )
                    VALUES (?, ?, ?, NULL, 'System Auto Mark', ?, ?)
                    """,
                    (session["id"], section_id, student["student_id"], ABSENT_STATUS, closed_at),
                )

        conn.execute(
            "UPDATE attendance_sessions SET status = 'closed', closed_at = ? WHERE id = ?",
            (closed_at, session["id"]),
        )

    conn.execute(
        """
        UPDATE class_sections
        SET status = 'closed', closed_at = ?, current_session_id = NULL
        WHERE id = ?
        """,
        (closed_at, section_id),
    )
    conn.commit()
    conn.close()


def check_in(student_user_id: int, session_code: str):
    student_id = get_student_id_by_user(student_user_id)
    if student_id is None:
        return False, "Student profile not found."

    clean_code = session_code.strip().upper()
    if not clean_code:
        return False, "Please enter the attendance code."

    conn = get_connection()
    session = conn.execute(
        """
        SELECT
            ats.*,
            cs.section_code,
            c.course_code,
            c.course_name
        FROM attendance_sessions ats
        JOIN class_sections cs ON cs.id = ats.section_id
        JOIN courses c ON c.id = cs.course_id
        WHERE UPPER(ats.session_code) = UPPER(?)
          AND ats.status = 'open'
        """,
        (clean_code,),
    ).fetchone()

    if session is None:
        conn.close()
        return False, "Invalid code or attendance session is not open."

    enrolled = conn.execute(
        """
        SELECT 1
        FROM enrollments
        WHERE section_id = ? AND student_id = ? AND status = 'active'
        """,
        (session["section_id"], student_id),
    ).fetchone()

    if enrolled is None:
        conn.close()
        return False, "You are not enrolled in this class section."

    old_record = conn.execute(
        """
        SELECT status, checkin_time
        FROM attendance_records
        WHERE session_id = ? AND student_id = ?
        """,
        (session["id"], student_id),
    ).fetchone()

    if old_record is not None:
        conn.close()
        return False, f"You have already checked in. Status: {old_record['status']}."

    status = classify_status(session["opened_at"])
    checkin_time = now_text()

    conn.execute(
        """
        INSERT INTO attendance_records(
            session_id, section_id, student_id, checkin_time, method, status,
            updated_at, notification_sent
        )
        VALUES (?, ?, ?, ?, 'Attendance Session Code', ?, ?, 1)
        """,
        (session["id"], session["section_id"], student_id, checkin_time, status, checkin_time),
    )

    conn.execute(
        """
        INSERT INTO notifications(user_id, title, message, created_at, is_read)
        VALUES (?, ?, ?, ?, 0)
        """,
        (
            student_user_id,
            "Attendance confirmed",
            f"Your attendance for {session['course_name']} ({session['section_code']}) was recorded at {checkin_time}. Status: {status}.",
            checkin_time,
        ),
    )

    conn.commit()
    conn.close()
    return True, f"Attendance recorded successfully. Status: {status}."


def get_student_current_status(user_id: int):
    student_id = get_student_id_by_user(user_id)
    if student_id is None:
        return []

    conn = get_connection()
    rows = conn.execute(
        """
        SELECT
            c.course_code,
            c.course_name,
            cs.section_code,
            ats.session_code,
            ats.status AS session_status,
            COALESCE(ar.status, 'Not checked in') AS attendance_status,
            ar.checkin_time
        FROM enrollments e
        JOIN class_sections cs ON cs.id = e.section_id
        JOIN courses c ON c.id = cs.course_id
        JOIN attendance_sessions ats ON ats.section_id = cs.id AND ats.status = 'open'
        LEFT JOIN attendance_records ar
            ON ar.session_id = ats.id AND ar.student_id = e.student_id
        WHERE e.student_id = ? AND e.status = 'active'
        ORDER BY ats.opened_at DESC
        """,
        (student_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_student_history(user_id: int):
    student_id = get_student_id_by_user(user_id)
    if student_id is None:
        return []

    conn = get_connection()
    rows = conn.execute(
        """
        SELECT
            c.course_code,
            c.course_name,
            cs.section_code,
            ats.session_code,
            ats.opened_at,
            ats.closed_at,
            ar.checkin_time,
            ar.status,
            ar.method,
            ar.edit_reason,
            ar.updated_at
        FROM attendance_records ar
        JOIN attendance_sessions ats ON ats.id = ar.session_id
        JOIN class_sections cs ON cs.id = ar.section_id
        JOIN courses c ON c.id = cs.course_id
        WHERE ar.student_id = ?
        ORDER BY ats.opened_at DESC, ar.updated_at DESC
        """,
        (student_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_section_attendance(section_id: int, session_id: int = None):
    conn = get_connection()
    if session_id is None:
        latest = conn.execute(
            """
            SELECT id FROM attendance_sessions
            WHERE section_id = ?
            ORDER BY opened_at DESC, id DESC
            LIMIT 1
            """,
            (section_id,),
        ).fetchone()
        session_id = latest["id"] if latest else None

    if session_id is None:
        rows = conn.execute(
            """
            SELECT
                s.id AS student_id,
                s.student_code,
                u.full_name,
                'No session yet' AS status,
                NULL AS checkin_time,
                NULL AS method,
                NULL AS edit_reason,
                NULL AS updated_at
            FROM enrollments e
            JOIN students s ON s.id = e.student_id
            JOIN users u ON u.id = s.user_id
            WHERE e.section_id = ? AND e.status = 'active'
            ORDER BY s.student_code
            """,
            (section_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT
                s.id AS student_id,
                s.student_code,
                u.full_name,
                COALESCE(ar.status, ?) AS status,
                ar.checkin_time,
                ar.method,
                ar.edit_reason,
                ar.updated_at
            FROM enrollments e
            JOIN students s ON s.id = e.student_id
            JOIN users u ON u.id = s.user_id
            LEFT JOIN attendance_records ar
                ON ar.session_id = ?
               AND ar.student_id = e.student_id
            WHERE e.section_id = ? AND e.status = 'active'
            ORDER BY s.student_code
            """,
            (ABSENT_STATUS, session_id, section_id),
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_attendance_status(
    section_id: int,
    student_id: int,
    status: str,
    edited_by_user_id: int,
    edit_reason: str = "",
    session_id: int = None,
):
    conn = get_connection()
    if session_id is None:
        latest = conn.execute(
            """
            SELECT id FROM attendance_sessions
            WHERE section_id = ?
            ORDER BY opened_at DESC, id DESC
            LIMIT 1
            """,
            (section_id,),
        ).fetchone()
        if latest is None:
            conn.close()
            return False, "No attendance session found for this class section."
        session_id = latest["id"]

    time_text = now_text()
    conn.execute(
        """
        INSERT INTO attendance_records(
            session_id, section_id, student_id, checkin_time, method, status,
            edited_by, edit_reason, updated_at
        )
        VALUES (?, ?, ?, NULL, 'Manual Edit', ?, ?, ?, ?)
        ON CONFLICT(session_id, student_id)
        DO UPDATE SET
            status = excluded.status,
            method = 'Manual Edit',
            edited_by = excluded.edited_by,
            edit_reason = excluded.edit_reason,
            updated_at = excluded.updated_at
        """,
        (session_id, section_id, student_id, status, edited_by_user_id, edit_reason, time_text),
    )
    conn.commit()
    conn.close()
    return True, "Attendance status updated."
