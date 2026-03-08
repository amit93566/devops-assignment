"""
ACEest Fitness & Performance - Tkinter frontend.
Client Management via Flask API (clients and progress in backend SQLite).
Matches Aceestver-4 style: setup_data (program factors from API), Save/Load Client, Save Progress.
Start Flask first (python app.py).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from urllib.parse import quote

try:
    import requests
except ImportError:
    requests = None

API_BASE = "http://localhost:5000"


class ACEestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ACEest Fitness & Performance")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1a1a1a")

        self.setup_data()
        self.setup_ui()

    # ---------- DATA (program factors from API) ----------
    def setup_data(self):
        """Load program list and factors from Flask API."""
        self.programs = {}
        if not requests:
            return
        try:
            r = requests.get(f"{API_BASE}/api/programs", timeout=5)
            r.raise_for_status()
            names = r.json()
            for name in names:
                r2 = requests.get(f"{API_BASE}/api/program/{quote(name)}", timeout=5)
                if r2.status_code == 200:
                    data = r2.json()
                    self.programs[name] = {"factor": data.get("calorie_factor", 0)}
        except Exception:
            pass

    # ---------- UI ----------
    def setup_ui(self):
        header = tk.Label(
            self.root,
            text="ACEest Functional Fitness System",
            bg="#d4af37",
            fg="black",
            font=("Helvetica", 24, "bold"),
            height=2,
        )
        header.pack(fill="x")

        main = tk.Frame(self.root, bg="#1a1a1a")
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # LEFT PANEL
        left = tk.LabelFrame(
            main,
            text=" Client Management ",
            bg="#1a1a1a",
            fg="#d4af37",
            font=("Arial", 12, "bold"),
        )
        left.pack(side="left", fill="y", padx=10)

        self.name = tk.StringVar()
        self.age = tk.IntVar(value=0)
        self.weight = tk.DoubleVar(value=0.0)
        self.program = tk.StringVar()
        self.adherence = tk.IntVar(value=0)

        self._field(left, "Name", self.name)
        self._field(left, "Age", self.age)
        self._field(left, "Weight (kg)", self.weight)

        tk.Label(left, text="Program", bg="#1a1a1a", fg="white").pack(pady=5)
        ttk.Combobox(
            left,
            textvariable=self.program,
            values=list(self.programs.keys()),
            state="readonly",
        ).pack()

        tk.Label(left, text="Weekly Adherence %", bg="#1a1a1a", fg="white").pack(pady=10)
        ttk.Scale(left, from_=0, to=100, orient="horizontal", variable=self.adherence).pack()

        ttk.Button(left, text="Save Client", command=self.save_client).pack(pady=10)
        ttk.Button(left, text="Load Client", command=self.load_client).pack(pady=5)
        ttk.Button(left, text="Save Progress", command=self.save_progress).pack(pady=5)

        # RIGHT PANEL
        right = tk.LabelFrame(
            main,
            text=" Client Summary ",
            bg="#1a1a1a",
            fg="#d4af37",
            font=("Arial", 12),
        )
        right.pack(side="right", fill="both", expand=True)

        self.summary = tk.Text(right, bg="#111", fg="white", font=("Consolas", 11))
        self.summary.pack(fill="both", expand=True, padx=10, pady=10)

    # ---------- HELPERS ----------
    def _field(self, parent, label, var):
        tk.Label(parent, text=label, bg="#1a1a1a", fg="white").pack(pady=5)
        tk.Entry(parent, textvariable=var, bg="#333", fg="white").pack()

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

    # ---------- LOGIC ----------
    def save_client(self):
        if not self.name.get() or not self.program.get():
            messagebox.showerror("Error", "Name and Program required")
            return
        if self.program.get() not in self.programs:
            messagebox.showerror("Error", "Program not loaded. Is Flask running?")
            return
        calories = int(self.weight.get() * self.programs[self.program.get()]["factor"])
        payload = {
            "name": self.name.get(),
            "age": self.age.get(),
            "weight": self.weight.get(),
            "program": self.program.get(),
            "calories": calories,
        }
        result = self._api_post("/api/clients", payload)
        if result is not None:
            messagebox.showinfo("Saved", "Client data saved")
        else:
            messagebox.showerror("Error", "Could not save client. Is Flask running?")

    def load_client(self):
        if not self.name.get():
            messagebox.showwarning("Warning", "Enter client name")
            return
        data = self._api_get(f"/api/clients/{quote(self.name.get())}")
        if data is None or "error" in data:
            messagebox.showwarning("Not Found", "Client not found")
            return
        self.age.set(data.get("age", 0))
        self.weight.set(data.get("weight", 0))
        self.program.set(data.get("program", ""))
        self.summary.delete("1.0", "end")
        name = data.get("name", "")
        age = data.get("age", 0)
        weight = data.get("weight", 0)
        program = data.get("program", "")
        calories = data.get("calories", 0)
        self.summary.insert(
            "end",
            f"""
CLIENT PROFILE
--------------
Name     : {name}
Age      : {age}
Weight   : {weight} kg
Program  : {program}
Calories : {calories} kcal/day
""",
        )

    def save_progress(self):
        if not self.name.get():
            messagebox.showwarning("Warning", "Enter client name first")
            return
        week = datetime.now().strftime("Week %U - %Y")
        payload = {
            "client_name": self.name.get(),
            "week": week,
            "adherence": self.adherence.get(),
        }
        result = self._api_post("/api/progress", payload)
        if result is not None:
            messagebox.showinfo("Progress Saved", "Weekly progress logged")
        else:
            messagebox.showerror("Error", "Could not save progress. Is Flask running?")


if __name__ == "__main__":
    root = tk.Tk()
    ACEestApp(root)
    root.mainloop()
