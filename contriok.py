import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime
from fpdf import FPDF
import os

class ContributionManagement:
    def __init__(self, parent, bg_color, fg_color):
        self.parent = parent
        self.bg_color = bg_color
        self.fg_color = fg_color

        self.title_font = ('Arial', 18, 'bold')
        self.label_font = ('Arial', 12)
        self.entry_font = ('Arial', 12)
        self.button_font = ('Arial', 12, 'bold')

        self.setup_db()
        self.create_ui()
        self.refresh_table()
        self.refresh_credits_table()

    def setup_db(self):
        self.conn = sqlite3.connect('contributiondb.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS contributions (
                contribution_id TEXT PRIMARY KEY,
                member_name TEXT NOT NULL,
                contribution_type TEXT NOT NULL,
                amount TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                receipt_proof TEXT,
                status TEXT NOT NULL
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS credits (
                credit_id TEXT PRIMARY KEY,
                member_name TEXT NOT NULL,
                credit_amount TEXT NOT NULL,
                credit_date TEXT NOT NULL,
                credit_reason TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def create_ui(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Main container frame
        self.main_container = tk.Frame(self.parent, bg=self.bg_color)
        self.main_container.pack(fill='both', expand=True)

        # Left side - Contribution Management with scrollbar
        self.left_frame = tk.Frame(self.main_container, bg=self.bg_color)
        self.left_frame.pack(side='left', fill='both', expand=True)

        self.left_canvas = tk.Canvas(self.left_frame, bg=self.bg_color, highlightthickness=0)
        self.left_scrollbar = ttk.Scrollbar(self.left_frame, orient="vertical", command=self.left_canvas.yview)
        self.left_scrollable_frame = tk.Frame(self.left_canvas, bg=self.bg_color)

        self.left_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.left_canvas.configure(
                scrollregion=self.left_canvas.bbox("all")
            )
        )

        self.left_canvas.create_window((0, 0), window=self.left_scrollable_frame, anchor="nw")
        self.left_canvas.configure(yscrollcommand=self.left_scrollbar.set)
        self.left_canvas.pack(side="left", fill="both", expand=True)
        self.left_scrollbar.pack(side="right", fill="y")

        tk.Label(self.left_scrollable_frame, text="Contribution Management", 
                font=self.title_font, bg=self.bg_color, fg=self.fg_color).grid(row=0, column=0, columnspan=4, pady=20, sticky='w')

        # Contribution form
        form_frame = tk.LabelFrame(self.left_scrollable_frame, text="Add/Edit Contribution", 
                                  font=self.label_font, bg=self.bg_color, fg=self.fg_color)
        form_frame.grid(row=1, column=0, padx=20, pady=10, sticky='nsew')

        fields = [
            ('Member ID/Name*', 'member_name', 'text', 30),
            ('Contribution Type*', 'contribution_type', 'option', ['Monthly Savings', 'Donation', 'Fine', 'Adhoc']),
            ('Amount (₹)*', 'amount', 'text', 20),
            ('Payment Method*', 'payment_method', 'option', ['Cash', 'UPI', 'Bank Transfer', 'Mobile Money']),
            ('Transaction Date*', 'transaction_date', 'date'),
            ('Receipt/Proof*', 'receipt_proof', 'file'),
            ('Status*', 'status', 'option', ['Pending', 'Verified', 'Rejected']),
            ('Contribution ID', 'contribution_id', 'text', 30, True)
        ]

        self.entries = {}
        for i, field_data in enumerate(fields):
            label, field, field_type = field_data[0], field_data[1], field_data[2]
            tk.Label(form_frame, text=label, font=self.label_font, bg=self.bg_color).grid(
                row=i, column=0, sticky='e', padx=5, pady=5)

            if field_type == 'text':
                width = field_data[3]
                disabled = field_data[4] if len(field_data) > 4 else False
                entry = tk.Entry(form_frame, width=width, font=self.entry_font)
                if disabled:
                    entry.config(state='disabled')
                entry.grid(row=i, column=1, sticky='w', padx=5, pady=5, ipady=3)
                self.entries[field] = entry

            elif field_type == 'option':
                options = field_data[3]
                var = tk.StringVar()
                option = ttk.Combobox(form_frame, textvariable=var, values=options, width=25, font=self.entry_font)
                option.grid(row=i, column=1, sticky='w', padx=5, pady=5, ipady=3)
                self.entries[field] = var

            elif field_type == 'date':
                date_entry = DateEntry(form_frame, width=20, font=self.entry_font, 
                                     background='darkblue', foreground='white', borderwidth=2)
                date_entry.grid(row=i, column=1, sticky='w', padx=5, pady=5)
                self.entries[field] = date_entry

            elif field_type == 'file':
                file_var = tk.StringVar()
                file_entry = tk.Entry(form_frame, textvariable=file_var, width=30, font=self.entry_font)
                file_entry.grid(row=i, column=1, sticky='w', padx=5, pady=5, ipady=3)
                browse_btn = tk.Button(form_frame, text="Browse", 
                                      command=lambda var=file_var: self.browse_file(var), 
                                      font=self.entry_font)
                browse_btn.grid(row=i, column=2, sticky='w', padx=5)
                self.entries[field] = file_var

        button_frame = tk.Frame(form_frame, bg=self.bg_color)
        button_frame.grid(row=len(fields), column=0, columnspan=3, pady=15)

        btn_cfg = {'font': self.button_font, 'width': 15, 'padx': 10, 'pady': 8, 'bd': 0, 'highlightthickness': 0}
        tk.Button(button_frame, text="Add Contribution", command=self.add_contribution, 
                 bg=self.fg_color, fg='white', **btn_cfg).pack(side='left', padx=10)
        tk.Button(button_frame, text="Update", command=self.update_contribution, 
                 bg=self.fg_color, fg='white', **btn_cfg).pack(side='left', padx=10)
        tk.Button(button_frame, text="Delete", command=self.delete_contribution, 
                 bg=self.fg_color, fg='white', **btn_cfg).pack(side='left', padx=10)
        tk.Button(button_frame, text="Generate PDF", command=self.generate_pdf, 
                 bg=self.fg_color, fg='white', **btn_cfg).pack(side='left', padx=10)

        # Contributions table
        self.tree = ttk.Treeview(self.left_scrollable_frame, 
                               columns=["ID", "Name", "Type", "Amount", "Payment", "Date", "Status"], 
                               show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.grid(row=2, column=0, padx=20, pady=10, sticky='nsew')
        self.tree.bind("<Double-1>", self.on_tree_select)

        # Right side - Credits Management with scrollbar
        self.right_frame = tk.Frame(self.main_container, bg=self.bg_color, width=350)
        self.right_frame.pack(side='right', fill='y', padx=10, pady=10)

        self.right_canvas = tk.Canvas(self.right_frame, bg=self.bg_color, highlightthickness=0)
        self.right_scrollbar = ttk.Scrollbar(self.right_frame, orient="vertical", command=self.right_canvas.yview)
        self.right_scrollable_frame = tk.Frame(self.right_canvas, bg=self.bg_color)

        self.right_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.right_canvas.configure(
                scrollregion=self.right_canvas.bbox("all")
            )
        )

        self.right_canvas.create_window((0, 0), window=self.right_scrollable_frame, anchor="nw")
        self.right_canvas.configure(yscrollcommand=self.right_scrollbar.set)
        self.right_canvas.pack(side="left", fill="both", expand=True)
        self.right_scrollbar.pack(side="right", fill="y")

        tk.Label(self.right_scrollable_frame, text="Credits Management", 
                font=self.title_font, bg=self.bg_color, fg=self.fg_color).pack(pady=10, anchor='w')

        # Credits form
        credits_form = tk.LabelFrame(self.right_scrollable_frame, text="Add/Edit Credit", 
                                   font=self.label_font, bg=self.bg_color, fg=self.fg_color)
        credits_form.pack(fill='x', padx=5, pady=5)

        tk.Label(credits_form, text="Member Name:", bg=self.bg_color).grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.credit_member_name = tk.Entry(credits_form, width=25)
        self.credit_member_name.grid(row=0, column=1, sticky='w', padx=5, pady=5)

        tk.Label(credits_form, text="Amount (₹):", bg=self.bg_color).grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.credit_amount = tk.Entry(credits_form, width=25)
        self.credit_amount.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        tk.Label(credits_form, text="Date:", bg=self.bg_color).grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.credit_date = DateEntry(credits_form, width=20, background='darkblue', foreground='white', borderwidth=2)
        self.credit_date.grid(row=2, column=1, sticky='w', padx=5, pady=5)

        tk.Label(credits_form, text="Reason:", bg=self.bg_color).grid(row=3, column=0, sticky='e', padx=5, pady=5)
        self.credit_reason = ttk.Combobox(credits_form, values=["Refund", "Adjustment", "Other"], width=22)
        self.credit_reason.grid(row=3, column=1, sticky='w', padx=5, pady=5)

        # Credit buttons frame
        credit_buttons = tk.Frame(credits_form, bg=self.bg_color)
        credit_buttons.grid(row=4, column=0, columnspan=2, pady=10)
        
        btn_cfg = {'font': self.button_font, 'width': 10, 'padx': 5, 'pady': 5, 'bd': 0, 'highlightthickness': 0}
        tk.Button(credit_buttons, text="Add", command=self.add_credit, 
                 bg=self.fg_color, fg='white', **btn_cfg).pack(side='left', padx=5)
        tk.Button(credit_buttons, text="Update", command=self.update_credit, 
                 bg=self.fg_color, fg='white', **btn_cfg).pack(side='left', padx=5)
        tk.Button(credit_buttons, text="Delete", command=self.delete_credit, 
                 bg=self.fg_color, fg='white', **btn_cfg).pack(side='left', padx=5)
        tk.Button(credit_buttons, text="Clear", command=self.clear_credit_form, 
                 bg=self.fg_color, fg='white', **btn_cfg).pack(side='left', padx=5)

        # Credits table
        credits_table_frame = tk.LabelFrame(self.right_scrollable_frame, text="Credits", 
                                          font=self.label_font, bg=self.bg_color, fg=self.fg_color)
        credits_table_frame.pack(fill='x', padx=5, pady=5)

        self.credits_tree = ttk.Treeview(credits_table_frame, 
                                       columns=["ID", "Name", "Amount", "Date", "Reason"], 
                                       show="headings", height=5)
        for col in self.credits_tree["columns"]:
            self.credits_tree.heading(col, text=col)
            self.credits_tree.column(col, width=80)
        self.credits_tree.pack(fill='x', padx=5, pady=5)
        self.credits_tree.bind("<Double-1>", self.on_credit_tree_select)

        # Member credits calculation
        member_credits_frame = tk.LabelFrame(self.right_scrollable_frame, text="Member Credits", 
                                           font=self.label_font, bg=self.bg_color, fg=self.fg_color)
        member_credits_frame.pack(fill='x', padx=5, pady=5)

        tk.Label(member_credits_frame, text="Member Name:", bg=self.bg_color).pack(pady=5)
        self.member_credit_name = tk.Entry(member_credits_frame, width=25)
        self.member_credit_name.pack(pady=5)

        self.member_credit_total = tk.Label(member_credits_frame, text="Total: ₹0", 
                                          font=('Arial', 12, 'bold'), bg=self.bg_color)
        self.member_credit_total.pack(pady=5)

        tk.Button(member_credits_frame, text="Calculate", command=self.calculate_member_credits, 
                 bg=self.fg_color, fg='white', font=self.button_font).pack(pady=5)

        # Net total section
        total_frame = tk.LabelFrame(self.right_scrollable_frame, text="Net Total (Contributions - Credits)", 
                                   font=self.label_font, bg=self.bg_color, fg=self.fg_color)
        total_frame.pack(fill='x', padx=5, pady=10)

        self.total_label = tk.Label(total_frame, text="Net Total: ₹0", 
                                  font=('Arial', 14, 'bold'), bg=self.bg_color)
        self.total_label.pack(pady=10)

        tk.Button(total_frame, text="Calculate Net Total", command=self.calculate_net_total, 
                 bg=self.fg_color, fg='white', font=self.button_font).pack(pady=5)

    def browse_file(self, var):
        filepath = filedialog.askopenfilename()
        if filepath:
            var.set(filepath)

    def get_form_data(self, include_id=True):
        data = {}
        for field, entry in self.entries.items():
            if not include_id and field == 'contribution_id':
                continue
            if isinstance(entry, tk.Entry):
                data[field] = entry.get()
            elif isinstance(entry, tk.StringVar):
                data[field] = entry.get()
            elif isinstance(entry, DateEntry):
                data[field] = entry.get()
        return data

    def add_contribution(self):
        try:
            contribution_id = f"CNT{int(datetime.now().timestamp())}"
            self.entries['contribution_id'].config(state='normal')
            self.entries['contribution_id'].delete(0, tk.END)
            self.entries['contribution_id'].insert(0, contribution_id)
            self.entries['contribution_id'].config(state='disabled')

            data = self.get_form_data()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            values = tuple(data.values())

            self.cursor.execute(f"INSERT INTO contributions ({columns}) VALUES ({placeholders})", values)
            self.conn.commit()
            self.refresh_table()
            messagebox.showinfo("Success", "Contribution added successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.cursor.execute("SELECT contribution_id, member_name, contribution_type, amount, payment_method, transaction_date, status FROM contributions")
        for row in self.cursor.fetchall():
            self.tree.insert('', 'end', values=row)

    def refresh_credits_table(self):
        for row in self.credits_tree.get_children():
            self.credits_tree.delete(row)
        self.cursor.execute("SELECT credit_id, member_name, credit_amount, credit_date, credit_reason FROM credits")
        for row in self.cursor.fetchall():
            self.credits_tree.insert('', 'end', values=row)

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0])['values']
            self.cursor.execute("SELECT * FROM contributions WHERE contribution_id = ?", (values[0],))
            record = self.cursor.fetchone()
            if record:
                fields = ['contribution_id', 'member_name', 'contribution_type', 'amount', 'payment_method', 'transaction_date', 'receipt_proof', 'status']
                for i, field in enumerate(fields):
                    if field in self.entries:
                        entry = self.entries[field]
                        if isinstance(entry, tk.Entry):
                            entry.config(state='normal')
                            entry.delete(0, tk.END)
                            entry.insert(0, record[i])
                            if field == 'contribution_id':
                                entry.config(state='disabled')
                        elif isinstance(entry, tk.StringVar):
                            entry.set(record[i])
                        elif isinstance(entry, DateEntry):
                            entry.set_date(record[i])

    def update_contribution(self):
        try:
            data = self.get_form_data()
            contribution_id = data.pop('contribution_id')
            values = list(data.values()) + [contribution_id]
            query = f"UPDATE contributions SET {', '.join([f'{k}=?' for k in data])} WHERE contribution_id = ?"
            self.cursor.execute(query, values)
            self.conn.commit()
            self.refresh_table()
            messagebox.showinfo("Success", "Contribution updated successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_contribution(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Record", "Please select a record to delete")
            return
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this record?")
        if confirm:
            contribution_id = self.tree.item(selected[0])['values'][0]
            self.cursor.execute("DELETE FROM contributions WHERE contribution_id = ?", (contribution_id,))
            self.conn.commit()
            self.refresh_table()
            messagebox.showinfo("Deleted", "Contribution deleted successfully")

    def generate_pdf(self):
        data = self.get_form_data()
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="Contribution Receipt", ln=True, align='C')
        pdf.ln(10)

        for key, value in data.items():
            pdf.cell(200, 10, txt=f"{key.replace('_', ' ').title()}: {value}", ln=True)

        filename = f"receipt_{data.get('contribution_id', 'unknown')}.pdf"
        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")], initialfile=filename)
        if save_path:
            pdf.output(save_path)
            messagebox.showinfo("Success", f"PDF generated and saved as {os.path.basename(save_path)}")

    def on_credit_tree_select(self, event):
        selected = self.credits_tree.selection()
        if selected:
            values = self.credits_tree.item(selected[0])['values']
            if values:
                self.credit_member_name.delete(0, tk.END)
                self.credit_member_name.insert(0, values[1])
                self.credit_amount.delete(0, tk.END)
                self.credit_amount.insert(0, values[2])
                self.credit_date.set_date(values[3])
                self.credit_reason.set(values[4])

    def clear_credit_form(self):
        self.credit_member_name.delete(0, tk.END)
        self.credit_amount.delete(0, tk.END)
        self.credit_reason.set('')

    def add_credit(self):
        try:
            member_name = self.credit_member_name.get()
            amount = self.credit_amount.get()
            date = self.credit_date.get()
            reason = self.credit_reason.get()

            if not all([member_name, amount, date, reason]):
                messagebox.showwarning("Input Error", "All fields are required")
                return

            credit_id = f"CRD{int(datetime.now().timestamp())}"
            self.cursor.execute("INSERT INTO credits VALUES (?, ?, ?, ?, ?)",
                               (credit_id, member_name, amount, date, reason))
            self.conn.commit()
            self.refresh_credits_table()
            self.clear_credit_form()
            messagebox.showinfo("Success", "Credit added successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_credit(self):
        selected = self.credits_tree.selection()
        if not selected:
            messagebox.showwarning("Select Record", "Please select a credit to update")
            return

        try:
            credit_id = self.credits_tree.item(selected[0])['values'][0]
            member_name = self.credit_member_name.get()
            amount = self.credit_amount.get()
            date = self.credit_date.get()
            reason = self.credit_reason.get()

            if not all([member_name, amount, date, reason]):
                messagebox.showwarning("Input Error", "All fields are required")
                return

            self.cursor.execute("""
                UPDATE credits 
                SET member_name=?, credit_amount=?, credit_date=?, credit_reason=?
                WHERE credit_id=?
            """, (member_name, amount, date, reason, credit_id))
            self.conn.commit()
            self.refresh_credits_table()
            self.clear_credit_form()
            messagebox.showinfo("Success", "Credit updated successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_credit(self):
        selected = self.credits_tree.selection()
        if not selected:
            messagebox.showwarning("Select Record", "Please select a credit to delete")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this credit?")
        if confirm:
            credit_id = self.credits_tree.item(selected[0])['values'][0]
            self.cursor.execute("DELETE FROM credits WHERE credit_id=?", (credit_id,))
            self.conn.commit()
            self.refresh_credits_table()
            self.clear_credit_form()
            messagebox.showinfo("Deleted", "Credit deleted successfully")

    def calculate_member_credits(self):
        member_name = self.member_credit_name.get()
        if not member_name:
            messagebox.showwarning("Input Error", "Please enter a member name")
            return

        try:
            self.cursor.execute("""
                SELECT SUM(CAST(credit_amount AS REAL)) 
                FROM credits 
                WHERE member_name=?
            """, (member_name,))
            total = self.cursor.fetchone()[0] or 0
            self.member_credit_total.config(text=f"Total: ₹{total:,.2f}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate credits: {str(e)}")

    def calculate_net_total(self):
        try:
            # Calculate total verified contributions
            self.cursor.execute("SELECT SUM(CAST(amount AS REAL)) FROM contributions WHERE status='Verified'")
            total_contributions = self.cursor.fetchone()[0] or 0
            
            # Calculate total credits
            self.cursor.execute("SELECT SUM(CAST(credit_amount AS REAL)) FROM credits")
            total_credits = self.cursor.fetchone()[0] or 0
            
            # Calculate net total (contributions - credits)
            net_total = total_contributions - total_credits
            
            self.total_label.config(text=f"Net Total: ₹{net_total:,.2f}\n"
                                      f"(Contributions: ₹{total_contributions:,.2f}\n"
                                      f"Credits: ₹{total_credits:,.2f})")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate net total: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1400x700")
    root.title("Contribution Management System")
    app = ContributionManagement(root, "#F6DED8", "#D2665A")
    root.mainloop()