import pandas as pd
import streamlit as st
from services.attendance_service import (
    close_session,
    get_lecturer_sections,
    get_section_attendance,
    get_section_sessions,
    open_session,
    update_attendance_status,
)
from services.report_service import export_section_attendance_to_excel, get_absence_summary

STATUS_OPTIONS = ["Present", "Late", "Excused Absence", "Unexcused Absence"]


def render_lecturer_page(user: dict):
    st.header("Lecturer Dashboard")

    sections = get_lecturer_sections(user["id"])
    if not sections:
        st.info("You do not have any assigned class sections.")
        return

    section_labels = {
        f"{section['section_code']} - {section['course_name']} ({section['status']})": section
        for section in sections
    }
    selected_label = st.selectbox("Select class section", list(section_labels.keys()))
    selected_section = section_labels[selected_label]
    section_id = selected_section["id"]

    st.subheader("Class Information")
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.write(f"**Course:** {selected_section['course_name']}")
    col_b.write(f"**Section:** {selected_section['section_code']}")
    col_c.write(f"**Room:** {selected_section.get('room') or 'N/A'}")
    col_d.write(f"**Time:** {selected_section.get('start_time') or 'N/A'} - {selected_section.get('end_time') or 'N/A'}")

    st.divider()
    st.subheader("Session Control")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Open attendance session", type="primary", use_container_width=True):
            code = open_session(section_id, user["id"])
            st.success(f"Session opened. Code: {code}")
            st.rerun()

    with col2:
        if st.button("Close attendance session", use_container_width=True):
            close_session(section_id)
            st.success("Session closed. Students without check-in were marked as Unexcused Absence.")
            st.rerun()

    with col3:
        if selected_section.get("session_code") and selected_section["status"] == "open":
            st.metric("Current code", selected_section["session_code"])
        else:
            st.metric("Current code", "Not opened")

    sessions = get_section_sessions(section_id)
    selected_session_id = None
    if sessions:
        session_options = {
            f"{s['session_code']} | {s['opened_at']} | {s['status']}": s["id"]
            for s in sessions
        }
        selected_session_label = st.selectbox("View attendance session", list(session_options.keys()))
        selected_session_id = session_options[selected_session_label]

    st.divider()
    st.subheader("Real-time Attendance List")
    records = get_section_attendance(section_id, selected_session_id)
    df = pd.DataFrame(records)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Manual Edit Attendance")
    if records:
        student_labels = {f"{r['student_code']} - {r['full_name']}": r for r in records}
        selected_student_label = st.selectbox("Select student", list(student_labels.keys()))
        selected_student = student_labels[selected_student_label]
        new_status = st.selectbox("New status", STATUS_OPTIONS)
        edit_reason = st.text_area("Edit reason", placeholder="Example: Student had a technical issue")

        if st.button("Save manual edit", type="primary"):
            success, message = update_attendance_status(
                section_id,
                selected_student["student_id"],
                new_status,
                user["id"],
                edit_reason,
                selected_session_id,
            )
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    st.subheader("Class Attendance Statistics")
    summary = get_absence_summary(section_id)
    if summary:
        st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)
        st.bar_chart(pd.DataFrame(summary).set_index("student_code")["absence_rate"])
    else:
        st.info("No statistics available yet.")

    st.subheader("Export Report")
    excel_bytes = export_section_attendance_to_excel(section_id, selected_session_id)
    st.download_button(
        label="Download attendance Excel file",
        data=excel_bytes,
        file_name=f"attendance_{selected_section['section_code']}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
