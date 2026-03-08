"""
ACEest Fitness & Performance - Tkinter frontend (Aceestver-1.1.2).
Desktop GUI: client profile, program details, client list table, progress chart, CSV export.
Fetches programs and clients from the Flask backend. Start Flask first (python app.py).
"""

import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from urllib.parse import quote

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

API_BASE = "http://localhost:5000"


class ACEestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ACEest Fitness & Performance")
        self.root.geometry("1250x820")
        self.root.configure(bg="#1a1a1a")

        self.clients = []
        self.setup_ui()
        self.fetch_programs()
        self.fetch_clients()

    def setup_ui(self):
        header = tk.Frame(self.root, bg="#d4af37", height=80)
        header.pack(fill="x")
        tk.Label(
            header,
            text="ACEest FUNCTIONAL FITNESS SYSTEM v2",
            font=("Helvetica", 24, "bold"),
            bg="#d4af37",
            fg="black",
        ).pack(pady=20)

        main = tk.Frame(self.root, bg="#1a1a1a")
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # LEFT PANEL – CLIENT PROFILE
        left = tk.LabelFrame(
            main,
            text=" Client Profile ",
            bg="#1a1a1a",
            fg="#d4af37",
            font=("Arial", 12, "bold"),
        )
        left.pack(side="left", fill="y", padx=10)

        self.name_var = tk.StringVar()
        self.age_var = tk.IntVar(value=0)
        self.weight_var = tk.DoubleVar(value=0.0)
        self.program_var = tk.StringVar()
        self.progress_var = tk.IntVar(value=0)
        self.notes_var = tk.StringVar()

        self._input(left, "Name", self.name_var)
        self._input(left, "Age", self.age_var)
        self._input(left, "Weight (kg)", self.weight_var)

        tk.Label(left, text="Program", bg="#1a1a1a", fg="white").pack(pady=5)
        self.program_box = ttk.Combobox(
            left,
            textvariable=self.program_var,
            values=[],
            state="readonly",
        )
        self.program_box.pack(padx=20)
        self.program_box.bind("<<ComboboxSelected>>", self.update_program)

        tk.Label(left, text="Weekly Adherence (%)", bg="#1a1a1a", fg="white").pack(pady=10)
        ttk.Scale(left, from_=0, to=100, variable=self.progress_var, orient="horizontal").pack(padx=20)

        tk.Label(left, text="Coach Notes", bg="#1a1a1a", fg="white").pack(pady=5)
        tk.Entry(left, textvariable=self.notes_var, bg="#333", fg="white").pack(padx=20)

        ttk.Button(left, text="Save Client", command=self.save_client).pack(pady=15)
        ttk.Button(left, text="Export CSV", command=self.export_csv).pack(pady=5)
        ttk.Button(left, text="Reset", command=self.reset).pack()

        # RIGHT PANEL – PROGRAM DETAILS
        right = tk.Frame(main, bg="#1a1a1a")
        right.pack(side="right", fill="both", expand=True)

        self.workout_text = self._scrollable_block(right, " Weekly Training Plan ")
        self.diet_text = self._scrollable_block(right, " Nutrition Plan ")

        self.calorie_label = tk.Label(
            right,
            text="Estimated Calories: --",
            bg="#1a1a1a",
            fg="#d4af37",
            font=("Arial", 12, "bold"),
        )
        self.calorie_label.pack(pady=10)

        # CLIENT LIST TABLE
        table_frame = tk.LabelFrame(right, text=" Client List ", bg="#1a1a1a", fg="#d4af37")
        table_frame.pack(fill="both", expand=True, pady=10)
        self.client_table = ttk.Treeview(
            table_frame,
            columns=("Name", "Age", "Weight", "Program", "Adherence", "Notes"),
            show="headings",
            height=6,
        )
        for col in self.client_table["columns"]:
            self.client_table.heading(col, text=col)
        self.client_table.pack(fill="both", expand=True)

        # PROGRESS CHART
        chart_frame = tk.LabelFrame(right, text=" Progress Chart ", bg="#1a1a1a", fg="#d4af37")
        chart_frame.pack(fill="both", expand=True, pady=10)
        if HAS_MATPLOTLIB:
            self.fig, self.ax = plt.subplots(figsize=(4, 2))
            self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
            self.canvas.get_tk_widget().pack()
        else:
            self.fig = self.ax = self.canvas = None
            tk.Label(chart_frame, text="Install matplotlib for progress chart", bg="#1a1a1a", fg="#888").pack()

    def _input(self, parent, label, variable):
        tk.Label(parent, text=label, bg="#1a1a1a", fg="white").pack(pady=5)
        tk.Entry(parent, textvariable=variable, bg="#333", fg="white").pack(padx=20)

    def _scrollable_block(self, parent, title):
        frame = tk.LabelFrame(parent, text=title, bg="#1a1a1a", fg="#d4af37", font=("Arial", 12))
        frame.pack(fill="both", expand=True, pady=5)
        text = tk.Text(frame, bg="#111", fg="white", wrap="word", height=8)
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.config(state="disabled")
        return text

    def _api_get(self, path):
        if not requests:
            return None
        try:
            r = requests.get(f"{API_BASE}{path}", timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    def _api_post(self, path, data):
        if not requests:
            return None
        try:
            r = requests.post(f"{API_BASE}{path}", json=data, timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    def fetch_programs(self):
        if not requests:
            messagebox.showerror("Error", "Install requests: pip install requests")
            return
        data = self._api_get("/api/programs")
        if data is not None:
            self.program_box["values"] = data
        else:
            messagebox.showwarning(
                "Backend not reachable",
                f"Cannot reach Flask API at {API_BASE}. Start the server with: python app.py",
            )

    def fetch_clients(self):
        data = self._api_get("/api/clients")
        if data is not None:
            self.clients = data
            self._refresh_table()
            self.update_chart()

    def _refresh_table(self):
        for row in self.client_table.get_children():
            self.client_table.delete(row)
        for c in self.clients:
            self.client_table.insert(
                "",
                "end",
                values=(
                    c.get("name", ""),
                    c.get("age", 0),
                    c.get("weight", 0),
                    c.get("program", ""),
                    c.get("adherence", 0),
                    c.get("notes", ""),
                ),
            )

    def update_program(self, event=None):
        program = self.program_var.get()
        if not program or not requests:
            return
        data = self._api_get(f"/api/program/{quote(program)}")
        if data is None:
            return
        self._update_text(self.workout_text, data.get("workout", ""), data.get("color", "#fff"))
        self._update_text(self.diet_text, data.get("diet", ""), "white")
        weight = self.weight_var.get()
        factor = data.get("calorie_factor")
        if weight > 0 and factor is not None:
            self.calorie_label.config(text=f"Estimated Calories: {int(weight * factor)} kcal")
        else:
            self.calorie_label.config(text="Estimated Calories: --")

    def _update_text(self, widget, content, color="white"):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", content)
        widget.config(fg=color, state="disabled")

    def save_client(self):
        if not self.name_var.get() or not self.program_var.get():
            messagebox.showwarning("Incomplete", "Please fill client name and program.")
            return
        payload = {
            "name": self.name_var.get(),
            "age": self.age_var.get(),
            "weight": self.weight_var.get(),
            "program": self.program_var.get(),
            "adherence": self.progress_var.get(),
            "notes": self.notes_var.get(),
        }
        if self._api_post("/api/clients", payload) is not None:
            self.fetch_clients()
            messagebox.showinfo("Saved", f"Client {self.name_var.get()} saved successfully.")
        else:
            messagebox.showerror("Error", "Could not save client. Is the Flask server running?")

    def export_csv(self):
        if not self.clients:
            messagebox.showwarning("No Data", "No clients to export.")
            return
        file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file:
            with open(file, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["Name", "Age", "Weight", "Program", "Adherence", "Notes"])
                for c in self.clients:
                    w.writerow([
                        c.get("name", ""),
                        c.get("age", 0),
                        c.get("weight", 0),
                        c.get("program", ""),
                        c.get("adherence", 0),
                        c.get("notes", ""),
                    ])
            messagebox.showinfo("Exported", f"Client data exported to {file}")

    def update_chart(self):
        if not HAS_MATPLOTLIB or self.ax is None:
            return
        self.ax.clear()
        if not self.clients:
            self.ax.set_ylabel("Adherence %")
            self.ax.set_title("Client Progress")
        else:
            names = [c.get("name", "") for c in self.clients]
            adherence = [c.get("adherence", 0) for c in self.clients]
            self.ax.bar(names, adherence, color="#d4af37")
            self.ax.set_ylabel("Adherence %")
            self.ax.set_title("Client Progress")
        if self.canvas:
            self.canvas.draw()

    def reset(self):
        self.name_var.set("")
        self.age_var.set(0)
        self.weight_var.set(0.0)
        self.program_var.set("")
        self.progress_var.set(0)
        self.notes_var.set("")
        self._update_text(self.workout_text, "", "white")
        self._update_text(self.diet_text, "", "white")
        self.calorie_label.config(text="Estimated Calories: --")


if __name__ == "__main__":
    root = tk.Tk()
    ACEestApp(root)
    root.mainloop()
