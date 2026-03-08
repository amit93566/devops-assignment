"""
ACEest Fitness & Performance - Tkinter frontend (Aceestver-2.2.4).
Client Management, Progress & Analytics, Workouts, Metrics via Flask API.
Start Flask first (python app.py).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from urllib.parse import quote

try:
    import requests
except ImportError:
    requests = None

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

API_BASE = "http://localhost:5000"


class ACEestApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ACEest Fitness & Performance")
        self.root.geometry("1300x850")
        self.root.configure(bg="#1a1a1a")

        self.current_client = None

        self.setup_data()
        self.setup_ui()
        self.refresh_client_list()

    # ---------- DATA (program factors + desc from API) ----------
    def setup_data(self):
        """Load program list, factors and desc from Flask API."""
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
                    self.programs[name] = {
                        "factor": data.get("calorie_factor", 0),
                        "desc": data.get("desc", ""),
                    }
        except Exception:
            pass

    # ---------- UI ----------
    def setup_ui(self):
        # Header
        header = tk.Label(
            self.root,
            text="ACEest Functional Fitness System",
            bg="#d4af37",
            fg="black",
            font=("Helvetica", 24, "bold"),
            height=2,
        )
        header.pack(fill="x")

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bg="#111111",
            fg="#d4af37",
            anchor="w",
        )
        status_bar.pack(side="bottom", fill="x")

        # Main area
        main = tk.Frame(self.root, bg="#1a1a1a")
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # LEFT PANEL (client management)
        left = tk.LabelFrame(
            main,
            text=" Client Management ",
            bg="#1a1a1a",
            fg="#d4af37",
            font=("Arial", 12, "bold"),
        )
        left.pack(side="left", fill="y", padx=10, pady=5)

        # Client selection
        tk.Label(left, text="Select Client", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.client_list = ttk.Combobox(left, state="readonly")
        self.client_list.pack(pady=(0, 5))
        self.client_list.bind("<<ComboboxSelected>>", self.on_client_selected)

        tk.Label(left, text="Name", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.name = tk.StringVar()
        tk.Entry(left, textvariable=self.name, bg="#333", fg="white").pack()

        tk.Label(left, text="Age", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.age = tk.IntVar(value=0)
        tk.Entry(left, textvariable=self.age, bg="#333", fg="white").pack()

        tk.Label(left, text="Height (cm)", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.height = tk.DoubleVar(value=0.0)
        tk.Entry(left, textvariable=self.height, bg="#333", fg="white").pack()

        tk.Label(left, text="Weight (kg)", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.weight = tk.DoubleVar(value=0.0)
        tk.Entry(left, textvariable=self.weight, bg="#333", fg="white").pack()

        tk.Label(left, text="Program", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.program = tk.StringVar()
        ttk.Combobox(
            left,
            textvariable=self.program,
            values=list(self.programs.keys()),
            state="readonly",
        ).pack()

        tk.Label(left, text="Target Weight (kg)", bg="#1a1a1a", fg="white").pack(pady=(10, 0))
        self.target_weight = tk.DoubleVar(value=0.0)
        tk.Entry(left, textvariable=self.target_weight, bg="#333", fg="white").pack()

        tk.Label(left, text="Target Adherence %", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.target_adherence = tk.IntVar(value=0)
        tk.Entry(left, textvariable=self.target_adherence, bg="#333", fg="white").pack()

        tk.Label(left, text="Weekly Adherence %", bg="#1a1a1a", fg="white").pack(pady=(10, 0))
        self.adherence = tk.IntVar(value=0)
        ttk.Scale(
            left,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.adherence,
        ).pack(pady=(0, 5))

        ttk.Button(left, text="Save Client", command=self.save_client).pack(pady=5)
        ttk.Button(left, text="Load Client", command=self.load_client).pack(pady=5)
        ttk.Button(left, text="Save Weekly Progress", command=self.save_progress).pack(pady=5)
        ttk.Button(left, text="Log Workout", command=self.open_log_workout_window).pack(pady=5)
        ttk.Button(left, text="Log Body Metrics", command=self.open_log_metrics_window).pack(pady=5)
        ttk.Button(left, text="View Workout History", command=self.open_workout_history_window).pack(pady=5)

        # RIGHT PANEL with Notebook
        right = tk.Frame(main, bg="#1a1a1a")
        right.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        notebook = ttk.Notebook(right)
        notebook.pack(fill="both", expand=True)

        # Summary tab
        summary_frame = tk.Frame(notebook, bg="#1a1a1a")
        notebook.add(summary_frame, text="Client Summary")

        self.summary = tk.Text(summary_frame, bg="#111", fg="white", font=("Consolas", 11))
        self.summary.pack(fill="both", expand=True, padx=10, pady=10)

        # Analytics tab
        analytics_frame = tk.Frame(notebook, bg="#1a1a1a")
        notebook.add(analytics_frame, text="Progress & Analytics")

        ttk.Button(
            analytics_frame,
            text="Adherence Chart",
            command=self.show_progress_chart,
        ).pack(pady=10)

        ttk.Button(
            analytics_frame,
            text="Weight Trend Chart",
            command=self.show_weight_chart,
        ).pack(pady=10)

        ttk.Button(
            analytics_frame,
            text="BMI & Risk Info",
            command=self.show_bmi_info,
        ).pack(pady=10)

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

    def set_status(self, text: str):
        self.status_var.set(text)

    def ensure_client(self) -> bool:
        name = self.current_client or self.name.get().strip() or self.client_list.get()
        if not name:
            messagebox.showwarning("No Client", "Select or enter client first")
            return False
        self.current_client = name
        return True

    # ---------- CLIENT LIST / STATUS ----------
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
        name = self.client_list.get()
        if not name:
            return
        self.name.set(name)
        self.current_client = name
        self.load_client()

    # ---------- CORE LOGIC ----------
    def save_client(self):
        if not self.name.get():
            messagebox.showerror("Error", "Name is required")
            return
        if not self.program.get():
            messagebox.showerror("Error", "Program is required")
            return
        if self.program.get() not in self.programs:
            messagebox.showerror("Error", "Program not loaded. Is Flask running?")
            return

        name = self.name.get().strip()
        age = self.age.get() if self.age.get() > 0 else None
        height = self.height.get() if self.height.get() > 0 else None
        weight = self.weight.get() if self.weight.get() > 0 else None
        factor = self.programs[self.program.get()]["factor"]
        calories = int(weight * factor) if weight else None
        target_weight = self.target_weight.get() if self.target_weight.get() > 0 else None
        target_adherence = self.target_adherence.get() if self.target_adherence.get() > 0 else None

        payload = {
            "name": name,
            "age": age,
            "height": height,
            "weight": weight,
            "program": self.program.get(),
            "calories": calories,
            "target_weight": target_weight,
            "target_adherence": target_adherence,
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
        name = self.name.get().strip() or self.client_list.get()
        if not name:
            messagebox.showwarning("No Client", "Enter or select client name first")
            return

        data = self._api_get(f"/api/clients/{quote(name)}")
        if data is None or data.get("error"):
            messagebox.showwarning("Not Found", "Client not found")
            return

        self.current_client = name
        self.name.set(data.get("name", ""))
        self.age.set(data.get("age") if data.get("age") is not None else 0)
        self.height.set(data.get("height") if data.get("height") is not None else 0.0)
        self.weight.set(data.get("weight") if data.get("weight") is not None else 0.0)
        self.program.set(data.get("program") or "")
        self.target_weight.set(data.get("target_weight") if data.get("target_weight") is not None else 0.0)
        self.target_adherence.set(data.get("target_adherence") if data.get("target_adherence") is not None else 0)

        self.client_list.set(name)
        self.refresh_summary()
        self.set_status(f"Loaded client: {name}")

    def refresh_summary(self):
        if not self.current_client:
            return
        name = self.current_client

        data = self._api_get(f"/api/clients/{quote(name)}")
        if not data or data.get("error"):
            return

        age = data.get("age")
        height = data.get("height")
        weight = data.get("weight")
        program = data.get("program", "")
        calories = data.get("calories")
        target_weight = data.get("target_weight")
        target_adherence = data.get("target_adherence")

        progress_list = self._api_get(f"/api/progress/{quote(name)}") or []
        total_weeks = len(progress_list)
        avg_adherence = 0
        if progress_list:
            avg_adherence = round(sum(p.get("adherence", 0) for p in progress_list) / len(progress_list), 1)

        metrics_list = self._api_get(f"/api/metrics/{quote(name)}") or []
        last_metric_str = "None"
        if metrics_list:
            m = metrics_list[-1]
            last_metric_str = (
                f"{m.get('date', '')} | {m.get('weight')} kg, Waist {m.get('waist')} cm, "
                f"Bodyfat {m.get('bodyfat')}%"
            )

        goal_summary = "None"
        if target_weight or target_adherence:
            goal_summary = ""
            if target_weight:
                goal_summary += f"Target Weight: {target_weight} kg; "
            if target_adherence:
                goal_summary += f"Target Adherence: {target_adherence}%"

        prog_desc = self.programs.get(program, {}).get("desc", "")

        lines = [
            "CLIENT PROFILE",
            "--------------",
            f"Name      : {name}",
            f"Age       : {age if age is not None else '-'}",
            f"Height    : {height if height is not None else '-'} cm",
            f"Weight    : {weight if weight is not None else '-'} kg",
            f"Program   : {program}",
            f"Calories  : {calories if calories is not None else '-'} kcal/day",
            "",
            "PROGRAM NOTES",
            "-------------",
            prog_desc,
            "",
            "GOALS",
            "-----",
            goal_summary,
            "",
            "PROGRESS SUMMARY",
            "----------------",
            f"Weeks logged       : {total_weeks}",
            f"Average adherence  : {avg_adherence}%",
            "",
            "LAST BODY METRICS",
            "-----------------",
            last_metric_str,
        ]
        self.summary.configure(state="normal")
        self.summary.delete("1.0", "end")
        self.summary.insert("end", "\n".join(lines))
        self.summary.configure(state="disabled")

    def save_progress(self):
        if not self.ensure_client():
            return
        week = datetime.now().strftime("Week %U - %Y")
        payload = {
            "client_name": self.current_client,
            "week": week,
            "adherence": self.adherence.get(),
        }
        result = self._api_post("/api/progress", payload)
        if result is not None:
            self.refresh_summary()
            self.set_status(f"Saved weekly progress for {self.current_client}")
            messagebox.showinfo("Progress Saved", "Weekly progress logged")
        else:
            messagebox.showerror("Error", "Could not save progress. Is Flask running?")

    # ---------- CHARTS / ANALYTICS ----------
    def show_progress_chart(self):
        if not self.ensure_client():
            return
        if not HAS_MATPLOTLIB:
            messagebox.showerror("Error", "Install matplotlib to view the chart")
            return
        data = self._api_get(f"/api/progress/{quote(self.current_client)}")
        if data is None:
            messagebox.showerror("Error", "Could not load progress. Is Flask running?")
            return
        if not data:
            messagebox.showinfo("No Data", "No progress data available for this client")
            return
        weeks = [d["week"] for d in data]
        adherence = [d["adherence"] for d in data]
        plt.figure(figsize=(8, 4))
        plt.plot(weeks, adherence, marker="o", linewidth=2)
        plt.title(f"Weekly Adherence – {self.current_client}")
        plt.xlabel("Week")
        plt.ylabel("Adherence (%)")
        plt.ylim(0, 100)
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def show_weight_chart(self):
        if not self.ensure_client():
            return
        if not HAS_MATPLOTLIB:
            messagebox.showerror("Error", "Install matplotlib to view the chart")
            return
        data = self._api_get(f"/api/metrics/{quote(self.current_client)}")
        if data is None:
            messagebox.showerror("Error", "Could not load metrics. Is Flask running?")
            return
        data = [d for d in data if d.get("weight") is not None]
        if not data:
            messagebox.showinfo("No Data", "No weight metrics available for this client")
            return
        dates = [d["date"] for d in data]
        weights = [d["weight"] for d in data]
        plt.figure(figsize=(8, 4))
        plt.plot(dates, weights, marker="o", linewidth=2, color="orange")
        plt.title(f"Weight Trend – {self.current_client}")
        plt.xlabel("Date")
        plt.ylabel("Weight (kg)")
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def show_bmi_info(self):
        if not self.ensure_client():
            return
        height = self.height.get()
        weight = self.weight.get()
        if height <= 0 or weight <= 0:
            messagebox.showwarning("Missing Data", "Enter valid height and weight first")
            return
        h_m = height / 100.0
        bmi = round(weight / (h_m * h_m), 1)
        if bmi < 18.5:
            category = "Underweight"
            risk = "Potential nutrient deficiency, low energy."
        elif bmi < 25:
            category = "Normal"
            risk = "Low risk if active and strong."
        elif bmi < 30:
            category = "Overweight"
            risk = "Moderate risk; focus on adherence and progressive activity."
        else:
            category = "Obese"
            risk = "Higher risk; prioritize fat loss, consistency, and supervision."
        messagebox.showinfo(
            "BMI Info",
            f"BMI for {self.current_client}: {bmi} ({category})\n\nRisk note: {risk}",
        )

    # ---------- WORKOUT LOGGING ----------
    def open_log_workout_window(self):
        if not self.ensure_client():
            return

        win = tk.Toplevel(self.root)
        win.title(f"Log Workout – {self.current_client}")
        win.configure(bg="#1a1a1a")
        win.geometry("450x500")

        tk.Label(win, text="Date (YYYY-MM-DD)", bg="#1a1a1a", fg="white").pack(pady=(10, 0))
        date_var = tk.StringVar(value=date.today().isoformat())
        tk.Entry(win, textvariable=date_var, bg="#333", fg="white").pack()

        tk.Label(win, text="Workout Type", bg="#1a1a1a", fg="white").pack(pady=(10, 0))
        type_var = tk.StringVar()
        ttk.Combobox(
            win,
            textvariable=type_var,
            values=["Strength", "Hypertrophy", "Conditioning", "Mixed", "Mobility"],
            state="readonly",
        ).pack()

        tk.Label(win, text="Duration (min)", bg="#1a1a1a", fg="white").pack(pady=(10, 0))
        dur_var = tk.IntVar(value=60)
        tk.Entry(win, textvariable=dur_var, bg="#333", fg="white").pack()

        tk.Label(win, text="Notes", bg="#1a1a1a", fg="white").pack(pady=(10, 0))
        notes_text = tk.Text(win, height=4, bg="#333", fg="white")
        notes_text.pack(fill="x", padx=10)

        tk.Label(win, text="Exercise Name", bg="#1a1a1a", fg="white").pack(pady=(10, 0))
        ex_name_var = tk.StringVar()
        tk.Entry(win, textvariable=ex_name_var, bg="#333", fg="white").pack()

        tk.Label(win, text="Sets", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        sets_var = tk.IntVar(value=3)
        tk.Entry(win, textvariable=sets_var, bg="#333", fg="white").pack()

        tk.Label(win, text="Reps", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        reps_var = tk.IntVar(value=10)
        tk.Entry(win, textvariable=reps_var, bg="#333", fg="white").pack()

        tk.Label(win, text="Weight (kg)", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        ex_weight_var = tk.DoubleVar(value=0.0)
        tk.Entry(win, textvariable=ex_weight_var, bg="#333", fg="white").pack()

        def save_workout():
            w_date = date_var.get().strip()
            w_type = type_var.get().strip()
            try:
                duration = int(dur_var.get())
            except (ValueError, tk.TclError):
                duration = 60
            notes = notes_text.get("1.0", "end").strip()
            if not w_date or not w_type:
                messagebox.showerror("Error", "Date and workout type are required")
                return
            payload = {
                "client_name": self.current_client,
                "date": w_date,
                "workout_type": w_type,
                "duration_min": duration,
                "notes": notes,
            }
            ex_name = ex_name_var.get().strip()
            if ex_name:
                payload["exercises"] = [
                    {
                        "name": ex_name,
                        "sets": sets_var.get(),
                        "reps": reps_var.get(),
                        "weight": ex_weight_var.get(),
                    }
                ]
            result = self._api_post("/api/workouts", payload)
            if result is not None:
                self.set_status(f"Workout logged for {self.current_client}")
                messagebox.showinfo("Saved", "Workout logged successfully")
                win.destroy()
            else:
                messagebox.showerror("Error", "Could not save workout. Is Flask running?")

        ttk.Button(win, text="Save Workout", command=save_workout).pack(pady=15)

    def open_log_metrics_window(self):
        if not self.ensure_client():
            return

        win = tk.Toplevel(self.root)
        win.title(f"Log Body Metrics – {self.current_client}")
        win.configure(bg="#1a1a1a")
        win.geometry("350x300")

        tk.Label(win, text="Date (YYYY-MM-DD)", bg="#1a1a1a", fg="white").pack(pady=(10, 0))
        date_var = tk.StringVar(value=date.today().isoformat())
        tk.Entry(win, textvariable=date_var, bg="#333", fg="white").pack()

        tk.Label(win, text="Weight (kg)", bg="#1a1a1a", fg="white").pack(pady=(10, 0))
        weight_val = self.weight.get() if self.weight.get() > 0 else 0.0
        weight_var = tk.DoubleVar(value=weight_val)
        tk.Entry(win, textvariable=weight_var, bg="#333", fg="white").pack()

        tk.Label(win, text="Waist (cm)", bg="#1a1a1a", fg="white").pack(pady=(10, 0))
        waist_var = tk.DoubleVar(value=0.0)
        tk.Entry(win, textvariable=waist_var, bg="#333", fg="white").pack()

        tk.Label(win, text="Bodyfat (%)", bg="#1a1a1a", fg="white").pack(pady=(10, 0))
        bf_var = tk.DoubleVar(value=0.0)
        tk.Entry(win, textvariable=bf_var, bg="#333", fg="white").pack()

        def save_metrics():
            m_date = date_var.get().strip()
            if not m_date:
                messagebox.showerror("Error", "Date is required")
                return
            payload = {
                "client_name": self.current_client,
                "date": m_date,
                "weight": weight_var.get(),
                "waist": waist_var.get(),
                "bodyfat": bf_var.get(),
            }
            result = self._api_post("/api/metrics", payload)
            if result is not None:
                if weight_var.get() > 0:
                    self.weight.set(weight_var.get())
                self.refresh_summary()
                self.set_status(f"Metrics logged for {self.current_client}")
                messagebox.showinfo("Saved", "Metrics logged successfully")
                win.destroy()
            else:
                messagebox.showerror("Error", "Could not save metrics. Is Flask running?")

        ttk.Button(win, text="Save Metrics", command=save_metrics).pack(pady=15)

    def open_workout_history_window(self):
        if not self.ensure_client():
            return

        win = tk.Toplevel(self.root)
        win.title(f"Workout History – {self.current_client}")
        win.geometry("700x400")

        columns = ("date", "type", "duration", "notes")
        tree = ttk.Treeview(win, columns=columns, show="headings")
        tree.heading("date", text="Date")
        tree.heading("type", text="Type")
        tree.heading("duration", text="Duration (min)")
        tree.heading("notes", text="Notes")

        tree.column("date", width=100, anchor="center")
        tree.column("type", width=100, anchor="center")
        tree.column("duration", width=120, anchor="center")
        tree.column("notes", width=350, anchor="w")

        tree.pack(fill="both", expand=True)

        data = self._api_get(f"/api/workouts/{quote(self.current_client)}")
        if data:
            for row in data:
                tree.insert("", "end", values=(
                    row.get("date", ""),
                    row.get("workout_type", ""),
                    row.get("duration_min", ""),
                    row.get("notes", ""),
                ))

        self.set_status(f"Loaded workout history for {self.current_client}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ACEestApp(root)
    root.mainloop()
