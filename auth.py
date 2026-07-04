import hashlib
import secrets
import string
import streamlit as st
from database import get_connection

# Hash password using SHA-256
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# Check if the input password matches the stored hash
def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash

# Handle user login check
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

# Handle password change inside user profile
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

# Create a random temporary password
def generate_temporary_password(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

# Handle forgot password request
def reset_password_by_email(email: str):
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", 
        (email.strip(),)
    ).fetchone()

    if not user:
        conn.close()
        return False, "Email not found in the system!", None

    temp_password = generate_temporary_password()
    hashed_temp = hash_password(temp_password)

    conn.execute(
        "UPDATE users SET password_hash = ? WHERE email = ?",
        (hashed_temp, email.strip()),
    )
    conn.commit()
    conn.close()
    return True, "Temporary password created successfully!", temp_password

# Clear session state on logout
def logout():
    st.session_state.user = None
    st.session_state.login_error = None
    st.session_state.last_reset_password = None
