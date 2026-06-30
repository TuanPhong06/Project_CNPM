from io import BytesIO
import pandas as pd
from database import get_connection
from services.attendance_service import get_section_attendance


def get_absence_summary(section_id: int):
    records = get_section_attendance(section_id)
    total_sessions = 1  # Demo has one active session per section.
    summary = []

    for record in records:
        absent_count = 1 if record["status"] in ["Absent"] else 0
        absence_percent = absent_count / total_sessions * 100
        summary.append(
            {
                "student_code": record["student_code"],
                "full_name": record["full_name"],
                "status": record["status"],
                "absence_percent": absence_percent,
            }
        )
    return summary


def export_section_attendance_to_excel(section_id: int) -> bytes:
    records = get_section_attendance(section_id)
    df = pd.DataFrame(records)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Attendance")

    return output.getvalue()


def get_all_sections():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT cs.id, cs.section_code, c.course_code, c.course_name, u.full_name AS lecturer_name, cs.status
        FROM class_sections cs
        JOIN courses c ON c.id = cs.course_id
        JOIN lecturers l ON l.id = cs.lecturer_id
        JOIN users u ON u.id = l.user_id
        ORDER BY cs.section_code
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
