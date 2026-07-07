import hashlib
import pandas as pd
import streamlit as st

from database import get_connection


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def fetch_all_users():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, username, full_name, email, role
        FROM users
        ORDER BY role, username
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_all_courses():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, course_code, course_name
        FROM courses
        ORDER BY course_code
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_all_lecturers():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT l.id, l.lecturer_code, u.full_name
        FROM lecturers l
        JOIN users u ON u.id = l.user_id
        ORDER BY u.full_name
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_all_students():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT s.id, s.student_code, u.full_name
        FROM students s
        JOIN users u ON u.id = s.user_id
        ORDER BY u.full_name
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_all_sections():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT
            cs.id,
            c.course_code,
            c.course_name,
            cs.section_code,
            cs.room,
            cs.start_time,
            cs.end_time,
            cs.status,
            u.full_name AS lecturer_name
        FROM class_sections cs
        JOIN courses c ON c.id = cs.course_id
        JOIN lecturers l ON l.id = cs.lecturer_id
        JOIN users u ON u.id = l.user_id
        ORDER BY c.course_code, cs.section_code
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_user(username, password, full_name, email, role, code=None, major=None, department=None):
    if not username or not password or not full_name or not role:
        return False, "Please fill in all required fields."

    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (username, password_hash, full_name, email, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (username, hash_password(password), full_name, email, role),
        )

        user_id = cursor.lastrowid

        if role == "student":
            student_code = code or f"SV{user_id:03d}"
            cursor.execute(
                """
                INSERT INTO students (user_id, student_code, major)
                VALUES (?, ?, ?)
                """,
                (user_id, student_code, major or ""),
            )

        elif role == "lecturer":
            lecturer_code = code or f"GV{user_id:03d}"
            cursor.execute(
                """
                INSERT INTO lecturers (user_id, lecturer_code, department)
                VALUES (?, ?, ?)
                """,
                (user_id, lecturer_code, department or ""),
            )

        conn.commit()
        return True, "User added successfully."
    except Exception as error:
        conn.rollback()
        return False, f"Failed to add user: {error}"
    finally:
        conn.close()


def update_user(user_id, full_name, email, role):
    conn = get_connection()

    try:
        conn.execute(
            """
            UPDATE users
            SET full_name = ?, email = ?, role = ?
            WHERE id = ?
            """,
            (full_name, email, role, user_id),
        )
        conn.commit()
        return True, "User updated successfully."
    except Exception as error:
        conn.rollback()
        return False, f"Failed to update user: {error}"
    finally:
        conn.close()


def delete_user(user_id):
    conn = get_connection()

    try:
        user = conn.execute(
            "SELECT role FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

        if user is None:
            return False, "User not found."

        role = user["role"]

        if role == "student":
            student = conn.execute(
                "SELECT id FROM students WHERE user_id = ?",
                (user_id,),
            ).fetchone()

            if student:
                conn.execute(
                    "DELETE FROM attendance_records WHERE student_id = ?",
                    (student["id"],),
                )
                conn.execute(
                    "DELETE FROM enrollments WHERE student_id = ?",
                    (student["id"],),
                )
                conn.execute(
                    "DELETE FROM students WHERE id = ?",
                    (student["id"],),
                )

        elif role == "lecturer":
            lecturer = conn.execute(
                "SELECT id FROM lecturers WHERE user_id = ?",
                (user_id,),
            ).fetchone()

            if lecturer:
                section_count = conn.execute(
                    "SELECT COUNT(*) AS total FROM class_sections WHERE lecturer_id = ?",
                    (lecturer["id"],),
                ).fetchone()["total"]

                if section_count > 0:
                    return False, "Cannot delete lecturer because this lecturer is assigned to class sections."

                conn.execute(
                    "DELETE FROM lecturers WHERE id = ?",
                    (lecturer["id"],),
                )

        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True, "User deleted successfully."
    except Exception as error:
        conn.rollback()
        return False, f"Failed to delete user: {error}"
    finally:
        conn.close()


def add_course(course_code, course_name):
    if not course_code or not course_name:
        return False, "Please enter course code and course name."

    conn = get_connection()

    try:
        conn.execute(
            """
            INSERT INTO courses (course_code, course_name)
            VALUES (?, ?)
            """,
            (course_code.upper(), course_name),
        )
        conn.commit()
        return True, "Course added successfully."
    except Exception as error:
        conn.rollback()
        return False, f"Failed to add course: {error}"
    finally:
        conn.close()


def delete_course(course_id):
    conn = get_connection()

    try:
        section_count = conn.execute(
            "SELECT COUNT(*) AS total FROM class_sections WHERE course_id = ?",
            (course_id,),
        ).fetchone()["total"]

        if section_count > 0:
            return False, "Cannot delete course because it has class sections."

        conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        conn.commit()
        return True, "Course deleted successfully."
    except Exception as error:
        conn.rollback()
        return False, f"Failed to delete course: {error}"
    finally:
        conn.close()


def add_section(course_id, lecturer_id, section_code, room, start_time, end_time):
    if not course_id or not lecturer_id or not section_code:
        return False, "Please select course, lecturer and enter section code."

    conn = get_connection()

    try:
        conn.execute(
            """
            INSERT INTO class_sections (
                course_id,
                lecturer_id,
                section_code,
                room,
                start_time,
                end_time,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                course_id,
                lecturer_id,
                section_code.upper(),
                room,
                start_time,
                end_time,
                "not_opened",
            ),
        )
        conn.commit()
        return True, "Class section added successfully."
    except Exception as error:
        conn.rollback()
        return False, f"Failed to add section: {error}"
    finally:
        conn.close()


def delete_section(section_id):
    conn = get_connection()

    try:
        conn.execute("DELETE FROM attendance_records WHERE section_id = ?", (section_id,))
        conn.execute("DELETE FROM enrollments WHERE section_id = ?", (section_id,))
        conn.execute("DELETE FROM class_sections WHERE id = ?", (section_id,))
        conn.commit()
        return True, "Class section deleted successfully."
    except Exception as error:
        conn.rollback()
        return False, f"Failed to delete section: {error}"
    finally:
        conn.close()


def enroll_student(section_id, student_id):
    if not section_id or not student_id:
        return False, "Please select class section and student."

    conn = get_connection()

    try:
        conn.execute(
            """
            INSERT INTO enrollments (section_id, student_id)
            VALUES (?, ?)
            """,
            (section_id, student_id),
        )
        conn.commit()
        return True, "Student enrolled successfully."
    except Exception as error:
        conn.rollback()
        return False, f"Failed to enroll student: {error}"
    finally:
        conn.close()


def render_admin_page(user):
    st.subheader("Academic Admin Management")

    tab_users, tab_courses, tab_sections, tab_enroll = st.tabs(
        [
            "Manage Users",
            "Manage Courses",
            "Manage Sections",
            "Enroll Students",
        ]
    )

    with tab_users:
        st.markdown("### Add New User")

        with st.form("add_user_form", clear_on_submit=True):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            full_name = st.text_input("Full Name")
            email = st.text_input("Email")
            role = st.selectbox("Role", ["student", "lecturer", "admin"])
            code = st.text_input("Student/Lecturer Code")
            major = st.text_input("Major")
            department = st.text_input("Department")

            submitted = st.form_submit_button("Add User")

        if submitted:
            success, message = add_user(
                username,
                password,
                full_name,
                email,
                role,
                code,
                major,
                department,
            )
            st.success(message) if success else st.error(message)

        st.markdown("### User List")
        users = fetch_all_users()

        if users:
            keyword = st.text_input("Search user by username or full name")
            role_filter = st.selectbox("Filter by role", ["all", "student", "lecturer", "admin"])

            filtered_users = users

            if keyword:
                keyword_lower = keyword.lower()
                filtered_users = [
                    item for item in filtered_users
                    if keyword_lower in item["username"].lower()
                    or keyword_lower in item["full_name"].lower()
                ]

            if role_filter != "all":
                filtered_users = [
                    item for item in filtered_users
                    if item["role"] == role_filter
                ]

            st.dataframe(pd.DataFrame(filtered_users), use_container_width=True, hide_index=True)

            st.markdown("### Edit / Delete User")
            user_options = {
                f"{item['username']} - {item['full_name']} ({item['role']})": item
                for item in users
            }

            selected_label = st.selectbox("Select user", list(user_options.keys()))
            selected_user = user_options[selected_label]

            edit_full_name = st.text_input("Edit Full Name", value=selected_user["full_name"])
            edit_email = st.text_input("Edit Email", value=selected_user["email"] or "")
            edit_role = st.selectbox(
                "Edit Role",
                ["student", "lecturer", "admin"],
                index=["student", "lecturer", "admin"].index(selected_user["role"]),
            )

            col_update, col_delete = st.columns(2)

            with col_update:
                if st.button("Update User"):
                    success, message = update_user(
                        selected_user["id"],
                        edit_full_name,
                        edit_email,
                        edit_role,
                    )
                    st.success(message) if success else st.error(message)
                    st.rerun()

            with col_delete:
                if st.button("Delete User"):
                    success, message = delete_user(selected_user["id"])
                    st.success(message) if success else st.error(message)
                    st.rerun()
        else:
            st.info("No users found.")

    with tab_courses:
        st.markdown("### Add Course")

        with st.form("add_course_form", clear_on_submit=True):
            course_code = st.text_input("Course Code")
            course_name = st.text_input("Course Name")
            submitted = st.form_submit_button("Add Course")

        if submitted:
            success, message = add_course(course_code, course_name)
            st.success(message) if success else st.error(message)

        courses = fetch_all_courses()

        st.markdown("### Course List")
        if courses:
            st.dataframe(pd.DataFrame(courses), use_container_width=True, hide_index=True)

            course_options = {
                f"{item['course_code']} - {item['course_name']}": item["id"]
                for item in courses
            }

            selected_course = st.selectbox("Select course to delete", list(course_options.keys()))

            if st.button("Delete Course"):
                success, message = delete_course(course_options[selected_course])
                st.success(message) if success else st.error(message)
                st.rerun()
        else:
            st.info("No courses found.")

    with tab_sections:
        st.markdown("### Add Class Section")

        courses = fetch_all_courses()
        lecturers = fetch_all_lecturers()

        if not courses or not lecturers:
            st.warning("Please create at least one course and one lecturer first.")
        else:
            course_options = {
                f"{item['course_code']} - {item['course_name']}": item["id"]
                for item in courses
            }

            lecturer_options = {
                f"{item['lecturer_code']} - {item['full_name']}": item["id"]
                for item in lecturers
            }

            with st.form("add_section_form", clear_on_submit=True):
                selected_course = st.selectbox("Course", list(course_options.keys()))
                selected_lecturer = st.selectbox("Lecturer", list(lecturer_options.keys()))
                section_code = st.text_input("Section Code")
                room = st.text_input("Room")
                start_time = st.text_input("Start Time", placeholder="07:00")
                end_time = st.text_input("End Time", placeholder="09:00")
                submitted = st.form_submit_button("Add Section")

            if submitted:
                success, message = add_section(
                    course_options[selected_course],
                    lecturer_options[selected_lecturer],
                    section_code,
                    room,
                    start_time,
                    end_time,
                )
                st.success(message) if success else st.error(message)

        sections = fetch_all_sections()

        st.markdown("### Class Section List")
        if sections:
            st.dataframe(pd.DataFrame(sections), use_container_width=True, hide_index=True)

            section_options = {
                f"{item['course_code']} - {item['section_code']}": item["id"]
                for item in sections
            }

            selected_section = st.selectbox("Select section to delete", list(section_options.keys()))

            if st.button("Delete Section"):
                success, message = delete_section(section_options[selected_section])
                st.success(message) if success else st.error(message)
                st.rerun()
        else:
            st.info("No class sections found.")

    with tab_enroll:
        st.markdown("### Enroll Student into Class")

        sections = fetch_all_sections()
        students = fetch_all_students()

        if not sections or not students:
            st.warning("Please create class sections and students first.")
        else:
            section_options = {
                f"{item['course_code']} - {item['section_code']}": item["id"]
                for item in sections
            }

            student_options = {
                f"{item['student_code']} - {item['full_name']}": item["id"]
                for item in students
            }

            selected_section = st.selectbox("Class Section", list(section_options.keys()))
            selected_student = st.selectbox("Student", list(student_options.keys()))

            if st.button("Enroll Student"):
                success, message = enroll_student(
                    section_options[selected_section],
                    student_options[selected_student],
                )
                st.success(message) if success else st.error(message)

        conn = get_connection()
        rows = conn.execute(
            """
            SELECT
                e.id,
                s.student_code,
                u.full_name,
                c.course_code,
                cs.section_code
            FROM enrollments e
            JOIN students s ON s.id = e.student_id
            JOIN users u ON u.id = s.user_id
            JOIN class_sections cs ON cs.id = e.section_id
            JOIN courses c ON c.id = cs.course_id
            ORDER BY c.course_code, cs.section_code, u.full_name
            """
        ).fetchall()
        conn.close()

        enrollment_rows = [dict(row) for row in rows]

        st.markdown("### Enrollment List")
        if enrollment_rows:
            st.dataframe(pd.DataFrame(enrollment_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No enrollments found.")
