import pandas as pd
import streamlit as st
from services.report_service import get_absence_summary, get_all_sections


def render_reports_page(user: dict):
    st.header("Attendance Reports")

    sections = get_all_sections()
    if not sections:
        st.info("No class sections found.")
        return

    section_labels = {
        f"{section['section_code']} - {section['course_name']}": section
        for section in sections
    }
    selected_label = st.selectbox("Select class section", list(section_labels.keys()))
    selected_section = section_labels[selected_label]

    summary = get_absence_summary(selected_section["id"])
    st.subheader("Absence Summary")
    st.dataframe(pd.DataFrame(summary), use_container_width=True)

    if summary:
        df = pd.DataFrame(summary)
        st.bar_chart(df.set_index("student_code")["absence_percent"])
