#!/usr/bin/env python3
"""
Admin Account Creation Tool (PyMySQL Version)
For the E-Class Record System
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Add parent directory to path to import db_conn
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
)

DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin001")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD")
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "programmingproject06@gmail.com")
DEFAULT_ADMIN_FIRST_NAME = os.getenv("DEFAULT_ADMIN_FIRST_NAME", "System")
DEFAULT_ADMIN_LAST_NAME = os.getenv("DEFAULT_ADMIN_LAST_NAME", "Administrator")
DEFAULT_ADMIN_DEPARTMENT = os.getenv("DEFAULT_ADMIN_DEPARTMENT", "Administration")

from utils.db_conn import get_db_connection


def _ensure_admin_email_profile(cursor, user_id, admin_email):
    """Ensure admin has instructor/personal_info linkage with an email for MFA."""
    cursor.execute(
        """
        SELECT i.id AS instructor_id, i.personal_info_id, pi.email
        FROM instructors i
        LEFT JOIN personal_info pi ON i.personal_info_id = pi.id
        WHERE i.user_id = %s
        LIMIT 1
        """,
        (user_id,),
    )
    instructor_row = cursor.fetchone()

    if instructor_row and instructor_row.get("personal_info_id"):
        personal_info_id = instructor_row["personal_info_id"]
        current_email = (instructor_row.get("email") or "").strip()
        if not current_email:
            cursor.execute(
                "UPDATE personal_info SET email = %s WHERE id = %s",
                (admin_email, personal_info_id),
            )
            return admin_email
        return current_email

    cursor.execute(
        """
        INSERT INTO personal_info (first_name, last_name, email)
        VALUES (%s, %s, %s)
        """,
        (DEFAULT_ADMIN_FIRST_NAME, DEFAULT_ADMIN_LAST_NAME, admin_email),
    )
    personal_info_id = cursor.lastrowid

    if instructor_row and instructor_row.get("instructor_id"):
        cursor.execute(
            """
            UPDATE instructors
            SET personal_info_id = %s, department = COALESCE(department, %s)
            WHERE id = %s
            """,
            (
                personal_info_id,
                DEFAULT_ADMIN_DEPARTMENT,
                instructor_row["instructor_id"],
            ),
        )
    else:
        cursor.execute(
            """
            INSERT INTO instructors (user_id, personal_info_id, department, status)
            VALUES (%s, %s, %s, 'active')
            """,
            (user_id, personal_info_id, DEFAULT_ADMIN_DEPARTMENT),
        )

    return admin_email


def create_admin():
    """Create the default admin account using PyMySQL."""
    if not DEFAULT_ADMIN_PASSWORD:
        messagebox.showerror(
            "Missing Configuration",
            "DEFAULT_ADMIN_PASSWORD is not set in .env. Please set it before creating the default admin.",
        )
        return

    try:
        with get_db_connection().cursor() as cursor:
            # Check if admin already exists
            cursor.execute(
                "SELECT * FROM users WHERE school_id = %s", (DEFAULT_ADMIN_USERNAME,)
            )
            existing_admin = cursor.fetchone()

            if existing_admin:
                linked_email = _ensure_admin_email_profile(
                    cursor,
                    existing_admin["id"],
                    DEFAULT_ADMIN_EMAIL,
                )
                get_db_connection().commit()
                messagebox.showwarning(
                    "Admin Exists",
                    "Admin already exists!\n\n"
                    f"Username: {existing_admin['school_id']}\n"
                    f"Role: {existing_admin['role']}\n"
                    f"Created: {existing_admin['created_at']}\n"
                    f"Email (for MFA): {linked_email}",
                )
                return

            # Create admin user
            password_hash = generate_password_hash(DEFAULT_ADMIN_PASSWORD)
            cursor.execute(
                "INSERT INTO users (school_id, password_hash, role) VALUES (%s, %s, %s)",
                (DEFAULT_ADMIN_USERNAME, password_hash, "admin"),
            )
            admin_user_id = cursor.lastrowid

            linked_email = _ensure_admin_email_profile(
                cursor,
                admin_user_id,
                DEFAULT_ADMIN_EMAIL,
            )

        get_db_connection().commit()

        messagebox.showinfo(
            "Success",
            "Default admin account created!\n\n"
            "👤 ACCOUNT DETAILS:\n"
            f"Username: {DEFAULT_ADMIN_USERNAME}\n"
            "Password: [from DEFAULT_ADMIN_PASSWORD in .env]\n"
            "Role: admin\n"
            f"Email: {linked_email}\n\n"
            "🔗 LOGIN URL:\n"
            "http://127.0.0.1:5000/adminlogin",
        )
    except Exception as e:
        get_db_connection().rollback()
        messagebox.showerror("Error", f"Error creating admin: {str(e)}")


def open_custom_admin_form():
    """Open a window for custom admin creation."""
    form = tk.Toplevel(root)
    form.title("Create Custom Admin")
    form.geometry("420x360")
    form.resizable(False, False)

    # Labels + Entries
    tk.Label(form, text="School ID:").pack(pady=5)
    school_id_entry = tk.Entry(form, width=30)
    school_id_entry.pack()

    tk.Label(form, text="Password:").pack(pady=5)
    password_entry = tk.Entry(form, show="*", width=30)
    password_entry.pack()

    tk.Label(form, text="Confirm Password:").pack(pady=5)
    confirm_entry = tk.Entry(form, show="*", width=30)
    confirm_entry.pack()

    tk.Label(form, text="Email:").pack(pady=5)
    email_entry = tk.Entry(form, width=30)
    email_entry.insert(0, DEFAULT_ADMIN_EMAIL)
    email_entry.pack()

    def create_custom_admin():
        school_id = school_id_entry.get().strip()
        password = password_entry.get().strip()
        confirm_password = confirm_entry.get().strip()
        admin_email = email_entry.get().strip() or DEFAULT_ADMIN_EMAIL

        if not school_id:
            messagebox.showerror("Error", "School ID cannot be empty")
            return
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters")
            return
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return
        if "@" not in admin_email:
            messagebox.showerror("Error", "Please enter a valid email address")
            return

        try:
            with get_db_connection().cursor() as cursor:
                # Check if admin already exists
                cursor.execute("SELECT * FROM users WHERE school_id = %s", (school_id,))
                existing_admin = cursor.fetchone()

                if existing_admin:
                    messagebox.showwarning(
                        "Exists", f"Admin with ID '{school_id}' already exists!"
                    )
                    return

                # Create custom admin user
                password_hash = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO users (school_id, password_hash, role) VALUES (%s, %s, %s)",
                    (school_id, password_hash, "admin"),
                )
                admin_user_id = cursor.lastrowid

                linked_email = _ensure_admin_email_profile(
                    cursor,
                    admin_user_id,
                    admin_email,
                )

            get_db_connection().commit()

            messagebox.showinfo(
                "Success",
                "Custom admin created!\n\n"
                f"👤 ACCOUNT DETAILS:\n"
                f"Username: {school_id}\n"
                "Password: [hidden for security]\n"
                f"Role: admin\n"
                f"Email: {linked_email}\n\n"
                "🔗 LOGIN URL:\n"
                "http://127.0.0.1:5000/adminlogin",
            )
            form.destroy()
        except Exception as e:
            get_db_connection().rollback()
            messagebox.showerror("Error", f"Error: {str(e)}")

    tk.Button(form, text="Create Admin", command=create_custom_admin).pack(pady=20)


# Main Window
root = tk.Tk()
root.title("E-Class Record - Admin Creator")
root.geometry("400x250")
root.resizable(False, False)

tk.Label(root, text="🔧 Admin Account Creator", font=("Arial", 14, "bold")).pack(
    pady=15
)

ttk.Button(root, text="Create Default Admin", command=create_admin).pack(pady=10)
ttk.Button(root, text="Create Custom Admin", command=open_custom_admin_form).pack(
    pady=10
)
ttk.Button(root, text="Exit", command=root.quit).pack(pady=10)

root.mainloop()
