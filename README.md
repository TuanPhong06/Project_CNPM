# Student Attendance System - Python Streamlit Starter

This is a simple web GUI demo for a Student Attendance System.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Demo accounts

| Role | Username | Password |
|---|---|---|
| Student | student01 | 123456 |
| Student | student02 | 123456 |
| Lecturer | lecturer01 | 123456 |
| Admin / Academic Staff | admin01 | 123456 |

## Suggested task division

1. Member 1: `auth.py`, login UI in `app.py`
2. Member 2: `database.py`, `seed_data.py`
3. Member 3: `pages/student_page.py`
4. Member 4: `pages/lecturer_page.py`, part of `services/attendance_service.py`
5. Member 5: monitoring/edit attendance in `pages/lecturer_page.py`
6. Member 6: `pages/admin_page.py`, `pages/reports_page.py`, `services/report_service.py`
