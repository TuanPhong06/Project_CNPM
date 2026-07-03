import sqlite3
from pathlib import Path

DB_PATH = Path("attendance.db")


def get_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all database tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL CHECK(role IN ('student', 'lecturer', 'admin'))
        );

        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            student_code TEXT UNIQUE NOT NULL,
            major TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS lecturers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            lecturer_code TEXT UNIQUE NOT NULL,
            department TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT UNIQUE NOT NULL,
            course_name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS class_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            lecturer_id INTEGER NOT NULL,
            section_code TEXT UNIQUE NOT NULL,
            room TEXT,
            start_time TEXT,
            end_time TEXT,
            status TEXT DEFAULT 'not_opened'
                CHECK(status IN ('not_opened', 'open', 'closed')),
            session_code TEXT,
            opened_at TEXT,
            closed_at TEXT,
            FOREIGN KEY(course_id) REFERENCES courses(id),
            FOREIGN KEY(lecturer_id) REFERENCES lecturers(id)
        );

        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            UNIQUE(section_id, student_id),
            FOREIGN KEY(section_id) REFERENCES class_sections(id),
            FOREIGN KEY(student_id) REFERENCES students(id)
        );

        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            checkin_time TEXT,
            method TEXT DEFAULT 'Attendance Session Code',
            status TEXT NOT NULL
                CHECK(status IN ('Present', 'Late', 'Absent', 'Excused Absent')),
            edited_by INTEGER,
            edit_reason TEXT,
            updated_at TEXT,
            UNIQUE(section_id, student_id),
            FOREIGN KEY(section_id) REFERENCES class_sections(id),
            FOREIGN KEY(student_id) REFERENCES students(id),
            FOREIGN KEY(edited_by) REFERENCES users(id)
        );
        """
    )

    # Tự động cập nhật database cũ
    columns = [
        row["name"]
        for row in cursor.execute(
            "PRAGMA table_info(attendance_records)"
        ).fetchall()
    ]

    if "edited_by" not in columns:
        cursor.execute(
            "ALTER TABLE attendance_records ADD COLUMN edited_by INTEGER"
        )

    if "edit_reason" not in columns:
        cursor.execute(
            "ALTER TABLE attendance_records ADD COLUMN edit_reason TEXT"
        )

    if "updated_at" not in columns:
        cursor.execute(
            "ALTER TABLE attendance_records ADD COLUMN updated_at TEXT"
        )

    conn.commit()
    conn.close()
