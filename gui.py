"""
ACEest Fitness & Performance - Tkinter frontend (Aceestver-3.1.2).
Login, Client Management, Membership Expiry, AI Program Generator, PDF Export via Flask API.
Start Flask first (python app.py).
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, date
from urllib.parse import quote
import random

try:
    import requests
except ImportError:
    requests = None

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

API_BASE = "http://localhost:5000"


class ACEestApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ACEest Fitness & Performance")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1a1a1a")

        self.current_client = None
        self.current_user = None
        self.user_role = None

        self.setup_data()
        self.show_login_window()

    # ---------- DATA (program factors from API or fallback) ----------
    def setup_data(self):
        """Load program list and factors from Flask API or use fallback."""
        self.programs = {
            "Fat Loss (FL) – 3 day": {"factor": 22, "desc": "3-day full-body fat loss"},
            "Fat Loss (FL) – 5 day": {"factor": 24, "desc": "5-day split, higher volume fat loss"},
            "Muscle Gain (MG) – PPL": {"factor": 35, "desc": "Push/Pull/Legs hypertrophy"},
            "Beginner (BG)": {"factor": 26, "desc": "3-day simple beginner full-body"},
        }
        if requests:
            try:
                r = requests.get(f"{API_BASE}/api/programs", timeout=5)
                r.raise_for_status()
                names = r.json()
                for name in names:
                    r2 = requests.get(f"{API_BASE}/api/program/{quote(name)}", timeout=5)
                    if r2.status_code == 200:
                        data = r2.json()
                        self.programs[name] = {
                            "factor": data.get("calorie_factor", 0),
                            "desc": data.get("desc", ""),
                        }
            except Exception:
                pass

    # ---------- LOGIN ----------
    def show_login_window(self):
        self.root.withdraw()
        self.login_win = tk.Toplevel(self.root)
        self.login_win.title("Login")
        self.login_win.geometry("300x200")
        self.login_win.configure(bg="#1a1a1a")
        self.login_win.protocol("WM_DELETE_WINDOW", self.on_login_close)

        tk.Label(self.login_win, text="Username", bg="#1a1a1a", fg="white").pack(pady=(20, 5))
        self.username_var = tk.StringVar()
        tk.Entry(self.login_win, textvariable=self.username_var, bg="#333", fg="white").pack()

        tk.Label(self.login_win, text="Password", bg="#1a1a1a", fg="white").pack(pady=(10, 5))
        self.password_var = tk.StringVar()
        tk.Entry(self.login_win, textvariable=self.password_var, show="*", bg="#333", fg="white").pack()

        ttk.Button(self.login_win, text="Login", command=self.login_user).pack(pady=20)

        self.login_win.transient(self.root)
        self.login_win.grab_set()
        self.login_win.focus_set()

    def on_login_close(self):
        self.root.destroy()

    def login_user(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        if not requests:
            messagebox.showerror("Login Failed", "requests library required")
            return
        try:
            r = requests.post(
                f"{API_BASE}/api/login",
                json={"username": username, "password": password},
                timeout=5,
            )
            if r.status_code == 200:
                data = r.json()
                self.user_role = data.get("role", "User")
                self.current_user = data.get("username", username)
                self.login_win.grab_release()
                self.login_win.destroy()
                self.root.deiconify()
                self.setup_ui()
                self.refresh_client_list()
            else:
                messagebox.showerror("Login Failed", "Invalid credentials\nTry admin / admin")
        except Exception as e:
            messagebox.showerror("Login Failed", f"Could not reach server\n{e}")

    # ---------- UI ----------
    def setup_ui(self):
        header = tk.Label(
            self.root,
            text=f"ACEest Fitness Dashboard ({self.user_role})",
            bg="#d4af37",
            fg="black",
            font=("Helvetica", 24, "bold"),
            height=2,
        )
        header.pack(fill="x")

        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bg="#111111",
            fg="#d4af37",
            anchor="w",
        )
        status_bar.pack(side="bottom", fill="x")

        main = tk.Frame(self.root, bg="#1a1a1a")
        main.pack(fill="both", expand=True, padx=10, pady=10)

        left = tk.LabelFrame(
            main,
            text=" Client Management ",
            bg="#1a1a1a",
            fg="#d4af37",
            font=("Arial", 12, "bold"),
        )
        left.pack(side="left", fill="y", padx=10, pady=5)

        tk.Label(left, text="Select Client", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.client_list = ttk.Combobox(left, state="readonly")
        self.client_list.pack(pady=(0, 5))
        self.client_list.bind("<<ComboboxSelected>>", self.on_client_selected)

        tk.Label(left, text="Name", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.name = tk.StringVar()
        tk.Entry(left, textvariable=self.name, bg="#333", fg="white").pack()

        tk.Label(left, text="Age", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.age = tk.IntVar()
        tk.Entry(left, textvariable=self.age, bg="#333", fg="white").pack()

        tk.Label(left, text="Height (cm)", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.height = tk.DoubleVar()
        tk.Entry(left, textvariable=self.height, bg="#333", fg="white").pack()

        tk.Label(left, text="Weight (kg)", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.weight = tk.DoubleVar()
        tk.Entry(left, textvariable=self.weight, bg="#333", fg="white").pack()

        tk.Label(left, text="Program", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.program = tk.StringVar()
        ttk.Combobox(
            left,
            textvariable=self.program,
            values=list(self.programs.keys()),
            state="readonly",
        ).pack()

        tk.Label(
            left,
            text="Membership Expiry (YYYY-MM-DD)",
            bg="#1a1a1a",
            fg="white",
        ).pack(pady=(10, 0))
        self.membership_var = tk.StringVar()
        tk.Entry(left, textvariable=self.membership_var, bg="#333", fg="white").pack()

        ttk.Button(left, text="Save Client", command=self.save_client).pack(pady=5)
        ttk.Button(left, text="Load Client", command=self.load_client).pack(pady=5)
        ttk.Button(left, text="Generate AI Program", command=self.generate_ai_program).pack(pady=5)
        ttk.Button(left, text="Export PDF Report", command=self.export_pdf_report).pack(pady=5)

        right = tk.Frame(main, bg="#1a1a1a")
        right.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        notebook = ttk.Notebook(right)
        notebook.pack(fill="both", expand=True)

        summary_frame = tk.Frame(notebook, bg="#1a1a1a")
        notebook.add(summary_frame, text="Client Summary")
        self.summary = tk.Text(summary_frame, bg="#111", fg="white", font=("Consolas", 11))
        self.summary.pack(fill="both", expand=True, padx=10, pady=10)

        analytics_frame = tk.Frame(notebook, bg="#1a1a1a")
        notebook.add(analytics_frame, text="Progress & Analytics")

        if HAS_MATPLOTLIB:
            self.fig, self.ax = plt.subplots(figsize=(6, 4))
            self.ax.set_visible(False)
            self.canvas = FigureCanvasTkAgg(self.fig, master=analytics_frame)
            self.canvas.get_tk_widget().pack(pady=10, fill="both", expand=True)
        else:
            tk.Label(analytics_frame, text="(Install matplotlib for charts)", bg="#1a1a1a", fg="gray").pack(pady=10)

        self.program_tree = ttk.Treeview(
            analytics_frame,
            columns=("day", "exercise", "sets", "reps"),
            show="headings",
        )
        for col in ("day", "exercise", "sets", "reps"):
            self.program_tree.heading(col, text=col.capitalize())
        self.program_tree.pack(fill="both", expand=True, pady=10)

        self.refresh_client_list()

    # ---------- HELPERS ----------
    def _api_get(self, path):
        if not requests:
            return None
        try:
            r = requests.get(f"{API_BASE}{path}", timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    def _api_post(self, path, json_data):
        if not requests:
            return None
        try:
            r = requests.post(f"{API_BASE}{path}", json=json_data, timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    def set_status(self, text):
        self.status_var.set(text)

    # ---------- CLIENT MANAGEMENT ----------
    def refresh_client_list(self):
        data = self._api_get("/api/clients")
        names = []
        if data is not None:
            names = [c.get("name") for c in data if c.get("name")]
            names.sort()
        self.client_list["values"] = names
        if self.current_client and self.current_client in names:
            self.client_list.set(self.current_client)

    def on_client_selected(self, event=None):
        self.current_client = self.client_list.get()
        if self.current_client:
            self.load_client()

    def save_client(self):
        name = self.name.get().strip()
        if not name:
            messagebox.showerror("Error", "Name required")
            return
        program = self.program.get() or ""
        age = self.age.get() if self.age.get() else None
        height = self.height.get() if self.height.get() else None
        weight = self.weight.get() if self.weight.get() else None
        membership = self.membership_var.get().strip() or None
        factor = self.programs.get(program, {}).get("factor", 25)
        calories = int(weight * factor) if weight and weight > 0 else None
        payload = {
            "name": name,
            "age": age,
            "height": height,
            "weight": weight,
            "program": program or "Beginner (BG)",
            "calories": calories,
            "membership_expiry": membership or "",
        }
        result = self._api_post("/api/clients", payload)
        if result is not None:
            self.current_client = name
            self.refresh_client_list()
            self.set_status(f"Saved client: {name}")
            messagebox.showinfo("Saved", "Client data saved")
        else:
            messagebox.showerror("Error", "Could not save client. Is Flask running?")

    def load_client(self):
        if not self.current_client:
            return
        data = self._api_get(f"/api/clients/{quote(self.current_client)}")
        if data is None or data.get("error"):
            return
        self.name.set(data.get("name", ""))
        self.age.set(data.get("age") if data.get("age") is not None else 0)
        self.height.set(data.get("height") if data.get("height") is not None else 0)
        self.weight.set(data.get("weight") if data.get("weight") is not None else 0)
        self.program.set(data.get("program") or "")
        self.membership_var.set(data.get("membership_expiry") or "")
        self.refresh_summary()

    def refresh_summary(self):
        if not self.current_client:
            return
        data = self._api_get(f"/api/clients/{quote(self.current_client)}")
        if not data or data.get("error"):
            return
        self.summary.configure(state="normal")
        self.summary.delete("1.0", "end")
        self.summary.insert(
            "end",
            f"Name: {data.get('name', '')}\n"
            f"Age: {data.get('age', '')}\n"
            f"Height: {data.get('height', '')} cm\n"
            f"Weight: {data.get('weight', '')} kg\n"
            f"Program: {data.get('program', '')}\n"
            f"Membership Expiry: {data.get('membership_expiry', '')}",
        )
        self.summary.configure(state="disabled")

    # ---------- AI PROGRAM GENERATOR ----------
    def generate_ai_program(self):
        if not self.current_client:
            messagebox.showerror("Error", "Select client first")
            return
        exp_level = simpledialog.askstring(
            "Experience",
            "Enter experience (beginner/intermediate/advanced):",
            parent=self.root,
        )
        if not exp_level or exp_level.lower() not in ("beginner", "intermediate", "advanced"):
            messagebox.showerror("Error", "Invalid experience level")
            return
        program_name = self.program.get() or ""

        exercises_pool = {
            "Strength": [
                "Squat", "Deadlift", "Bench Press", "Overhead Press", "Pull-Up", "Barbell Row",
            ],
            "Hypertrophy": [
                "Leg Press", "Incline Dumbbell Press", "Lat Pulldown",
                "Lateral Raise", "Bicep Curl", "Tricep Extension",
            ],
            "Conditioning": [
                "Running", "Cycling", "Rowing", "Burpees", "Jump Rope", "Kettlebell Swings",
            ],
            "Full Body": [
                "Push-Up", "Pull-Up", "Lunge", "Plank", "Dumbbell Row", "Dumbbell Press",
            ],
        }

        focus = "Full Body"
        if "Fat Loss" in program_name:
            focus = "Conditioning"
        elif "Muscle Gain" in program_name:
            focus = "Hypertrophy"

        if exp_level.lower() == "beginner":
            sets_range = (2, 3)
            reps_range = (8, 12)
            days = 3
        elif exp_level.lower() == "intermediate":
            sets_range = (3, 4)
            reps_range = (8, 15)
            days = 4
        else:
            sets_range = (4, 5)
            reps_range = (6, 15)
            days = 5

        weekly_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][:days]

        for item in self.program_tree.get_children():
            self.program_tree.delete(item)

        for day in weekly_days:
            n_ex = 3 if days < 4 else 4
            exercises = random.sample(exercises_pool[focus], k=min(n_ex, len(exercises_pool[focus])))
            for ex in exercises:
                sets = random.randint(*sets_range)
                reps = random.randint(*reps_range)
                self.program_tree.insert("", "end", values=(day, ex, sets, reps))

        self.set_status(f"AI program generated for {self.current_client}")
        messagebox.showinfo("Generated", "AI workout program generated!")

    # ---------- PDF REPORT ----------
    def export_pdf_report(self):
        if not self.current_client:
            messagebox.showwarning("No Client", "Select client first")
            return
        if not HAS_FPDF:
            messagebox.showerror("Error", "Install fpdf to export PDF: pip install fpdf2")
            return
        data = self._api_get(f"/api/clients/{quote(self.current_client)}")
        if not data or data.get("error"):
            messagebox.showerror("Error", "Could not load client")
            return
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"Client Report - {self.current_client}", ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.ln(10)
        pdf.cell(0, 10, f"Name: {data.get('name', '')}", ln=True)
        pdf.cell(0, 10, f"Age: {data.get('age', '')}", ln=True)
        pdf.cell(0, 10, f"Height: {data.get('height', '')} cm", ln=True)
        pdf.cell(0, 10, f"Weight: {data.get('weight', '')} kg", ln=True)
        pdf.cell(0, 10, f"Program: {data.get('program', '')}", ln=True)
        pdf.cell(0, 10, f"Membership Expiry: {data.get('membership_expiry', '')}", ln=True)
        filename = f"{self.current_client}_report.pdf"
        pdf.output(filename)
        messagebox.showinfo("PDF Exported", f"Report saved as {filename}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ACEestApp(root)
    root.mainloop()
