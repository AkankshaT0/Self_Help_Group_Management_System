import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

class LoanManagementSystem:
    def __init__(self, master, bg_color, fg_color):
        self.master = master
       # self.master.title("Loan Application")
       # self.master.geometry("1000x600")
       # self.master.configure(bg=bg_color)
        self.bg_color = bg_color
        self.fg_color = fg_color

        frame = tk.Frame(master, bg=bg_color)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Loan Applications",
                 font=("Arial", 16, "bold"), bg=bg_color, fg=fg_color).pack(pady=20)

        # DB connection
        self.conn = sqlite3.connect("memberloandb.db")
        self.cursor = self.conn.cursor()
        self.create_loan_table()

        # Fonts
        self.label_font = ("Arial", 12)
        self.entry_font = ("Arial", 12)

        self.entries = {}
        self.member_names = []

        # UI
        self.create_ui()
        self.create_table_view()
        self.load_loans()

    def create_loan_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_name TEXT NOT NULL,
                group_name TEXT NOT NULL,
                loan_amount REAL NOT NULL,
                loan_reason TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def fetch_members(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='members'")
        if not self.cursor.fetchone():
            return []
        try:
            self.cursor.execute("SELECT member_name, group_name FROM members")
            return self.cursor.fetchall()
        except sqlite3.OperationalError:
            messagebox.showerror("Error", "The 'members' table does not contain the required fields.")
            return []

    def on_member_select(self, event):
        selected_name = self.entries['applicant_name'].get()
        for name, group in self.member_names:
            if name == selected_name:
                self.entries['group_name'].config(state='normal')
                self.entries['group_name'].delete(0, tk.END)
                self.entries['group_name'].insert(0, group)
                self.entries['group_name'].config(state='readonly')
                break

    def create_ui(self):
        form_frame = tk.LabelFrame(self.master, text="Loan Application Form", padx=10, pady=10, font=self.label_font)
        form_frame.pack(padx=20, pady=20, fill="x")

        self.member_names = self.fetch_members()
        if not self.member_names:
            return

        # Applicant Name
        tk.Label(form_frame, text="Applicant Name:", font=self.label_font).grid(row=0, column=0, sticky='e', padx=5, pady=5)
        applicant_combo = ttk.Combobox(form_frame, values=[name for name, _ in self.member_names], width=30, font=self.entry_font, state='readonly')
        applicant_combo.grid(row=0, column=1, sticky='w', padx=5, pady=5, ipady=3)
        applicant_combo.bind("<<ComboboxSelected>>", self.on_member_select)
        self.entries['applicant_name'] = applicant_combo

        # Group Name
        tk.Label(form_frame, text="Group Name:", font=self.label_font).grid(row=1, column=0, sticky='e', padx=5, pady=5)
        group_entry = tk.Entry(form_frame, width=30, font=self.entry_font, state='readonly')
        group_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5, ipady=3)
        self.entries['group_name'] = group_entry

        # Loan Amount
        tk.Label(form_frame, text="Loan Amount:", font=self.label_font).grid(row=2, column=0, sticky='e', padx=5, pady=5)
        amount_entry = tk.Entry(form_frame, width=30, font=self.entry_font)
        amount_entry.grid(row=2, column=1, sticky='w', padx=5, pady=5, ipady=3)
        self.entries['loan_amount'] = amount_entry

        # Loan Reason
        tk.Label(form_frame, text="Loan Reason:", font=self.label_font).grid(row=3, column=0, sticky='e', padx=5, pady=5)
        reason_entry = tk.Entry(form_frame, width=30, font=self.entry_font)
        reason_entry.grid(row=3, column=1, sticky='w', padx=5, pady=5, ipady=3)
        self.entries['loan_reason'] = reason_entry

        # Submit Button
        submit_btn = tk.Button(form_frame, text="Submit Loan", font=self.label_font, command=self.save_loan)
        submit_btn.grid(row=4, column=0, columnspan=2, pady=10)

        # Refresh Button
        refresh_btn = tk.Button(form_frame, text="Refresh Members", font=self.label_font, command=self.refresh_members)
        refresh_btn.grid(row=5, column=0, columnspan=2, pady=5)

    def create_table_view(self):
        table_frame = tk.Frame(self.master)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("id", "applicant_name", "group_name", "loan_amount", "loan_reason")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=150)
        self.tree.pack(fill="both", expand=True)

    def load_loans(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        self.cursor.execute("SELECT * FROM loans")
        for row in self.cursor.fetchall():
            self.tree.insert("", "end", values=row)

    def refresh_members(self):
        self.member_names = self.fetch_members()
        if not self.member_names:
            return

        self.entries['applicant_name']['values'] = [name for name, _ in self.member_names]
        self.entries['group_name'].config(state='normal')
        self.entries['group_name'].delete(0, tk.END)
        self.entries['group_name'].config(state='readonly')

    def save_loan(self):
        applicant = self.entries['applicant_name'].get()
        group = self.entries['group_name'].get()
        amount = self.entries['loan_amount'].get()
        reason = self.entries['loan_reason'].get()

        if not applicant or not group or not amount or not reason:
            messagebox.showerror("Error", "Please fill all fields.")
            return

        try:
            amount = float(amount)
        except ValueError:
            messagebox.showerror("Invalid Input", "Loan amount must be a number.")
            return

        self.cursor.execute(
            "INSERT INTO loans (applicant_name, group_name, loan_amount, loan_reason) VALUES (?, ?, ?, ?)",
            (applicant, group, amount, reason)
        )
        self.conn.commit()
        messagebox.showinfo("Success", "Loan application saved.")
        self.load_loans()
        for key in ['loan_amount', 'loan_reason']:
            self.entries[key].delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    bg_color = "#F6DED8"   # light blue background
    fg_color = "#D2665A"   # black text
    app = LoanManagementSystem(root, bg_color, fg_color)
    root.mainloop()
