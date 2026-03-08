"""
ACEest Fitness & Performance - Tkinter frontend (Aceestver-3.2.4).
Login on root, Dashboard with Client Summary + adherence chart, Workouts tab, Check Membership, PDF via Flask API.
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

        self.current_user = None
        self.current_role = None
        self.current_client = None

        self.program_templates = {
            "Fat Loss": ["Full Body HIIT", "Circuit Training", "Cardio + Weights"],
            "Muscle Gain": ["Push/Pull/Legs", "Upper/Lower Split", "Full Body Strength"],
            "Beginner": ["Full Body 3x/week", "Light Strength + Mobility"],
        }

        self.login_screen()

    # ---------- UTILITY ----------
    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # ---------- LOGIN ----------
    def login_screen(self):
        self.clear_root()
        frame = tk.Frame(self.root, bg="#1a1a1a")
        frame.pack(expand=True)

        tk.Label(frame, text="ACEest Login", font=("Arial", 24), fg="#d4af37", bg="#1a1a1a").pack(pady=20)
        tk.Label(frame, text="Username", fg="white", bg="#1a1a1a").pack(pady=5)
        self.username_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.username_var, bg="#333", fg="white").pack()
        tk.Label(frame, text="Password", fg="white", bg="#1a1a1a").pack(pady=5)
        self.password_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.password_var, show="*", bg="#333", fg="white").pack()
        ttk.Button(frame, text="Login", command=self.login).pack(pady=20)

    def login(self):
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
                self.current_user = data.get("username", username)
                self.current_role = data.get("role", "User")
                self.dashboard()
            else:
                messagebox.showerror("Login Failed", "Invalid credentials")
        except Exception as e:
            messagebox.showerror("Login Failed", str(e))

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

    # ---------- DASHBOARD ----------
    def dashboard(self):
        self.clear_root()

        header = tk.Label(
            self.root,
            text=f"ACEest Dashboard ({self.current_role})",
            font=("Arial", 24, "bold"),
            bg="#d4af37",
            fg="black",
            height=2,
        )
        header.pack(fill="x")

        left = tk.Frame(self.root, bg="#1a1a1a", width=350)
        left.pack(side="left", fill="y", padx=10, pady=10)

        tk.Label(left, text="Select Client", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.client_list = ttk.Combobox(left, state="readonly")
        self.client_list.pack()
        self.client_list.bind("<<ComboboxSelected>>", self.load_client)
        self.refresh_client_list()

        ttk.Button(left, text="Add / Save Client", command=self.add_save_client).pack(pady=5)
        ttk.Button(left, text="Generate AI Program", command=self.generate_program).pack(pady=5)
        ttk.Button(left, text="Generate PDF Report", command=self.generate_pdf).pack(pady=5)
        ttk.Button(left, text="Check Membership", command=self.check_membership).pack(pady=5)

        right = tk.Frame(self.root, bg="#1a1a1a")
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill="both", expand=True)

        self.tab_summary = tk.Frame(self.notebook, bg="#1a1a1a")
        self.notebook.add(self.tab_summary, text="Client Summary")
        self.summary_text = tk.Text(self.tab_summary, bg="#111", fg="white", font=("Consolas", 11))
        self.summary_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.chart_frame = tk.Frame(self.tab_summary, bg="#1a1a1a")
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_workouts = tk.Frame(self.notebook, bg="#1a1a1a")
        self.notebook.add(self.tab_workouts, text="Workouts & Exercises")
        self.setup_workout_tab()

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

    def add_save_client(self):
        name = simpledialog.askstring("Client Name", "Enter client name:", parent=self.root)
        if not name:
            return
        result = self._api_post("/api/clients", {"name": name, "membership_status": "Active"})
        if result is not None:
            self.refresh_client_list()
            messagebox.showinfo("Saved", f"Client {name} saved")
        else:
            messagebox.showerror("Error", "Could not save. Is Flask running?")

    def load_client(self, event=None):
        name = self.client_list.get()
        if not name:
            return
        self.current_client = name
        self.refresh_summary()
        self.refresh_workouts()
        self.plot_charts()

    # ---------- AI PROGRAM GENERATOR ----------
    def generate_program(self):
        if not self.current_client:
            messagebox.showwarning("No Client", "Select a client first")
            return
        program_type = random.choice(list(self.program_templates.keys()))
        program_detail = random.choice(self.program_templates[program_type])
        data = self._api_get(f"/api/clients/{quote(self.current_client)}")
        if data is None or data.get("error"):
            messagebox.showerror("Error", "Could not load client")
            return
        payload = {**data, "program": program_detail}
        payload.pop("id", None)
        result = self._api_post("/api/clients", payload)
        if result is not None:
            messagebox.showinfo("Program Generated", f"Program for {self.current_client}: {program_detail}")
            self.refresh_summary()
        else:
            messagebox.showerror("Error", "Could not update program")

    # ---------- PDF REPORT ----------
    def generate_pdf(self):
        if not self.current_client:
            messagebox.showwarning("No Client", "Select a client first")
            return
        if not HAS_FPDF:
            messagebox.showerror("Error", "Install fpdf2: pip install fpdf2")
            return
        data = self._api_get(f"/api/clients/{quote(self.current_client)}")
        if not data or data.get("error"):
            messagebox.showerror("Error", "Could not load client")
            return
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"ACEest Client Report - {self.current_client}", ln=True)
        pdf.set_font("Arial", "", 12)
        for key in ["name", "age", "height", "weight", "program", "calories", "target_weight", "target_adherence", "membership_status", "membership_end"]:
            val = data.get(key, "")
            pdf.cell(0, 10, f"{key.replace('_', ' ').title()}: {val}", ln=True)
        filename = f"{self.current_client}_report.pdf"
        pdf.output(filename)
        messagebox.showinfo("PDF Generated", f"{filename} created")

    # ---------- MEMBERSHIP ----------
    def check_membership(self):
        if not self.current_client:
            messagebox.showwarning("No Client", "Select a client first")
            return
        data = self._api_get(f"/api/clients/{quote(self.current_client)}")
        if not data or data.get("error"):
            messagebox.showerror("Error", "Client not found")
            return
        status = data.get("membership_status") or "N/A"
        end = data.get("membership_end") or data.get("membership_expiry") or "N/A"
        messagebox.showinfo("Membership", f"Membership: {status}\nRenewal Date: {end}")

    # ---------- SUMMARY & CHARTS ----------
    def refresh_summary(self):
        if not self.current_client:
            return
        data = self._api_get(f"/api/clients/{quote(self.current_client)}")
        if not data or data.get("error"):
            return
        text = (
            f"Name: {data.get('name', '')}\n"
            f"Program: {data.get('program', '')}\n"
            f"Calories: {data.get('calories', '')}\n"
            f"Membership: {data.get('membership_status', '') or data.get('membership_expiry', '')}"
        )
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("end", text)
        self.summary_text.configure(state="disabled")

    def plot_charts(self):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        if not self.current_client:
            return
        data = self._api_get(f"/api/progress/{quote(self.current_client)}")
        if not data:
            return
        if not HAS_MATPLOTLIB:
            return
        weeks = [d["week"] for d in data]
        adherence = [d["adherence"] for d in data]
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(weeks, adherence, marker="o")
        ax.set_title("Weekly Adherence")
        ax.set_ylabel("%")
        ax.set_ylim(0, 100)
        ax.grid(True)
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ---------- WORKOUT TAB ----------
    def setup_workout_tab(self):
        columns = ("date", "type", "duration", "notes")
        self.tree_workouts = ttk.Treeview(self.tab_workouts, columns=columns, show="headings")
        for c in columns:
            self.tree_workouts.heading(c, text=c.title())
            self.tree_workouts.column(c, width=150)
        self.tree_workouts.pack(fill="both", expand=True)
        ttk.Button(self.tab_workouts, text="Add Workout", command=self.add_workout).pack(pady=5)

    def refresh_workouts(self):
        for row in self.tree_workouts.get_children():
            self.tree_workouts.delete(row)
        if not self.current_client:
            return
        data = self._api_get(f"/api/workouts/{quote(self.current_client)}")
        if data:
            for row in data:
                self.tree_workouts.insert("", "end", values=(
                    row.get("date", ""),
                    row.get("workout_type", ""),
                    row.get("duration_min", ""),
                    row.get("notes", ""),
                ))

    def add_workout(self):
        if not self.current_client:
            messagebox.showwarning("No Client", "Select a client first")
            return
        win = tk.Toplevel(self.root)
        win.title(f"Add Workout - {self.current_client}")
        win.geometry("400x400")
        win.configure(bg="#1a1a1a")
        tk.Label(win, text="Date (YYYY-MM-DD)", bg="#1a1a1a", fg="white").pack()
        date_var = tk.StringVar(value=date.today().isoformat())
        tk.Entry(win, textvariable=date_var, bg="#333", fg="white").pack()
        tk.Label(win, text="Type", bg="#1a1a1a", fg="white").pack()
        type_var = tk.StringVar()
        ttk.Combobox(win, textvariable=type_var, values=["Strength", "Hypertrophy", "Cardio", "Mobility"], state="readonly").pack()
        tk.Label(win, text="Duration (min)", bg="#1a1a1a", fg="white").pack()
        dur_var = tk.IntVar(value=60)
        tk.Entry(win, textvariable=dur_var, bg="#333", fg="white").pack()
        tk.Label(win, text="Notes", bg="#1a1a1a", fg="white").pack()
        notes_var = tk.StringVar()
        tk.Entry(win, textvariable=notes_var, bg="#333", fg="white").pack()

        def save():
            result = self._api_post("/api/workouts", {
                "client_name": self.current_client,
                "date": date_var.get(),
                "workout_type": type_var.get(),
                "duration_min": dur_var.get(),
                "notes": notes_var.get(),
            })
            if result is not None:
                self.refresh_workouts()
                win.destroy()
            else:
                messagebox.showerror("Error", "Could not save workout")

        ttk.Button(win, text="Save", command=save).pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = ACEestApp(root)
    root.mainloop()
