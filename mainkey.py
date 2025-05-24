import tkinter as tk
from tkinter import messagebox, simpledialog
import pymysql
import hashlib
import subprocess

def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='license_system'
    )

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_license(license_key_input):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM license_keys WHERE license_key = %s AND is_active = 1"
            cursor.execute(sql, (license_key_input,))
            result = cursor.fetchone()
            return result is not None
    finally:
        connection.close()


def verify_admin_login(username, password):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT password_hash FROM admin_users WHERE username = %s", (username,))
            result = cursor.fetchone()
            if result:
                return result[0] == hash_password(password)
            return False
    finally:
        connection.close()

def launch_main_program():
    subprocess.Popen(['python', 'main.py'])

def validate_key():
    key = license_entry.get().strip()
    if check_license(key):
        messagebox.showinfo("สำเร็จ", "License ถูกต้อง! เปิดโปรแกรมได้เลย")
        root.destroy()
        launch_main_program()
    else:
        messagebox.showerror("ผิดพลาด", "License key ไม่ถูกต้อง หรือหมดอายุ")


def open_admin_login_window():
    login_win = tk.Toplevel()
    login_win.title("เข้าสู่ระบบแอดมิน")

    tk.Label(login_win, text="Username:").pack(pady=5)
    username_entry = tk.Entry(login_win)
    username_entry.pack(pady=5)

    tk.Label(login_win, text="Password:").pack(pady=5)
    password_entry = tk.Entry(login_win, show="*")
    password_entry.pack(pady=5)

    def attempt_login():
        username = username_entry.get()
        password = password_entry.get()
        if verify_admin_login(username, password):
            messagebox.showinfo("สำเร็จ", "เข้าสู่ระบบสำเร็จ", parent=login_win)
            login_win.destroy()
            open_admin_dashboard()
        else:
            messagebox.showerror("ผิดพลาด", "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง", parent=login_win)

    tk.Button(login_win, text="เข้าสู่ระบบ", command=attempt_login).pack(pady=10)


def open_admin_dashboard():
    admin_win = tk.Toplevel()
    admin_win.title("Admin Dashboard")

    listbox = tk.Listbox(admin_win, width=50)
    listbox.pack(pady=10)

    def refresh_list():
        listbox.delete(0, tk.END)
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, license_key, is_active FROM license_keys")
                for row in cursor.fetchall():
                    status = "✅" if row[2] else "❌"
                    listbox.insert(tk.END, f"[ID:{row[0]}] {row[1]} {status}")
        finally:
            connection.close()

    def add_key():
        new_key = simpledialog.askstring("เพิ่มคีย์", "ใส่ License Key ใหม่:", parent=admin_win)
        if new_key:
            connection = get_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("INSERT INTO license_keys (license_key, is_active) VALUES (%s, 1)", (new_key,))
                    connection.commit()
                    refresh_list()
            finally:
                connection.close()

    def delete_key():
        selection = listbox.curselection()
        if selection:
            key_text = listbox.get(selection[0])
            key_id = int(key_text.split(']')[0].split(':')[1])
            connection = get_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM license_keys WHERE id = %s", (key_id,))
                    connection.commit()
                    refresh_list()
            finally:
                connection.close()

    def toggle_status():
        selection = listbox.curselection()
        if selection:
            key_text = listbox.get(selection[0])
            key_id = int(key_text.split(']')[0].split(':')[1])
            connection = get_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT is_active FROM license_keys WHERE id = %s", (key_id,))
                    current = cursor.fetchone()[0]
                    new_status = 0 if current else 1
                    cursor.execute("UPDATE license_keys SET is_active = %s WHERE id = %s", (new_status, key_id))
                    connection.commit()
                    refresh_list()
            finally:
                connection.close()

    tk.Button(admin_win, text="เพิ่มคีย์", command=add_key).pack(pady=5)
    tk.Button(admin_win, text="ลบคีย์", command=delete_key).pack(pady=5)
    tk.Button(admin_win, text="สลับสถานะใช้งาน", command=toggle_status).pack(pady=5)

    refresh_list()

root = tk.Tk()
root.title("Check License Key")

tk.Label(root, text="กรุณาใส่ License Key:").pack(pady=10)
license_entry = tk.Entry(root, width=40)
license_entry.pack(pady=5)

tk.Button(root, text="ตรวจสอบ Key", command=validate_key).pack(pady=10)
tk.Button(root, text="เข้าสู่ระบบแอดมิน", command=open_admin_login_window).pack(pady=5)

root.mainloop()
