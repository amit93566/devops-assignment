"""
ACEest Fitness & Performance - Tkinter frontend (Aceestver-1.1).
Desktop GUI: client profile, program selection, workout/diet, estimated calories.
Fetches program data from the Flask backend. Start Flask first (python app.py).
"""

import tkinter as tk
from tkinter import ttk, messagebox
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
        self.root.geometry("1150x780")
        self.root.configure(bg="#1a1a1a")

        self.setup_styles()
        self.setup_ui()
        self.fetch_programs()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TCombobox", fieldbackground="#333", background="#333", foreground="white")
        style.configure("TButton", background="#d4af37", foreground="black", font=("Arial", 10, "bold"))

    def setup_ui(self):
        header = tk.Frame(self.root, bg="#d4af37", height=80)
        header.pack(fill="x")
        tk.Label(
            header,
            text="ACEest FUNCTIONAL FITNESS SYSTEM",
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

        ttk.Button(left, text="Save Client", command=self.save_client).pack(pady=15)
        ttk.Button(left, text="Reset", command=self.reset).pack()

        # RIGHT PANEL – PROGRAM DETAILS
        right = tk.Frame(main, bg="#1a1a1a")
        right.pack(side="right", fill="both", expand=True)

        self.workout_text = self._scrollable_block(right, " Weekly Training Plan ")
        self.diet_text = self._scrollable_block(right, " Nutrition Plan (TN Context) ")

        self.calorie_label = tk.Label(
            right,
            text="Estimated Calories: --",
            bg="#1a1a1a",
            fg="#d4af37",
            font=("Arial", 12, "bold"),
        )
        self.calorie_label.pack(pady=10)

    def _input(self, parent, label, variable):
        tk.Label(parent, text=label, bg="#1a1a1a", fg="white").pack(pady=5)
        tk.Entry(parent, textvariable=variable, bg="#333", fg="white").pack(padx=20)

    def _scrollable_block(self, parent, title):
        frame = tk.LabelFrame(
            parent,
            text=title,
            bg="#1a1a1a",
            fg="#d4af37",
            font=("Arial", 12),
        )
        frame.pack(fill="both", expand=True, pady=5)
        text = tk.Text(frame, bg="#111", fg="white", wrap="word", height=10)
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.config(state="disabled")
        return text

    def fetch_programs(self):
        if not requests:
            messagebox.showerror("Error", "Install requests: pip install requests")
            return
        try:
            r = requests.get(f"{API_BASE}/api/programs", timeout=5)
            r.raise_for_status()
            self.program_box["values"] = r.json()
        except Exception as e:
            messagebox.showwarning(
                "Backend not reachable",
                f"Cannot reach Flask API at {API_BASE}. Start the server with: python app.py\n\nError: {e}",
            )

    def update_program(self, event=None):
        program = self.program_var.get()
        if not program or not requests:
            return
        try:
            url = f"{API_BASE}/api/program/{quote(program)}"
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            self._update_text(self.workout_text, f"Error: {e}", "#e74c3c")
            self._update_text(self.diet_text, "", "white")
            self.calorie_label.config(text="Estimated Calories: --")
            return
        self._update_text(self.workout_text, data.get("workout", ""), data.get("color", "#fff"))
        self._update_text(self.diet_text, data.get("diet", ""), "white")
        weight = self.weight_var.get()
        factor = data.get("calorie_factor")
        if weight > 0 and factor is not None:
            calories = int(weight * factor)
            self.calorie_label.config(text=f"Estimated Calories: {calories} kcal")
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
        messagebox.showinfo(
            "Saved",
            f"Client {self.name_var.get()} saved successfully.\n"
            f"Adherence: {self.progress_var.get()}%",
        )

    def reset(self):
        self.name_var.set("")
        self.age_var.set(0)
        self.weight_var.set(0.0)
        self.program_var.set("")
        self.progress_var.set(0)
        self._update_text(self.workout_text, "", "white")
        self._update_text(self.diet_text, "", "white")
        self.calorie_label.config(text="Estimated Calories: --")


if __name__ == "__main__":
    root = tk.Tk()
    ACEestApp(root)
    root.mainloop()
