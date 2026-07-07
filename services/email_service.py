import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")


def is_email_configured():
    return bool(SMTP_EMAIL and SMTP_PASSWORD)


def send_email(to_email, subject, body):
    if not to_email:
        return False, "Receiver email is empty."

    if not is_email_configured():
        print("[EMAIL SIMULATION]")
        print("To:", to_email)
        print("Subject:", subject)
        print("Body:", body)
        return True, "Email simulated successfully. SMTP is not configured."

    try:
        message = MIMEMultipart()
        message["From"] = SMTP_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain", "utf-8"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(message)
        server.quit()

        return True, "Email sent successfully."
    except Exception as error:
        return False, f"Email sending failed: {error}"


def send_attendance_confirmation(to_email, student_name, course_name, status, checkin_time):
    subject = "Attendance Confirmation"
    body = f"""
Dear {student_name},

Your attendance has been submitted successfully.

Course: {course_name}
Status: {status}
Check-in time: {checkin_time}

This is an automatic message from Student Attendance System.
"""
    return send_email(to_email, subject, body)


def send_reset_password_email(to_email, username, temporary_password):
    subject = "Password Reset - Student Attendance System"
    body = f"""
Dear user,

Your password has been reset.

Username: {username}
Temporary password: {temporary_password}

Please log in and change your password immediately.

Student Attendance System
"""
    return send_email(to_email, subject, body)


def send_absence_warning(to_email, student_name, course_name, absence_rate):
    subject = "Attendance Warning"
    body = f"""
Dear {student_name},

Your absence rate is currently high.

Course: {course_name}
Absence rate: {absence_rate:.2f}%

Please contact your lecturer or academic staff if you need support.

Student Attendance System
"""
    return send_email(to_email, subject, body)
