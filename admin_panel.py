import tkinter as tk
from tkinter import messagebox
import sqlite3

# -- DB Connection --
conn = sqlite3.connect("hostel.db")
cur = conn.cursor()

# Alter table users to add new columns if they don't exist
try:
    cur.execute("ALTER TABLE users ADD COLUMN floor INTEGER")
except sqlite3.OperationalError:
    pass
try:
    cur.execute("ALTER TABLE users ADD COLUMN seater TEXT")
except sqlite3.OperationalError:
    pass
try:
    cur.execute("ALTER TABLE complaints ADD COLUMN viewed INTEGER DEFAULT 0")
except sqlite3.OperationalError:
    pass

# -- GUI Setup --
root = tk.Tk()
root.title("Admin Panel")
root.state('zoomed')  # Maximized window
root.resizable(False, False)

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# --- Gradient background ---
def draw_gradient(canvas, color1, color2):
    width = screen_width
    height = screen_height
    r1, g1, b1 = root.winfo_rgb(color1)
    r2, g2, b2 = root.winfo_rgb(color2)
    r_ratio = float(r2 - r1) / height
    g_ratio = float(g2 - g1) / height
    b_ratio = float(b2 - b1) / height
    for i in range(height):
        nr = int(r1 + (r_ratio * i))
        ng = int(g1 + (g_ratio * i))
        nb = int(b1 + (b_ratio * i))
        color = "#%04x%04x%04x" % (nr, ng, nb)
        canvas.create_line(0, i, width, i, fill=color)

canvas = tk.Canvas(root, width=screen_width, height=screen_height, highlightthickness=0)
canvas.place(x=0, y=0)
draw_gradient(canvas, "#a1c4fd", "#c2e9fb")  # blue gradient

# --- Main Card Frame ---
main_frame = tk.Frame(root, bg="#fff", bd=0, relief="ridge", highlightbackground="#3b82f6", highlightthickness=2)
main_frame.place(relx=0.5, rely=0.5, anchor="center", width=500, height=600)

tk.Label(main_frame, text="👨‍💼 Admin Dashboard", font=("Segoe UI", 20, "bold"), fg="#2563eb", bg="#fff").pack(pady=20)

# === Features ===

def approve_leaves():
    win = tk.Toplevel(root)
    win.title("Approve Leaves")
    win.geometry("400x300")
    win.configure(bg="#e0e7ef")
    tk.Label(win, text="Pending Leave Requests", bg="#e0e7ef", fg="#2563eb", font=("Segoe UI", 12, "bold")).pack(pady=10)

    cur.execute("SELECT id, email, reason FROM leaves WHERE status='Pending'")
    leaves = cur.fetchall()

    def approve(lid):
        cur.execute("UPDATE leaves SET status='Approved' WHERE id=?", (lid,))
        conn.commit()
        messagebox.showinfo("Done", "Leave Approved")
        win.destroy()

    def reject(lid):
        cur.execute("UPDATE leaves SET status='Rejected' WHERE id=?", (lid,))
        conn.commit()
        messagebox.showinfo("Done", "Leave Rejected")
        win.destroy()

    for leave in leaves:
        frame = tk.Frame(win, bg="#e0e7ef")
        frame.pack(pady=5, fill="x")
        tk.Label(frame, text=f"{leave[1]}: {leave[2]}", bg="#e0e7ef", fg="#2563eb").pack(side=tk.LEFT)
        tk.Button(frame, text="✅", command=lambda lid=leave[0]: approve(lid), bg="#27ae60", fg="white").pack(side=tk.RIGHT, padx=2)
        tk.Button(frame, text="❌", command=lambda lid=leave[0]: reject(lid), bg="#c0392b", fg="white").pack(side=tk.RIGHT, padx=2)

def assign_room():
    def assign():
        if not email.get() or not floor.get() or not seater.get():
            messagebox.showerror("Error", "All fields are required.")
            return
        cur.execute("UPDATE users SET floor=?, seater=? WHERE email=?", (int(floor.get()), seater.get(), email.get()))
        conn.commit()
        messagebox.showinfo("Done", f"Floor {floor.get()} and Seater {seater.get()} assigned to {email.get()}.")
        win.destroy()

    win = tk.Toplevel(root)
    win.title("Assign Room")
    win.geometry("350x220")
    win.configure(bg="#e0e7ef")
    email = tk.StringVar()
    floor = tk.StringVar()
    seater = tk.StringVar()
    tk.Label(win, text="Student Email", bg="#e0e7ef", fg="#2563eb").pack(pady=5)
    tk.Entry(win, textvariable=email, bg="#fff", fg="#232526").pack()
    tk.Label(win, text="Floor (1, 2, 3)", bg="#e0e7ef", fg="#2563eb").pack(pady=5)
    tk.Entry(win, textvariable=floor, bg="#fff", fg="#232526").pack()
    tk.Label(win, text="Seater (Single, Double, Triple)", bg="#e0e7ef", fg="#2563eb").pack(pady=5)
    tk.Entry(win, textvariable=seater, bg="#fff", fg="#232526").pack()
    tk.Button(win, text="Assign", command=assign, bg="#27ae60", fg="white").pack(pady=10)

def remove_student():
    def remove():
        cur.execute("DELETE FROM users WHERE email=?", (email.get(),))
        conn.commit()
        messagebox.showinfo("Removed", "Student removed.")
        win.destroy()

    win = tk.Toplevel(root)
    win.title("Remove Student")
    win.geometry("300x150")
    win.configure(bg="#e0e7ef")
    email = tk.StringVar()
    tk.Label(win, text="Student Email", bg="#e0e7ef", fg="#2563eb").pack(pady=10)
    tk.Entry(win, textvariable=email, bg="#fff", fg="#232526").pack()
    tk.Button(win, text="Remove", command=remove, bg="#c0392b", fg="white").pack(pady=10)

def view_complaints():
    win = tk.Toplevel(root)
    win.title("Student Complaints")
    win.geometry("400x350")
    win.configure(bg="#e0e7ef")
    tk.Label(win, text="Unviewed Complaints", bg="#e0e7ef", fg="#2563eb", font=("Segoe UI", 12, "bold")).pack(pady=10)
    cur.execute("SELECT id, email, complaint FROM complaints WHERE viewed=0")
    unviewed = cur.fetchall()
    for cid, email, msg in unviewed:
        frame = tk.Frame(win, bg="#e0e7ef")
        frame.pack(fill="x", pady=2)
        tk.Label(frame, text=f"{email}: {msg}", bg="#e0e7ef", fg="#2563eb").pack(side=tk.LEFT)
        tk.Button(frame, text="Mark as Viewed", command=lambda cid=cid: mark_viewed(cid, win), bg="#27ae60", fg="white").pack(side=tk.RIGHT, padx=5)
    tk.Label(win, text="Viewed Complaints", bg="#e0e7ef", fg="#2563eb", font=("Segoe UI", 12, "bold")).pack(pady=10)
    cur.execute("SELECT email, complaint FROM complaints WHERE viewed=1")
    viewed = cur.fetchall()
    for email, msg in viewed:
        tk.Label(win, text=f"{email}: {msg}", bg="#e0e7ef", fg="#2563eb").pack(anchor="w", padx=10)

def mark_viewed(cid, win):
    cur.execute("UPDATE complaints SET viewed=1 WHERE id=?", (cid,))
    conn.commit()
    messagebox.showinfo("Done", "Complaint marked as viewed.")
    win.destroy()
    view_complaints()

def view_students():
    win = tk.Toplevel(root)
    win.title("All Students")
    win.geometry("650x400")
    win.configure(bg="#e0e7ef")
    tk.Label(win, text="Students List", font=("Segoe UI", 14, "bold"), bg="#e0e7ef", fg="#2563eb").pack(pady=10)
    frame = tk.Frame(win, bg="#e0e7ef")
    frame.pack(fill="both", expand=True)
    cur.execute("SELECT name, email, floor, seater FROM users WHERE role='student'")
    students = cur.fetchall()
    for idx, (name, email, floor, seater) in enumerate(students):
        tk.Label(frame, text=f"{idx+1}. {name} | {email} | Floor: {floor} | Seater: {seater}",
                 bg="#e0e7ef", fg="#2563eb", anchor="w").pack(fill="x", padx=10, pady=2)

# === Logout with confirmation ===
def logout():
    confirm = messagebox.askyesno("Logout Confirmation", "Are you sure you want to logout?")
    if confirm:
        root.destroy()

# === Buttons ===
btn_frame = tk.Frame(main_frame, bg="#fff")
btn_frame.pack(pady=20)

tk.Button(btn_frame, text="Approve Leave", command=approve_leaves,
          bg="#27ae60", fg="white", font=("Segoe UI", 11, "bold"), width=22, height=2).pack(pady=7, fill="x")
tk.Button(btn_frame, text="Assign Room", command=assign_room,
          bg="#3498db", fg="white", font=("Segoe UI", 11, "bold"), width=22, height=2).pack(pady=7, fill="x")
tk.Button(btn_frame, text="Remove Student", command=remove_student,
          bg="#c0392b", fg="white", font=("Segoe UI", 11, "bold"), width=22, height=2).pack(pady=7, fill="x")
tk.Button(btn_frame, text="View Complaints", command=view_complaints,
          bg="#f39c12", fg="white", font=("Segoe UI", 11, "bold"), width=22, height=2).pack(pady=7, fill="x")
tk.Button(btn_frame, text="View All Students", command=view_students,
          bg="#8e44ad", fg="white", font=("Segoe UI", 11, "bold"), width=22, height=2).pack(pady=7, fill="x")
tk.Button(main_frame, text="Logout", command=logout,
          bg="#7f8c8d", fg="white", font=("Segoe UI", 11, "bold"), width=10, height=1).pack(pady=20)

root.mainloop()