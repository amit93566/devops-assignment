"""
ACEest Fitness & Performance - Tkinter frontend 
Client Management via Flask API (clients and progress stored in backend SQLite).
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

        self.setup_ui()
        self.fetch_programs()

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

        # LEFT PANEL – CLIENT MANAGEMENT
        left = tk.LabelFrame(
            main,
            text=" Client Management ",
            bg="#1a1a1a",
            fg="#d4af37",
            font=("Arial", 12, "bold"),
        )
        left.pack(side="left", fill="y", padx=10)

        self.name_var = tk.StringVar()
        self.age_var = tk.IntVar(value=0)
        self.weight_var = tk.DoubleVar(value=0.0)
        self.program_var = tk.StringVar()
        self.adherence_var = tk.IntVar(value=0)

        self._field(left, "Name", self.name_var)
        self._field(left, "Age", self.age_var)
        self._field(left, "Weight (kg)", self.weight_var)

        tk.Label(left, text="Program", bg="#1a1a1a", fg="white").pack(pady=5)
        self.program_box = ttk.Combobox(
            left,
            textvariable=self.program_var,
            values=[],
            state="readonly",
        )
        self.program_box.pack()

        tk.Label(left, text="Weekly Adherence %", bg="#1a1a1a", fg="white").pack(pady=10)
        ttk.Scale(
            left,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.adherence_var,
        ).pack()

        ttk.Button(left, text="Save Client", command=self.save_client).pack(pady=10)
        ttk.Button(left, text="Load Client", command=self.load_client).pack(pady=5)
        ttk.Button(left, text="Save Progress", command=self.save_progress).pack(pady=5)

        # RIGHT PANEL – CLIENT SUMMARY
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

    def fetch_programs(self):
        if not requests:
            messagebox.showwarning("Warning", "Install requests to load programs from API")
            return
        data = self._api_get("/api/programs")
        if data is not None:
            self.program_box["values"] = data
        else:
            messagebox.showwarning(
                "Backend not reachable",
                f"Cannot reach Flask API at {API_BASE}. Start with: python app.py",
            )

    def _get_factor(self):
        """Get calorie factor for current program from API."""
        program = self.program_var.get()
        if not program:
            return None
        data = self._api_get(f"/api/program/{quote(program)}")
        return data.get("calorie_factor") if data else None

    def save_client(self):
        if not self.name_var.get() or not self.program_var.get():
            messagebox.showerror("Error", "Name and Program required")
            return
        factor = self._get_factor()
        if factor is None:
            messagebox.showerror("Error", "Could not get program factor. Is Flask running?")
            return
        calories = int(self.weight_var.get() * factor)
        payload = {
            "name": self.name_var.get(),
            "age": self.age_var.get(),
            "weight": self.weight_var.get(),
            "program": self.program_var.get(),
            "calories": calories,
        }
        result = self._api_post("/api/clients", payload)
        if result is not None:
            messagebox.showinfo("Saved", "Client data saved")
        else:
            messagebox.showerror("Error", "Could not save client. Is Flask running?")

    def load_client(self):
        name = self.name_var.get()
        if not name:
            messagebox.showwarning("Warning", "Enter client name")
            return
        data = self._api_get(f"/api/clients/{quote(name)}")
        if data is None or "error" in data:
            messagebox.showwarning("Not Found", "Client not found")
            return
        self.age_var.set(data.get("age", 0))
        self.weight_var.set(data.get("weight", 0))
        self.program_var.set(data.get("program", ""))
        self.summary.delete("1.0", "end")
        self.summary.insert(
            "end",
            f"""
CLIENT PROFILE
--------------
Name     : {data.get('name', '')}
Age      : {data.get('age', 0)}
Weight   : {data.get('weight', 0)} kg
Program  : {data.get('program', '')}
Calories : {data.get('calories', 0)} kcal/day
""",
        )

    def save_progress(self):
        if not self.name_var.get():
            messagebox.showwarning("Warning", "Enter client name first")
            return
        week = datetime.now().strftime("Week %U - %Y")
        payload = {
            "client_name": self.name_var.get(),
            "week": week,
            "adherence": self.adherence_var.get(),
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
