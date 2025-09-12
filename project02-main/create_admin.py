#!/usr/bin/env python3
"""
Admin Account Creation Tool (Tkinter GUI Version)
For the E-Class Record System
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User


def create_admin():
    """Create the default admin account."""
    with app.app_context():
        try:
            existing_admin = User.query.filter_by(school_id="admin001").first()
            if existing_admin:
                messagebox.showwarning(
                    "Admin Exists",
                    f"Admin already exists!\n\n"
                    f"Username: {existing_admin.school_id}\n"
                    f"Role: {existing_admin.role}\n"
                    f"Created: {existing_admin.created_at}"
                )
                return

            admin = User(school_id="admin001", role="admin")
            admin.set_password("Admin123!")

            db.session.add(admin)
            db.session.commit()

            messagebox.showinfo(
                "Success",
                "Default admin account created!\n\n"
                "👤 ACCOUNT DETAILS:\n"
                "Username: admin001\n"
                "Password: Admin123!\n"
                "Role: admin\n\n"
                "🔗 DIRECT LOGIN URL:\n"
                "http://127.0.0.1:5000/admin-login?role=admin&username=admin001&password=Admin123!"
            )
        except Exception as e:
            db.session.rollback()
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

        with app.app_context():
            try:
                existing_admin = User.query.filter_by(school_id=school_id).first()
                if existing_admin:
                    messagebox.showwarning(
                        "Exists",
                        f"Admin with ID '{school_id}' already exists!"
                    )
                    return

                admin = User(school_id=school_id, role="admin")
                admin.set_password(password)

                db.session.add(admin)
                db.session.commit()

                messagebox.showinfo(
                    "Success",
                    f"Custom admin created!\n\n"
                    f"👤 ACCOUNT DETAILS:\n"
                    f"Username: {school_id}\n"
                    f"Password: {password}\n"
                    f"Role: admin\n\n"
                    f"🔗 DIRECT LOGIN URL:\n"
                    f"http://127.0.0.1:5000/admin-login?role=admin&username={school_id}&password={password}"
                )
                form.destroy()
            except Exception as e:
                db.session.rollback()
                messagebox.showerror("Error", f"Error: {str(e)}")

    tk.Button(form, text="Create Admin", command=create_custom_admin).pack(pady=20)


# Main Window
root = tk.Tk()
root.title("E-Class Record - Admin Creator")
root.geometry("400x250")
root.resizable(False, False)

tk.Label(root, text="🔧 Admin Account Creator", font=("Arial", 14, "bold")).pack(pady=15)

ttk.Button(root, text="Create Default Admin", command=create_admin).pack(pady=10)
ttk.Button(root, text="Create Custom Admin", command=open_custom_admin_form).pack(pady=10)
ttk.Button(root, text="Exit", command=root.quit).pack(pady=10)

root.mainloop()
