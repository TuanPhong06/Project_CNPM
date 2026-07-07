import pandas as pd
import streamlit as st

from services.report_service import (
    get_section_options,
    get_attendance_detail_report,
    build_attendance_summary,
    export_report_to_excel,
)


def render_reports_page(user):
    st.subheader("Attendance Reports")

    sections = get_section_options()

    if not sections:
        st.info("No class sections found.")
        return

    section_options = {
        f"{item['course_code']} - {item['section_code']} - {item['course_name']}": item["id"]
        for item in sections
    }

    selected_label = st.selectbox("Select Class Section", list(section_options.keys()))
    section_id = section_options[selected_label]

    detail_rows = get_attendance_detail_report(section_id)
    summary_rows = build_attendance_summary(detail_rows)

    if not detail_rows:
        st.info("No attendance data found.")
        return

    st.markdown("### Summary")

    summary_df = pd.DataFrame(summary_rows)

    if not summary_df.empty:
        col1, col2, col3, col4 = st.columns(4)

        total_students = len(summary_df)
        avg_attendance_rate = summary_df["Attendance Rate (%)"].mean()
        avg_absence_rate = summary_df["Absence Rate (%)"].mean()
        total_absent = summary_df["Absent"].sum() + summary_df["Unexcused Absence"].sum()

        col1.metric("Students", total_students)
        col2.metric("Average Attendance", f"{avg_attendance_rate:.2f}%")
        col3.metric("Average Absence", f"{avg_absence_rate:.2f}%")
        col4.metric("Total Absences", int(total_absent))

        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        chart_df = summary_df[["student_name", "Attendance Rate (%)"]].set_index("student_name")
        st.bar_chart(chart_df)

    st.markdown("### Attendance Detail")

    detail_df = pd.DataFrame(detail_rows)

    status_filter = st.multiselect(
        "Filter by status",
        options=sorted(detail_df["status"].dropna().unique().tolist()),
        default=sorted(detail_df["status"].dropna().unique().tolist()),
    )

    if status_filter:
        detail_df = detail_df[detail_df["status"].isin(status_filter)]

    keyword = st.text_input("Search by student name or student code")

    if keyword:
        keyword_lower = keyword.lower()
        detail_df = detail_df[
            detail_df["student_name"].str.lower().str.contains(keyword_lower)
            | detail_df["student_code"].str.lower().str.contains(keyword_lower)
        ]

    st.dataframe(detail_df, use_container_width=True, hide_index=True)

    excel_data = export_report_to_excel(section_id)

    st.download_button(
        label="Download Excel Report",
        data=excel_data,
        file_name="attendance_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
