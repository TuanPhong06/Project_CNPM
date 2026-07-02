import pandas as p
import streamlit as st
from services.attendance_service import (
    close_session,
    get_lecturer_sections,
    get_section_attendance,
    open_session,
    update_attendance_status,
)
from services.report_service import export_section_attendance_to_excel

STATUS_OPTIONS = ["Present", "Late", "Absent", "Excused Absent"]


def render_lecturer_page(user: dict):
    st.header("Lecturer Dashboard")
    st.write(f"Welcome, **{user['full_name']}**")

    sections = get_lecturer_sections(user["id"])
    if not sections:
        st.info("You do not have any assigned class sections.")
        return

    section_labels = {
        f"{s['section_code']} - {s['course_name']} ({s['status']})": s
        for s in sections
    }
    selected_label = st.selectbox("Select class section", list(section_labels.keys()))
    selected_section = section_labels[selected_label]
    section_id = selected_section["id"]

    st.subheader("Session Control")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Open attendance session", type="primary"):
            code = open_session(section_id)
            st.success(f"Session opened. Code: {code}")
            st.rerun()

    with col2:
        if st.button("Close attendance session"):
            close_session(section_id)
            st.success("Session closed.")
            st.rerun()

    with col3:
        if selected_section.get("session_code"):
            st.metric("Current code", selected_section["session_code"])
        else:
            st.metric("Current code", "Not opened")

    st.divider()
    st.subheader("Real-time Attendance List")
    records = get_section_attendance(section_id)
    df = pd.DataFrame(records)
    st.dataframe(df, use_container_width=True)

    st.subheader("Manual Edit Attendance")
    if records:
        student_labels = {
            f"{r['student_code']} - {r['full_name']}": r
            for r in records
        }
        selected_student_label = st.selectbox("Select student", list(student_labels.keys()))
        selected_student = student_labels[selected_student_label]
        new_status = st.selectbox("New status", STATUS_OPTIONS)

        if st.button("Save manual edit"):
            update_attendance_status(
                section_id,
                selected_student["student_id"],
                new_status,
                user["id"],
            )
            st.success("Attendance status updated.")
            st.rerun()

    st.subheader("Export Report")
    excel_bytes = export_section_attendance_to_excel(section_id)
    st.download_button(
        label="Download attendance Excel file",
        data=excel_bytes,
        file_name=f"attendance_{selected_section['section_code']}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
