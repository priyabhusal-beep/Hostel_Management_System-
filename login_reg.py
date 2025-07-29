import tkinter as tk
from tkinter import messagebox
import sqlite3
import subprocess

# --- Database setup ---
conn = sqlite3.connect("hostel.db")
cur = conn.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    phone TEXT,
    parent_name TEXT,
    parent_phone TEXT,
    course TEXT,
    password TEXT,
    role TEXT DEFAULT 'student',
    seater TEXT,
    floor INTEGER
)''')

cur.execute('''CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    complaint TEXT,
    viewed INTEGER DEFAULT 0
)''')

cur.execute('''CREATE TABLE IF NOT EXISTS leaves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    reason TEXT,
    status TEXT DEFAULT 'Pending'
)''')

cur.execute('''CREATE TABLE IF NOT EXISTS notices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    message TEXT
)''')

# --- Seater table for occupancy tracking ---
cur.execute('''
CREATE TABLE IF NOT EXISTS seaters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    floor INTEGER,
    seater_type TEXT,
    seat_no INTEGER,
    occupied_by TEXT, -- email of user or NULL
    UNIQUE(floor, seater_type, seat_no)
)
''')

# --- Initialize seaters if not already present ---
def initialize_seaters():
    # Floor 1 and 3: 1 single, 2 double, 3 triple
    # Floor 2: 2 double, 3 triple (no single)
    for floor in [1, 3]:
        # Only 1 single seater per floor
        cur.execute('INSERT OR IGNORE INTO seaters (floor, seater_type, seat_no, occupied_by) VALUES (?, ?, ?, NULL)', (floor, 'Single', 1))
        for seat_no in range(1, 2+1):  # double: 2
            cur.execute('INSERT OR IGNORE INTO seaters (floor, seater_type, seat_no, occupied_by) VALUES (?, ?, ?, NULL)', (floor, 'Double', seat_no))
        for seat_no in range(1, 3+1):  # triple: 3
            cur.execute('INSERT OR IGNORE INTO seaters (floor, seater_type, seat_no, occupied_by) VALUES (?, ?, ?, NULL)', (floor, 'Triple', seat_no))
    floor = 2
    for seat_no in range(1, 2+1):
        cur.execute('INSERT OR IGNORE INTO seaters (floor, seater_type, seat_no, occupied_by) VALUES (?, ?, ?, NULL)', (floor, 'Double', seat_no))
    for seat_no in range(1, 3+1):
        cur.execute('INSERT OR IGNORE INTO seaters (floor, seater_type, seat_no, occupied_by) VALUES (?, ?, ?, NULL)', (floor, 'Triple', seat_no))
    conn.commit()

initialize_seaters()
conn.commit()

root = tk.Tk()
root.title("Hostel Management System")
root.state('zoomed')
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

draw_gradient(canvas, "#87CEEB", "#87CEEB")

card = tk.Frame(root, bg="#fff", bd=0, relief="ridge", highlightbackground="#3b82f6", highlightthickness=2)
card.place(relx=0.5, rely=0.5, anchor="center", width=420, height=400)

def show_login():
    card.place_configure(height=400)
    for widget in card.winfo_children():
        widget.destroy()
    tk.Label(card, text="Hostel Management", font=("Segoe UI", 15, "bold"), fg="#2563eb", bg="#fff").pack(pady=(18, 2))
    tk.Label(card, text="Login", font=("Segoe UI", 12, "bold"), fg="#334155", bg="#fff").pack(pady=(0, 10))

    login_mode = tk.StringVar(value="Student")

    def set_mode_admin():
        login_mode.set("Admin")
        admin_btn.config(bg="#2563eb", fg="#fff")
        student_btn.config(bg="#f1f5f9", fg="#2563eb")
        update_fields()

    def set_mode_student():
        login_mode.set("Student")
        admin_btn.config(bg="#f1f5f9", fg="#2563eb")
        student_btn.config(bg="#2563eb", fg="#fff")
        update_fields()

    btn_frame = tk.Frame(card, bg="#fff")
    btn_frame.pack(pady=5)
    admin_btn = tk.Button(btn_frame, text="Admin", font=("Segoe UI", 10, "bold"), width=10, command=set_mode_admin, bg="#f1f5f9", fg="#2563eb", bd=0)
    admin_btn.pack(side="left", padx=2)
    student_btn = tk.Button(btn_frame, text="Student", font=("Segoe UI", 10, "bold"), width=10, command=set_mode_student, bg="#2563eb", fg="#fff", bd=0)
    student_btn.pack(side="left", padx=2)

    user_var = tk.StringVar()
    pass_var = tk.StringVar()

    user_label = tk.Label(card, text="Email", fg="#334155", bg="#fff", font=("Segoe UI", 10, "bold"))
    user_label.pack(pady=(18,2))
    user_entry = tk.Entry(card, textvariable=user_var, width=26, font=("Segoe UI", 11), bd=1, relief="solid", bg="#f1f5f9", fg="#232526", insertbackground="#232526")
    user_entry.pack(pady=2)

    tk.Label(card, text="Password", fg="#334155", bg="#fff", font=("Segoe UI", 10, "bold")).pack(pady=(8,2))
    tk.Entry(card, textvariable=pass_var, show="*", width=26, font=("Segoe UI", 11), bd=1, relief="solid", bg="#f1f5f9", fg="#232526", insertbackground="#232526").pack(pady=2)

    def update_fields():
        if login_mode.get() == "Admin":
            user_label.config(text="Admin ID")
            user_entry.delete(0, tk.END)
        else:
            user_label.config(text="Email")
            user_entry.delete(0, tk.END)

    def login_user():
        user = user_var.get().strip()
        password = pass_var.get().strip()
        if not user or not password:
            messagebox.showerror("Error", "Please enter all fields.")
            return
        if login_mode.get() == "Admin":
            if user == "0111" and password == "admin123":
                subprocess.Popen(["python", "admin_panel.py"])
                root.destroy()
            else:
                messagebox.showerror("Error", "Invalid admin credentials.")
        else:
            cur.execute("SELECT role FROM users WHERE email=? AND password=?", (user, password))
            result = cur.fetchone()
            if result:
                subprocess.Popen(["python", "student_panel.py", user])
                root.destroy()
            else:
                messagebox.showerror("Error", "Invalid student credentials.")

    tk.Button(card, text="Login", command=login_user, bg="#2563eb", fg="#fff", font=("Segoe UI", 11, "bold"), bd=0, relief="flat", width=20, height=1, activebackground="#1e293b").pack(pady=18)
    tk.Label(card, text="Don't have an account?", fg="#64748b", bg="#fff", font=("Segoe UI", 9)).pack(pady=(10,2))
    tk.Button(card, text="Register", command=show_registration, bg="#fff", fg="#2563eb", font=("Segoe UI", 10, "bold"), bd=1, relief="solid", width=13, height=1, activebackground="#f1f5f9").pack()

def show_registration():
    card.place_configure(height=850)
    for widget in card.winfo_children():
        widget.destroy()

    tk.Label(card, text="Hostel Management", font=("Segoe UI", 15, "bold"), fg="#2563eb", bg="#fff").pack(pady=(14, 2))
    tk.Label(card, text="Student Registration", font=("Segoe UI", 12, "bold"), fg="#334155", bg="#fff").pack(pady=(0, 10))

    name_var = tk.StringVar()
    email_var = tk.StringVar()
    phone_var = tk.StringVar()
    parent_name_var = tk.StringVar()
    parent_phone_var = tk.StringVar()
    course_var = tk.StringVar()
    pass_var = tk.StringVar()
    floor_var = tk.StringVar(value="1")
    seater_var = tk.StringVar(value="Single")

    fields = [
        ("Full Name", name_var),
        ("Email", email_var),
        ("Phone", phone_var),
        ("Parent Name", parent_name_var),
        ("Parent Phone", parent_phone_var),
        ("Course", course_var),
        ("Password", pass_var)
    ]

    for label, var in fields:
        tk.Label(card, text=label, fg="#334155", bg="#fff", font=("Segoe UI", 10, "bold")).pack(pady=(5,1))
        tk.Entry(card, textvariable=var, show="*" if label == "Password" else None, width=26, font=("Segoe UI", 11), bd=1, relief="solid", bg="#f1f5f9", fg="#232526", insertbackground="#232526").pack(pady=1)

    tk.Label(card, text="Floor", fg="#334155", bg="#fff", font=("Segoe UI", 10, "bold")).pack(pady=(10,2))
    floor_frame = tk.Frame(card, bg="#fff")
    floor_frame.pack(pady=1)
    for val in ["1", "2", "3"]:
        tk.Radiobutton(
            floor_frame, text=val, variable=floor_var, value=val,
            indicatoron=0, width=3, font=("Segoe UI", 10, "bold"),
            bg="#e0e7ef", fg="#2563eb", selectcolor="#2563eb", bd=0, relief="ridge"
        ).pack(side="left", padx=10)

    tk.Label(card, text="Seater", fg="#334155", bg="#fff", font=("Segoe UI", 10, "bold")).pack(pady=(10,2))
    seater_frame = tk.Frame(card, bg="#fff")
    seater_frame.pack(pady=1)
    for val in ["Single", "Double", "Triple"]:
        tk.Radiobutton(
            seater_frame, text=val, variable=seater_var, value=val,
            indicatoron=0, width=7, font=("Segoe UI", 10, "bold"),
            bg="#e0e7ef", fg="#2563eb", selectcolor="#2563eb", bd=0, relief="ridge"
        ).pack(side="left", padx=10)

    def register_user():
        values = [var.get().strip() for _, var in fields]
        floor = int(floor_var.get())
        seater = seater_var.get()
        email = values[1]

        if any(not v for v in values):
            messagebox.showerror("Error", "All fields are required.")
            return
        if email == "0111":
            messagebox.showerror("Error", "Admin ID cannot be registered here.")
            return

        # --- Seater occupancy validation using seaters table ---
        if seater == "Single":
            if floor == 2:
                messagebox.showerror("Error", "Single seater is not available on Floor 2.")
                return
            # Only 1 single seater per floor
            cur.execute('''
                SELECT id FROM seaters WHERE floor=? AND seater_type='Single'
            ''', (floor,))
            single_seat = cur.fetchone()
            if not single_seat:
                messagebox.showerror(
                    "Error",
                    f"No single seater room exists on Floor {floor}."
                )
                return
            cur.execute('''
                SELECT id FROM seaters WHERE floor=? AND seater_type='Single' AND occupied_by IS NULL
            ''', (floor,))
            available = cur.fetchone()
            if not available:
                messagebox.showerror(
                    "Error",
                    f"Single seater room on Floor {floor} is already fully occupied."
                )
                return
        else:
            cur.execute('''
                SELECT id FROM seaters WHERE floor=? AND seater_type=? AND occupied_by IS NULL
            ''', (floor, seater))
            available = cur.fetchone()
            max_allowed = {"Double": 2, "Triple": 3}[seater]
            cur.execute('SELECT COUNT(*) FROM seaters WHERE floor=? AND seater_type=?', (floor, seater))
            total = cur.fetchone()[0]
            if not available or total == 0:
                messagebox.showerror(
                    "Error",
                    f"{seater} seater on Floor {floor} is already fully occupied."
                )
                return

        try:
            cur.execute('''INSERT INTO users (name, email, phone, parent_name, parent_phone, course, password, seater, floor)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', tuple(values + [seater, floor]))
            # Mark the seat as occupied
            if seater == "Single":
                cur.execute('''
                    UPDATE seaters SET occupied_by=? WHERE floor=? AND seater_type='Single' AND occupied_by IS NULL
                ''', (email, floor))
            else:
                cur.execute('''
                    UPDATE seaters SET occupied_by=? WHERE id=(
                        SELECT id FROM seaters WHERE floor=? AND seater_type=? AND occupied_by IS NULL LIMIT 1
                    )
                ''', (email, floor, seater))
            conn.commit()
            messagebox.showinfo("Success", f"Registration successful!")
            show_login()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "This email is already registered.")

    tk.Button(card, text="Register", command=register_user, bg="#2563eb", fg="#fff",
              font=("Segoe UI", 11, "bold"), bd=0, relief="flat", width=20, height=1,
              activebackground="#1e293b").pack(pady=16)

    tk.Label(card, text="Already have an account?", fg="#64748b", bg="#fff",
             font=("Segoe UI", 9)).pack(pady=(10,2))

    tk.Button(card, text="Login", command=lambda: [card.place_configure(height=400), show_login()],
              bg="#fff", fg="#2563eb", font=("Segoe UI", 10, "bold"), bd=1, relief="solid",
              width=13, height=1, activebackground="#f1f5f9").pack(pady=(0,30))

show_login()
root.mainloop()