import hashlib
import secrets
import string
from database import get_connection


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def login(username: str, password: str):
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username.strip(),),
    ).fetchone()
    conn.close()

    if user and verify_password(password, user["password_hash"]):
        return dict(user)
    return None


def change_password(user_id: int, old_password: str, new_password: str) -> bool:
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if not user or not verify_password(old_password, user["password_hash"]):
        conn.close()
        return False

    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (hash_password(new_password), user_id),
    )
    conn.commit()
    conn.close()
    return True


def update_profile(user_id: int, full_name: str, email: str, phone: str = ""):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET full_name = ?, email = ?, phone = ? WHERE id = ?",
            (full_name.strip(), email.strip(), phone.strip(), user_id),
        )
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return True, dict(user)
    except Exception as error:
        conn.rollback()
        return False, str(error)
    finally:
        conn.close()


def generate_temporary_password(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def reset_password(identifier: str):
    conn = get_connection()
    user = conn.execute(
        """
        SELECT * FROM users
        WHERE username = ? OR email = ?
        """,
        (identifier.strip(), identifier.strip()),
    ).fetchone()

    if user is None:
        conn.close()
        return False, "Account not found.", None

    temporary_password = generate_temporary_password()
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (hash_password(temporary_password), user["id"]),
    )
    conn.execute(
        """
        INSERT INTO notifications(user_id, title, message, created_at, is_read)
        VALUES (?, ?, ?, DATETIME('now'), 0)
        """,
        (
            user["id"],
            "Temporary password created",
            "A temporary password was generated for your account. Please change it after login.",
        ),
    )
    conn.commit()
    email = user["email"] or "the registered university email"
    conn.close()
    return True, f"A temporary password was sent to {email}. Demo password: {temporary_password}", temporary_password
