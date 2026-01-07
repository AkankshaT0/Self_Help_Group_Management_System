import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
from fpdf import FPDF
import os

class LoanManagement:
    def __init__(self, parent_frame, bg_color, fg_color):
        self.parent = parent_frame
        self.bg_color = bg_color
        self.fg_color = fg_color

        self.title_font = ('Arial', 18, 'bold')
        self.label_font = ('Arial', 12)
        self.entry_font = ('Arial', 12)
        self.button_font = ('Arial', 12, 'bold')

        self.setup_db()
        self.create_ui()

    def setup_db(self):
        self.conn = sqlite3.connect('memberloandb.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS loans (
                loan_id TEXT PRIMARY KEY,
                applicant_name TEXT NOT NULL,
                group_name TEXT NOT NULL,
                loan_amount REAL NOT NULL,
                purpose TEXT NOT NULL,
                duration_months INTEGER NOT NULL,
                application_date TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def create_ui(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

        self.canvas = tk.Canvas(self.parent, bg=self.bg_color, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.bg_color)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind_all("<MouseWheel>", lambda event: self.canvas.yview_scroll(int(-1*(event.delta/120)), "units"))

        tk.Label(self.scrollable_frame, text="Loan Management System", font=self.title_font, bg=self.bg_color, fg=self.fg_color).grid(row=0, column=0, columnspan=4, pady=20, sticky='w')

        search_frame = tk.Frame(self.scrollable_frame, bg=self.bg_color)
        search_frame.grid(row=1, column=0, padx=20, pady=10, sticky='w')

        tk.Label(search_frame, text="Enter Loan ID:", font=self.label_font, bg=self.bg_color, fg=self.fg_color).pack(side='left', padx=(0, 10))
        self.search_entry = tk.Entry(search_frame, font=self.entry_font, width=30)
        self.search_entry.pack(side='left')
        tk.Button(search_frame, text="Search", command=self.search_loan, font=self.button_font, bg=self.fg_color, fg='white').pack(side='left', padx=10)

        form_frame = tk.LabelFrame(self.scrollable_frame, text="Loan Details", font=self.label_font, bg=self.bg_color, fg=self.fg_color)
        form_frame.grid(row=2, column=0, padx=20, pady=10, sticky='nsew')

        fields = [
            ('Applicant Name*', 'applicant_name', 'text', 30),
            ('Group Name*', 'group_name', 'text', 30),
            ('Loan Amount (₹)*', 'loan_amount', 'number', 15),
            ('Purpose*', 'purpose', 'text', 30),
            ('Duration (Months)*', 'duration_months', 'number', 10),
            ('Application Date', 'application_date', 'text', 15, True),
            ('Loan ID', 'loan_id', 'text', 20, True)
        ]

        self.entries = {}
        for i, field_data in enumerate(fields):
            label, field, field_type = field_data[0], field_data[1], field_data[2]
            width = field_data[3] if len(field_data) > 3 else 20
            disabled = field_data[4] if len(field_data) > 4 else False

            row = i
            tk.Label(form_frame, text=label, font=self.label_font, bg=self.bg_color).grid(row=row, column=0, sticky='e', padx=5, pady=5)
            entry = tk.Entry(form_frame, width=width, font=self.entry_font)
            if disabled:
                entry.config(state='disabled')
            entry.grid(row=row, column=1, sticky='w', padx=5, pady=5, ipady=3)
            self.entries[field] = entry

        button_frame = tk.Frame(form_frame, bg=self.bg_color)
        button_frame.grid(row=8, column=0, columnspan=2, pady=15)

        button_config = {'font': self.button_font, 'width': 12, 'padx': 10, 'pady': 8, 'bd': 0, 'highlightthickness': 0}
        tk.Button(button_frame, text="Add Loan", command=self.add_loan, bg=self.fg_color, fg='white', **button_config).pack(side='left', padx=10)
        tk.Button(button_frame, text="Update", command=self.update_loan, bg=self.fg_color, fg='white', **button_config).pack(side='left', padx=10)
        tk.Button(button_frame, text="Clear", command=self.clear_form, bg=self.fg_color, fg='white', **button_config).pack(side='left', padx=10)
        tk.Button(button_frame, text="Delete", command=self.delete_loan, bg='red', fg='white', **button_config).pack(side='left', padx=10)
        tk.Button(button_frame, text="Generate PDF", command=self.generate_pdf, bg='green', fg='white', **button_config).pack(side='left', padx=10)

        table_frame = tk.LabelFrame(self.scrollable_frame, text="Searched Loan Data", font=self.label_font, bg=self.bg_color, fg=self.fg_color)
        table_frame.grid(row=3, column=0, padx=20, pady=20, sticky='nsew')

        style = ttk.Style()
        style.configure("Treeview", font=('Arial', 11), rowheight=30)
        style.configure("Treeview.Heading", font=('Arial', 12, 'bold'))

        self.tree = ttk.Treeview(table_frame, columns=('ID', 'Applicant', 'Group', 'Amount', 'Purpose', 'Duration'), selectmode='browse', height=1)
        self.tree.grid(row=0, column=0, sticky='nsew')
        ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview).grid(row=0, column=1, sticky='ns')
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree.heading('#0', text='#')
        self.tree.column('#0', width=50, anchor='center')
        self.tree.heading('ID', text='Loan ID')
        self.tree.column('ID', width=150, anchor='w')
        self.tree.heading('Applicant', text='Applicant Name')
        self.tree.column('Applicant', width=200, anchor='w')
        self.tree.heading('Group', text='Group Name')
        self.tree.column('Group', width=150, anchor='w')
        self.tree.heading('Amount', text='Amount (₹)')
        self.tree.column('Amount', width=120, anchor='e')
        self.tree.heading('Purpose', text='Purpose')
        self.tree.column('Purpose', width=200, anchor='w')
        self.tree.heading('Duration', text='Duration')
        self.tree.column('Duration', width=100, anchor='center')

        self.tree.bind('<<TreeviewSelect>>', self.on_loan_select)

    def add_loan(self):
        try:
            now = datetime.now().strftime("%Y-%m-%d")
            loan_id = f"LN{int(datetime.now().timestamp())}"
            self.entries['loan_id'].config(state='normal')
            self.entries['loan_id'].delete(0, tk.END)
            self.entries['loan_id'].insert(0, loan_id)
            self.entries['loan_id'].config(state='disabled')

            self.entries['application_date'].config(state='normal')
            self.entries['application_date'].delete(0, tk.END)
            self.entries['application_date'].insert(0, now)
            self.entries['application_date'].config(state='disabled')

            data = {field: entry.get() for field, entry in self.entries.items()}
            required_fields = ['applicant_name', 'group_name', 'loan_amount', 'purpose', 'duration_months']
            for field in required_fields:
                if not data.get(field):
                    messagebox.showerror("Error", f"Please fill in all required fields ({field})")
                    return

            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            values = tuple(data.values())

            self.cursor.execute(f"INSERT INTO loans ({columns}) VALUES ({placeholders})", values)
            self.conn.commit()
            messagebox.showinfo("Success", "Loan application added successfully")
            self.clear_form()
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Integrity error: {e}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_loan(self):
        try:
            loan_id = self.entries['loan_id'].get()
            if not loan_id:
                messagebox.showwarning("Warning", "Please select a loan to update")
                return

            data = {field: entry.get() for field, entry in self.entries.items() if field not in ['loan_id', 'application_date']}
            required_fields = ['applicant_name', 'group_name', 'loan_amount', 'purpose', 'duration_months']
            for field in required_fields:
                if not data.get(field):
                    messagebox.showerror("Error", f"Please fill in all required fields ({field})")
                    return

            updates = ', '.join([f"{key}=?" for key in data])
            values = tuple(data.values()) + (loan_id,)

            self.cursor.execute(f"UPDATE loans SET {updates} WHERE loan_id=?", values)
            self.conn.commit()
            messagebox.showinfo("Success", "Loan application updated successfully")
            self.search_loan()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_loan(self):
        loan_id = self.entries['loan_id'].get()
        if not loan_id:
            messagebox.showwarning("Warning", "Please select a loan to delete")
            return
        self.cursor.execute("DELETE FROM loans WHERE loan_id=?", (loan_id,))
        self.conn.commit()
        messagebox.showinfo("Success", "Loan application deleted successfully")
        self.clear_form()
        self.tree.delete(*self.tree.get_children())

    def clear_form(self):
        for field, entry in self.entries.items():
            state = entry['state']
            entry.config(state='normal')
            entry.delete(0, tk.END)
            if state == 'disabled':
                entry.config(state='disabled')

    def search_loan(self):
        loan_id = self.search_entry.get().strip()
        if not loan_id:
            messagebox.showerror("Error", "Please enter a Loan ID")
            return

        self.cursor.execute("SELECT * FROM loans WHERE loan_id=?", (loan_id,))
        loan = self.cursor.fetchone()
        if not loan:
            messagebox.showinfo("Not Found", f"No loan found with ID {loan_id}")
            self.tree.delete(*self.tree.get_children())
            self.clear_form()
            return

        for field, value in zip([description[0] for description in self.cursor.description], loan):
            if field in self.entries:
                self.entries[field].config(state='normal')
                self.entries[field].delete(0, tk.END)
                self.entries[field].insert(0, value)
                if field in ['loan_id', 'application_date']:
                    self.entries[field].config(state='disabled')

        self.tree.delete(*self.tree.get_children())
        formatted_row = list(loan)
        formatted_row[3] = f"₹{float(formatted_row[3]):,.2f}"
        formatted_row[5] = f"{formatted_row[5]} months"
        self.tree.insert('', 'end', text="1", values=(loan[0], loan[1], loan[2], formatted_row[3], loan[4], formatted_row[5]))

    def on_loan_select(self, event):
        pass  # No action required, form is already filled during search

    def generate_pdf(self):
        loan_id = self.entries['loan_id'].get()
        if not loan_id:
            messagebox.showwarning("Warning", "Please search a loan before generating PDF")
            return

        self.cursor.execute("SELECT * FROM loans WHERE loan_id=?", (loan_id,))
        loan_data = self.cursor.fetchone()
        if not loan_data:
            messagebox.showerror("Error", "Loan not found")
            return

        columns = [desc[0] for desc in self.cursor.description]
        loan_dict = dict(zip(columns, loan_data))

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Loan_Application_{loan_id}.pdf"
        )

        if not file_path:
            return

        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "Loan Application Details", 0, 1, 'C')
            pdf.ln(10)
            pdf.set_font("Arial", '', 12)

            details = [
                ("Loan ID", loan_dict['loan_id']),
                ("Applicant Name", loan_dict['applicant_name']),
                ("Group Name", loan_dict['group_name']),
                ("Loan Amount", f"₹{float(loan_dict['loan_amount']):,.2f}"),
                ("Purpose", loan_dict['purpose']),
                ("Duration", f"{loan_dict['duration_months']} months"),
                ("Application Date", loan_dict['application_date'])
            ]

            for label, value in details:
                pdf.cell(50, 10, label + ":", 0, 0)
                pdf.cell(0, 10, value, 0, 1)

            pdf.output(file_path)
            messagebox.showinfo("Success", f"PDF generated successfully:\n{file_path}")
            if messagebox.askyesno("Open PDF", "Would you like to open the generated PDF?"):
                os.startfile(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x700")
    root.title("Loan Management System")
    app = LoanManagement(root, "#F6DED8", "#D2665A")
    root.mainloop()
