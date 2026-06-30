import hashlib
import secrets
import string
from database import get_connection


def hash_password(password: str) -> str:
    """Hash password using SHA-256 for simple demo purpose."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def login(username: str, password: str):
    """Return user row if username and password are correct."""
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


def generate_temporary_password(length: int = 8) -> str:
    """Generate a temporary password. Email sending can be simulated in demo."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))
