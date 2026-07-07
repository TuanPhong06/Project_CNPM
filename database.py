import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("attendance.db")
BACKUP_DIR = Path("backups")
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _add_column_if_missing(cursor, table_name, column_name, column_type):
    columns = [
        row["name"]
        for row in cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    ]
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            role TEXT NOT NULL CHECK(role IN ('student', 'lecturer', 'admin')),
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            student_code TEXT UNIQUE NOT NULL,
            major TEXT,
            face_template TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS lecturers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            lecturer_code TEXT UNIQUE NOT NULL,
            department TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT UNIQUE NOT NULL,
            course_name TEXT NOT NULL,
            credits INTEGER DEFAULT 3
        );

        CREATE TABLE IF NOT EXISTS class_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            lecturer_id INTEGER NOT NULL,
            section_code TEXT UNIQUE NOT NULL,
            room TEXT,
            semester TEXT,
            academic_year TEXT,
            start_time TEXT,
            end_time TEXT,
            status TEXT DEFAULT 'not_opened'
                CHECK(status IN ('not_opened', 'open', 'closed')),
            session_code TEXT,
            opened_at TEXT,
            closed_at TEXT,
            current_session_id INTEGER,
            FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
            FOREIGN KEY(lecturer_id) REFERENCES lecturers(id) ON DELETE CASCADE,
            FOREIGN KEY(current_session_id) REFERENCES attendance_sessions(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            enrolled_date TEXT,
            status TEXT DEFAULT 'active',
            UNIQUE(section_id, student_id),
            FOREIGN KEY(section_id) REFERENCES class_sections(id) ON DELETE CASCADE,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS attendance_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_id INTEGER NOT NULL,
            session_code TEXT UNIQUE NOT NULL,
            opened_at TEXT NOT NULL,
            closed_at TEXT,
            status TEXT DEFAULT 'open' CHECK(status IN ('open', 'closed')),
            created_by INTEGER,
            FOREIGN KEY(section_id) REFERENCES class_sections(id) ON DELETE CASCADE,
            FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            section_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            checkin_time TEXT,
            method TEXT DEFAULT 'Attendance Session Code',
            status TEXT NOT NULL CHECK(status IN (
                'Present', 'Late', 'Absent', 'Excused Absent',
                'Excused Absence', 'Unexcused Absence'
            )),
            edited_by INTEGER,
            edit_reason TEXT,
            updated_at TEXT,
            notification_sent INTEGER DEFAULT 0,
            UNIQUE(session_id, student_id),
            FOREIGN KEY(session_id) REFERENCES attendance_sessions(id) ON DELETE CASCADE,
            FOREIGN KEY(section_id) REFERENCES class_sections(id) ON DELETE CASCADE,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY(edited_by) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS backup_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            backup_path TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )

    _add_column_if_missing(cursor, "users", "phone", "TEXT")
    _add_column_if_missing(cursor, "users", "created_at", "TEXT")
    _add_column_if_missing(cursor, "students", "face_template", "TEXT")
    _add_column_if_missing(cursor, "courses", "credits", "INTEGER DEFAULT 3")
    _add_column_if_missing(cursor, "class_sections", "semester", "TEXT")
    _add_column_if_missing(cursor, "class_sections", "academic_year", "TEXT")
    _add_column_if_missing(cursor, "class_sections", "current_session_id", "INTEGER")
    _add_column_if_missing(cursor, "attendance_records", "session_id", "INTEGER")
    _add_column_if_missing(cursor, "attendance_records", "edited_by", "INTEGER")
    _add_column_if_missing(cursor, "attendance_records", "edit_reason", "TEXT")
    _add_column_if_missing(cursor, "attendance_records", "updated_at", "TEXT")
    _add_column_if_missing(cursor, "attendance_records", "notification_sent", "INTEGER DEFAULT 0")

    conn.commit()
    conn.close()


def execute_query(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return True
    except sqlite3.Error as error:
        print(f"Database error: {error}")
        return False
    finally:
        conn.close()


def fetch_data(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_one(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_database_backup():
    init_db()
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"attendance_backup_{timestamp}.db"

    if DB_PATH.exists():
        shutil.copy2(DB_PATH, backup_path)
    else:
        get_connection().close()
        shutil.copy2(DB_PATH, backup_path)

    conn = get_connection()
    conn.execute(
        "INSERT INTO backup_logs(backup_path, created_at) VALUES (?, ?)",
        (str(backup_path), datetime.now().strftime(TIME_FORMAT)),
    )
    conn.commit()
    conn.close()
    return backup_path


def get_backup_logs():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM backup_logs ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
