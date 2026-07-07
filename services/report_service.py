from io import BytesIO
import pandas as pd

from database import get_connection


def get_section_options():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT
            cs.id,
            c.course_code,
            c.course_name,
            cs.section_code
        FROM class_sections cs
        JOIN courses c ON c.id = cs.course_id
        ORDER BY c.course_code, cs.section_code
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_attendance_detail_report(section_id):
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT
            s.student_code,
            u.full_name AS student_name,
            c.course_code,
            c.course_name,
            cs.section_code,
            COALESCE(ar.status, 'Absent') AS status,
            ar.checkin_time,
            ar.method,
            ar.edit_reason,
            ar.updated_at
        FROM enrollments e
        JOIN students s ON s.id = e.student_id
        JOIN users u ON u.id = s.user_id
        JOIN class_sections cs ON cs.id = e.section_id
        JOIN courses c ON c.id = cs.course_id
        LEFT JOIN attendance_records ar
            ON ar.section_id = cs.id
            AND ar.student_id = s.id
        WHERE cs.id = ?
        ORDER BY u.full_name
        """,
        (section_id,),
    ).fetchall()

    conn.close()
    return [dict(row) for row in rows]


def build_attendance_summary(detail_rows):
    if not detail_rows:
        return []

    df = pd.DataFrame(detail_rows)

    summary = (
        df.pivot_table(
            index=["student_code", "student_name"],
            columns="status",
            values="course_code",
            aggfunc="count",
            fill_value=0,
        )
        .reset_index()
    )

    for column in ["Present", "Late", "Absent", "Excused Absent", "Unexcused Absence"]:
        if column not in summary.columns:
            summary[column] = 0

    status_columns = ["Present", "Late", "Absent", "Excused Absent", "Unexcused Absence"]

    summary["Total"] = summary[status_columns].sum(axis=1)
    summary["Attendance Rate (%)"] = (
        (summary["Present"] + summary["Late"]) / summary["Total"] * 100
    ).round(2)

    summary["Absence Rate (%)"] = (
        (summary["Absent"] + summary["Unexcused Absence"]) / summary["Total"] * 100
    ).round(2)

    return summary.to_dict("records")


def export_report_to_excel(section_id):
    detail_rows = get_attendance_detail_report(section_id)
    summary_rows = build_attendance_summary(detail_rows)

    detail_df = pd.DataFrame(detail_rows)
    summary_df = pd.DataFrame(summary_rows)

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        detail_df.to_excel(writer, index=False, sheet_name="Attendance Detail")
        summary_df.to_excel(writer, index=False, sheet_name="Summary")

    output.seek(0)
    return output
def export_section_attendance_to_excel(section_id, session_id=None):
    return export_report_to_excel(section_id)
def get_absence_summary(section_id):
    detail_rows = get_attendance_detail_report(section_id)
    summary_rows = build_attendance_summary(detail_rows)

    result = []

    for row in summary_rows:
        result.append(
            {
                "student_code": row.get("student_code", ""),
                "full_name": row.get("student_name", ""),
                "present": row.get("Present", 0),
                "late": row.get("Late", 0),
                "absent": row.get("Absent", 0),
                "excused_absence": row.get("Excused Absent", 0),
                "unexcused_absence": row.get("Unexcused Absence", 0),
                "attendance_rate": row.get("Attendance Rate (%)", 0),
                "absence_rate": row.get("Absence Rate (%)", 0),
            }
        )

    return result


def export_section_attendance_to_excel(section_id, session_id=None):
    return export_report_to_excel(section_id)