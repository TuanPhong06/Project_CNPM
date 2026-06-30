# Student Attendance System - Python Streamlit Starter

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

1. Thư: `auth.py`, login UI in `app.py`
2. Nhân: `database.py`, `seed_data.py`
3. Phong: `pages/student_page.py`
4. Sơn: `pages/lecturer_page.py`, part of `services/attendance_service.py`
5. Đạt: monitoring/edit attendance in `pages/lecturer_page.py`
6. Phước: `pages/admin_page.py`, `pages/reports_page.py`, `services/report_service.py`
