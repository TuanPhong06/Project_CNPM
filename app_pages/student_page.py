import pandas as pd
import streamlit as st
from database import get_connection
from services.attendance_service import (
    check_in,
    get_notifications,
    get_student_current_status,
    get_student_history,
    mark_notifications_read,
)

STATUS_OPTIONS = ["Present", "Late", "Excused Absence", "Unexcused Absence"]


def get_student_profile(user_id):
    conn = get_connection()
    row = conn.execute(
        """
        SELECT
            s.id AS student_id,
            s.student_code,
            s.major,
            s.face_template,
            u.id AS user_id,
            u.username,
            u.full_name,
            u.email,
            u.phone,
            u.role
        FROM students s
        JOIN users u ON u.id = s.user_id
        WHERE u.id = ?
        """,
        (user_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_student_classes(student_id):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT
            c.course_code,
            c.course_name,
            cs.section_code,
            cs.room,
            cs.start_time,
            cs.end_time,
            cs.status,
            cs.session_code,
            u.full_name AS lecturer_name
        FROM enrollments e
        JOIN class_sections cs ON cs.id = e.section_id
        JOIN courses c ON c.id = cs.course_id
        JOIN lecturers l ON l.id = cs.lecturer_id
        JOIN users u ON u.id = l.user_id
        WHERE e.student_id = ? AND e.status = 'active'
        ORDER BY c.course_code, cs.section_code
        """,
        (student_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def render_attendance_summary(history):
    total = len(history)
    present_count = sum(1 for item in history if item["status"] == "Present")
    late_count = sum(1 for item in history if item["status"] == "Late")
    excused_count = sum(1 for item in history if item["status"] in ["Excused Absence", "Excused Absent"])
    unexcused_count = sum(1 for item in history if item["status"] in ["Unexcused Absence", "Absent"])

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total", total)
    col2.metric("Present", present_count)
    col3.metric("Late", late_count)
    col4.metric("Excused", excused_count)
    col5.metric("Unexcused", unexcused_count)


def render_student_page(user):
    st.header("Student Dashboard")
    profile = get_student_profile(user["id"])

    if profile is None:
        st.error("Student profile not found.")
        st.info("Please check your account or contact Academic Staff.")
        return

    student_id = profile["student_id"]

    col1, col2, col3 = st.columns(3)
    col1.info(f"Student Code: **{profile['student_code']}**")
    col2.info(f"Major: **{profile['major'] or 'N/A'}**")
    col3.info(f"Email: **{profile['email'] or 'N/A'}**")

    tab_checkin, tab_status, tab_classes, tab_history, tab_notifications, tab_account = st.tabs(
        [
            "Check Attendance",
            "Current Status",
            "My Classes",
            "Attendance History",
            "Notifications",
            "Account",
        ]
    )

    with tab_checkin:
        st.subheader("Enter Attendance Code")
        st.write("Enter the attendance code provided by your lecturer.")

        with st.form("student_attendance_form", clear_on_submit=True):
            session_code = st.text_input("Attendance Code", placeholder="Example: SEABC123")
            submit_button = st.form_submit_button("Submit Attendance", type="primary")

        if submit_button:
            success, message = check_in(user["id"], session_code)
            if success:
                st.success(message)
            else:
                st.error(message)

        st.markdown("### Attendance Rule")
        st.write("0 - 15 minutes after the session opens: **Present**")
        st.write("16 - 30 minutes after the session opens: **Late**")
        st.write("After 30 minutes or after the session is closed: **Unexcused Absence**")

    with tab_status:
        st.subheader("Current Open Session Status")
        current_status = get_student_current_status(user["id"])
        if not current_status:
            st.info("There is no open attendance session for your enrolled classes.")
        else:
            st.dataframe(pd.DataFrame(current_status), use_container_width=True, hide_index=True)

    with tab_classes:
        st.subheader("My Classes")
        classes = get_student_classes(student_id)
        if not classes:
            st.info("You have not been enrolled in any class yet.")
        else:
            class_df = pd.DataFrame(classes).rename(
                columns={
                    "course_code": "Course Code",
                    "course_name": "Course Name",
                    "section_code": "Section",
                    "room": "Room",
                    "start_time": "Start Time",
                    "end_time": "End Time",
                    "status": "Status",
                    "session_code": "Session Code",
                    "lecturer_name": "Lecturer",
                }
            )
            st.dataframe(class_df, use_container_width=True, hide_index=True)

    with tab_history:
        st.subheader("Attendance History")
        history = get_student_history(user["id"])
        if not history:
            st.info("No attendance history found.")
        else:
            render_attendance_summary(history)
            history_df = pd.DataFrame(history).rename(
                columns={
                    "course_code": "Course Code",
                    "course_name": "Course Name",
                    "section_code": "Section",
                    "session_code": "Session Code",
                    "opened_at": "Opened At",
                    "closed_at": "Closed At",
                    "checkin_time": "Check-in Time",
                    "method": "Method",
                    "status": "Status",
                    "edit_reason": "Edit Reason",
                    "updated_at": "Updated At",
                }
            )
            status_filter = st.multiselect(
                "Filter by Status",
                options=STATUS_OPTIONS,
                default=STATUS_OPTIONS,
            )
            if status_filter:
                history_df = history_df[history_df["Status"].isin(status_filter)]
            st.dataframe(history_df, use_container_width=True, hide_index=True)

    with tab_notifications:
        st.subheader("Notifications")
        notifications = get_notifications(user["id"])
        if not notifications:
            st.info("No notifications yet.")
        else:
            st.dataframe(pd.DataFrame(notifications), use_container_width=True, hide_index=True)
            if st.button("Mark all as read"):
                mark_notifications_read(user["id"])
                st.success("Notifications marked as read.")
                st.rerun()

    with tab_account:
        st.subheader("Account Information")
        st.write(f"Username: **{profile['username']}**")
        st.write(f"Full Name: **{profile['full_name']}**")
        st.write(f"Student Code: **{profile['student_code']}**")
        st.write(f"Major: **{profile['major'] or 'N/A'}**")
        st.write(f"Email: **{profile['email'] or 'N/A'}**")
        st.write(f"Phone: **{profile['phone'] or 'N/A'}**")
        st.write(f"Face Template: **{profile['face_template'] or 'Not updated'}**")
