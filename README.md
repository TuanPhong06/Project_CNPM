# Student Attendance System - Streamlit

A Python Streamlit web GUI demo for a Student Attendance System based on the requirement document.

## Implemented features

- Login with role-based access control: Student, Lecturer, Admin / Academic Staff
- Simple captcha and failed-login limiting for demo security
- Update profile and change password for all logged-in users
- Reset password with simulated university email notification
- Student check-in using an attendance session code
- Student current attendance status, history, and notifications
- Lecturer open/close attendance sessions
- When a session is closed, students without check-in are automatically marked as Unexcused Absence
- Lecturer real-time class attendance list and manual status editing with edit reason
- Lecturer attendance statistics, absence percentage, and Excel export
- Academic Staff user management, courses, class sections, timetables, enrollment management
- Academic Staff face template management
- System monitoring and manual database backup
- Reports page with attendance/absence rates and Excel export

## Local demo limitations

Some supplementary requirements are represented at demo level because this is a local Streamlit project:

- HTTPS must be configured at deployment/server level.
- 2,000 concurrent users and millions of records require production infrastructure.
- Offline mobile synchronization requires a mobile/client storage layer.
- Automatic daily backup at 23:00 is represented by the manual backup function in the Admin page.
- Successful attendance email is simulated with an in-app notification and reset-password demo message.

## Run the project

```bash
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

If `py` does not work, use:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Demo accounts

| Role | Username | Password |
|---|---|---|
| Student | student01 | 123456 |
| Student | student02 | 123456 |
| Lecturer | lecturer01 | 123456 |
| Admin / Academic Staff | admin01 | 123456 |

The app automatically creates the database and seeds demo data if the `users` table is empty.

## Docker

```bash
docker build -t student-attendance .
docker run -p 8501:8501 student-attendance
```

Open: `http://localhost:8501`
