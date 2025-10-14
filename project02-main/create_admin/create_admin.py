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
from db_conn import get_db_connection

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def create_admin():
    """Create the default admin account using PyMySQL."""
    try:
        with get_db_connection().cursor() as cursor:
            # Check if admin already exists
            cursor.execute("SELECT * FROM users WHERE school_id = %s", ("admin001",))
            existing_admin = cursor.fetchone()

            if existing_admin:
                messagebox.showwarning(
                    "Admin Exists",
                    "Admin already exists!\n\n"
                    f"Username: {existing_admin['school_id']}\n"
                    f"Role: {existing_admin['role']}\n"
                    f"Created: {existing_admin['created_at']}",
                )
                return

            # Create admin user
            password_hash = generate_password_hash("Admin123!")
            cursor.execute(
                "INSERT INTO users (school_id, password_hash, role) VALUES (%s, %s, %s)",
                ("admin001", password_hash, "admin"),
            )

        get_db_connection().commit()

        messagebox.showinfo(
            "Success",
            "Default admin account created!\n\n"
            "👤 ACCOUNT DETAILS:\n"
            "Username: admin001\n"
            "Password: Admin123!\n"
            "Role: admin\n\n"
            "🔗 DIRECT LOGIN URL:\n"
            "http://127.0.0.1:5000/admin-login?role=admin&username=admin001&password=Admin123!",
        )
    except Exception as e:
        get_db_connection().rollback()
        messagebox.showerror("Error", f"Error creating admin: {str(e)}")


def open_custom_admin_form():
    """Open a window for custom admin creation."""
    form = tk.Toplevel(root)
    form.title("Create Custom Admin")
    form.geometry("400x300")
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

    def create_custom_admin():
        school_id = school_id_entry.get().strip()
        password = password_entry.get().strip()
        confirm_password = confirm_entry.get().strip()

        if not school_id:
            messagebox.showerror("Error", "School ID cannot be empty")
            return
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters")
            return
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
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

            get_db_connection().commit()

            messagebox.showinfo(
                "Success",
                "Custom admin created!\n\n"
                f"👤 ACCOUNT DETAILS:\n"
                f"Username: {school_id}\n"
                f"Password: {password}\n"
                f"Role: admin\n\n"
                "🔗 DIRECT LOGIN URL:\n"
                f"http://127.0.0.1:5000/admin-login?role=admin&username={school_id}&password={password}",
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
