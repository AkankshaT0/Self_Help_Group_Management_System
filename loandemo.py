import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime
from fpdf import FPDF
import os

class LoanManagement:
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

    def setup_db(self):
        # Set up loan database
        self.conn = sqlite3.connect('loandb.db')
        self.cursor = self.conn.cursor()
        
        # Check if loans table exists
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='loans'")
        table_exists = self.cursor.fetchone() is not None
        
        if not table_exists:
            # Create the table with all columns if it doesn't exist
            self.cursor.execute('''
                CREATE TABLE loans (
                    loan_id TEXT PRIMARY KEY,
                    applicant_name TEXT NOT NULL,
                    group_name TEXT NOT NULL,
                    loan_amount REAL NOT NULL,
                    purpose TEXT NOT NULL,
                    duration_months INTEGER NOT NULL,
                    interest_rate REAL NOT NULL,
                    status TEXT NOT NULL,
                    rejection_reason TEXT,
                    approved_date TEXT,
                    funds_allocated INTEGER DEFAULT 0
                )
            ''')
        else:
            # Check if approved_date column exists
            try:
                self.cursor.execute("SELECT approved_date FROM loans LIMIT 1")
            except sqlite3.OperationalError:
                # Add approved_date column if it doesn't exist
                self.cursor.execute("ALTER TABLE loans ADD COLUMN approved_date TEXT")
            
            # Check if funds_allocated column exists
            try:
                self.cursor.execute("SELECT funds_allocated FROM loans LIMIT 1")
            except sqlite3.OperationalError:
                # Add funds_allocated column if it doesn't exist
                self.cursor.execute("ALTER TABLE loans ADD COLUMN funds_allocated INTEGER DEFAULT 0")
        
        # Set up fund allocation tracking table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS fund_allocation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_available REAL,
                total_allocated REAL,
                last_updated TEXT
            )
        ''')
        
        # Initialize fund allocation if not exists
        self.cursor.execute("SELECT COUNT(*) FROM fund_allocation")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("INSERT INTO fund_allocation (total_available, total_allocated, last_updated) VALUES (0, 0, ?)", 
                               (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
        
        self.conn.commit()

    def create_ui(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Create main frame with scrollbar
        main_frame = tk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create canvas with scrollbar
        self.canvas = tk.Canvas(main_frame, bg=self.bg_color)
        self.scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        
        # Configure the canvas
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.bg_color)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Create a window inside the canvas with the scrollable frame
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configure canvas to fill available space and expand with the window
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Configure canvas to resize the scrollable frame when the canvas size changes
        self.canvas.bind('<Configure>', self.on_canvas_resize)
        
        # Bind mouse wheel to scrolling
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        self.parent.bind("<Down>", lambda event: self.canvas.yview_scroll(1, "units"))
        self.parent.bind("<Up>", lambda event: self.canvas.yview_scroll(-1, "units"))

        tk.Label(self.scrollable_frame, text="Loan Management System", font=self.title_font,
                 bg=self.bg_color, fg=self.fg_color).grid(row=0, column=0, columnspan=4, pady=20, sticky='w')
        
        # Fund status display
        fund_frame = tk.LabelFrame(self.scrollable_frame, text="Fund Status", font=self.label_font,
                                 bg=self.bg_color, fg=self.fg_color)
        fund_frame.grid(row=0, column=1, padx=20, pady=10, sticky='ne')
        
        self.fund_status_label = tk.Label(fund_frame, font=self.label_font, bg=self.bg_color,
                                        text="Loading fund status...")
        self.fund_status_label.pack(padx=10, pady=10)
        
        tk.Button(fund_frame, text="Refresh Funds", command=self.refresh_fund_status,
                 bg=self.fg_color, fg='white', font=self.button_font).pack(padx=10, pady=10)

        form_frame = tk.LabelFrame(self.scrollable_frame, text="Loan Application", font=self.label_font,
                                   bg=self.bg_color, fg=self.fg_color)
        form_frame.grid(row=1, column=0, padx=20, pady=10, sticky='nsew')

        fields = [
            ('Applicant Name*', 'applicant_name', 'text', 30),
            ('Group Name*', 'group_name', 'text', 25),
            ('Loan Amount (₹)*', 'loan_amount', 'number', 15),
            ('Purpose*', 'purpose', 'text', 30),
            ('Duration (months)*', 'duration_months', 'number', 10),
            ('Interest Rate (%)*', 'interest_rate', 'number', 10),
            ('Status*', 'status', 'option', ['Pending', 'Approved', 'Rejected']),
            ('Rejection Reason', 'rejection_reason', 'text', 30),
            ('Approved Date', 'approved_date', 'date'),
            ('Funds Allocated', 'funds_allocated', 'checkbox'),
            ('Loan ID', 'loan_id', 'text', 30, True)
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

            elif field_type == 'number':
                width = field_data[3]
                var = tk.StringVar()
                entry = tk.Entry(form_frame, width=width, font=self.entry_font, textvariable=var)
                entry.grid(row=i, column=1, sticky='w', padx=5, pady=5, ipady=3)
                self.entries[field] = var

            elif field_type == 'option':
                options = field_data[3]
                var = tk.StringVar()
                option = ttk.Combobox(form_frame, textvariable=var, values=options, width=25, font=self.entry_font)
                option.grid(row=i, column=1, sticky='w', padx=5, pady=5, ipady=3)
                # Add a trace to detect when status changes to "Approved"
                var.trace("w", self.on_status_change)
                self.entries[field] = var
                
            elif field_type == 'date':
                self.entries[field] = tk.StringVar()
                date_entry = DateEntry(form_frame, width=15, background=self.fg_color,
                                      foreground='white', borderwidth=2, textvariable=self.entries[field])
                date_entry.grid(row=i, column=1, sticky='w', padx=5, pady=5, ipady=3)
                
            elif field_type == 'checkbox':
                var = tk.IntVar()
                checkbox = tk.Checkbutton(form_frame, variable=var, bg=self.bg_color)
                checkbox.grid(row=i, column=1, sticky='w', padx=5, pady=5)
                self.entries[field] = var

        button_frame = tk.Frame(form_frame, bg=self.bg_color)
        button_frame.grid(row=len(fields), column=0, columnspan=3, pady=15)

        btn_cfg = {'font': self.button_font, 'width': 12, 'padx': 10, 'pady': 8, 'bd': 0, 'highlightthickness': 0}
        tk.Button(button_frame, text="Add Loan", command=self.add_loan, bg=self.fg_color, fg='white', **btn_cfg).pack(side='left', padx=10)
        tk.Button(button_frame, text="Update", command=self.update_loan, bg=self.fg_color, fg='white', **btn_cfg).pack(side='left', padx=10)
        tk.Button(button_frame, text="Clear", command=self.clear_form, bg=self.fg_color, fg='white', **btn_cfg).pack(side='left', padx=10)
        tk.Button(button_frame, text="Delete", command=self.delete_loan, bg='red', fg='white', **btn_cfg).pack(side='left', padx=10)

        table_frame = tk.LabelFrame(self.scrollable_frame, text="Loan Records", font=self.label_font, bg=self.bg_color, fg=self.fg_color)
        table_frame.grid(row=2, column=0, padx=20, pady=20, sticky='nsew', columnspan=2)

        style = ttk.Style()
        style.configure("Treeview", font=('Arial', 11), rowheight=30)
        style.configure("Treeview.Heading", font=('Arial', 12, 'bold'))

        self.tree = ttk.Treeview(table_frame, columns=('ID', 'Applicant', 'Group', 'Amount', 'Purpose', 'Duration', 'Interest', 'Status', 'Approved Date', 'Funds'), 
                               selectmode='browse', height=8)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        self.tree.column('#0', width=50, anchor='center')
        self.tree.heading('#0', text='#')
        columns = ['ID', 'Applicant', 'Group', 'Amount', 'Purpose', 'Duration', 'Interest', 'Status', 'Approved Date', 'Funds']
        for col in columns:
            width = 80 if col in ['Approved Date', 'Funds'] else 120
            self.tree.column(col, width=width, anchor='w')
            self.tree.heading(col, text=col)

        self.tree.bind('<<TreeviewSelect>>', self.on_loan_select)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Add summary frame
        summary_frame = tk.LabelFrame(self.scrollable_frame, text="Loan Summary", font=self.label_font, 
                                     bg=self.bg_color, fg=self.fg_color)
        summary_frame.grid(row=3, column=0, padx=20, pady=10, sticky='nsew', columnspan=2)
        
        self.summary_label = tk.Label(summary_frame, text="", font=self.label_font, bg=self.bg_color, justify=tk.LEFT)
        self.summary_label.pack(padx=10, pady=10, fill='x')
        
        
        # Add a padding frame at the bottom to ensure better scrolling
        padding_frame = tk.Frame(self.scrollable_frame, bg=self.bg_color, height=50)
        padding_frame.grid(row=4, column=0, columnspan=2, sticky='ew')
        
        self.load_loans()
        self.refresh_fund_status()
        self.update_loan_summary()
        
        # Ensure canvas scrolling works for all content
        self.scrollable_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def on_canvas_resize(self, event):
        """Handle canvas resize events to ensure proper scrolling"""
        # Update the width of the scrollable frame when the canvas changes
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def get_form_data(self, include_loan_id=True):
        data = {}
        for field, entry in self.entries.items():
            if not include_loan_id and field == 'loan_id':
                continue
            if isinstance(entry, tk.Entry):
                data[field] = entry.get()
            elif isinstance(entry, tk.StringVar):
                data[field] = entry.get()
            elif isinstance(entry, tk.IntVar):
                data[field] = entry.get()
        return data
    
    def on_status_change(self, *args):
        """Handle status changes, especially when changing to Approved"""
        try:
            current_status = self.entries['status'].get()
            if current_status == "Approved":
                # Set the approved date to today if empty
                if not self.entries['approved_date'].get():
                    self.entries['approved_date'].set(datetime.now().strftime('%Y-%m-%d'))
                
                # Check the funds_allocated checkbox
                self.entries['funds_allocated'].set(1)
                
                # Check if we have funds for this loan
                loan_amount = float(self.entries['loan_amount'].get())
                funds_available = self.get_available_funds()
                
                if loan_amount > funds_available:
                    messagebox.showwarning("Insufficient Funds", 
                                          f"Cannot approve this loan. Required amount (₹{loan_amount:,.2f}) exceeds available funds (₹{funds_available:,.2f}).")
                    # Reset status to Pending
                    self.entries['status'].set("Pending")
                    self.entries['funds_allocated'].set(0)
            elif current_status != "Approved":
                # Clear funds_allocated if not approved
                self.entries['funds_allocated'].set(0)
        except Exception as e:
            pass  # Ignore errors during input

    def add_loan(self):
        try:
            loan_id = f"LOAN{int(datetime.now().timestamp())}"
            self.entries['loan_id'].config(state='normal')
            self.entries['loan_id'].delete(0, tk.END)
            self.entries['loan_id'].insert(0, loan_id)
            self.entries['loan_id'].config(state='disabled')

            data = self.get_form_data()

            # Validate numeric fields
            try:
                data['loan_amount'] = float(data['loan_amount'])
                data['duration_months'] = int(data['duration_months'])
                data['interest_rate'] = float(data['interest_rate'])
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers for amount, duration and interest rate")
                return
                
            # Check if loan is approved and if we have enough funds
            if data['status'] == "Approved":
                funds_available = self.get_available_funds()
                if data['loan_amount'] > funds_available:
                    messagebox.showerror("Error", f"Insufficient funds available. Required: ₹{data['loan_amount']:,.2f}, Available: ₹{funds_available:,.2f}")
                    return
                
                # Ensure approved_date is set for approved loans
                if not data['approved_date']:
                    data['approved_date'] = datetime.now().strftime('%Y-%m-%d')
                
                # Make sure funds_allocated is set to 1 if status is approved
                data['funds_allocated'] = 1
            else:
                # If not approved, funds should not be allocated
                data['funds_allocated'] = 0
                # Clear approved date if status is not approved
                if data['status'] != "Approved":
                    data['approved_date'] = ""

            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            values = tuple(data.values())

            self.cursor.execute(f"INSERT INTO loans ({columns}) VALUES ({placeholders})", values)
            
            # Update fund allocation if loan is approved
            if data['status'] == "Approved" and data['funds_allocated'] == 1:
                self.update_fund_allocation(data['loan_amount'])
                
            self.conn.commit()
            messagebox.showinfo("Success", "Loan application added successfully")
            self.load_loans()
            self.clear_form()
            self.refresh_fund_status()
            self.update_loan_summary()
            
            # Ensure canvas scrolling shows all content after update
            self.scrollable_frame.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
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
                
            # Get the original loan data to check if status is changing
            self.cursor.execute("SELECT status, loan_amount, funds_allocated FROM loans WHERE loan_id=?", (loan_id,))
            original_data = self.cursor.fetchone()
            if not original_data:
                messagebox.showerror("Error", "Loan record not found")
                return
                
            original_status, original_amount, original_funds_allocated = original_data
            
            # Convert funds_allocated to int if it's None
            if original_funds_allocated is None:
                original_funds_allocated = 0
            
            # Get new data from form
            data = self.get_form_data(include_loan_id=False)
            
            # Validate numeric fields
            try:
                data['loan_amount'] = float(data['loan_amount'])
                data['duration_months'] = int(data['duration_months'])
                data['interest_rate'] = float(data['interest_rate'])
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers for amount, duration and interest rate")
                return
            
            # Check if status is changing to Approved and if we have enough funds
            if data['status'] == "Approved" and original_status != "Approved":
                funds_available = self.get_available_funds()
                if data['loan_amount'] > funds_available:
                    messagebox.showerror("Error", f"Insufficient funds available. Required: ₹{data['loan_amount']:,.2f}, Available: ₹{funds_available:,.2f}")
                    return
                # Add approval date for newly approved loans if not already set
                if not data['approved_date']:
                    data['approved_date'] = datetime.now().strftime('%Y-%m-%d')
                # Set funds_allocated to 1
                data['funds_allocated'] = 1
            
            # Check if status is changing from Approved to something else
            if original_status == "Approved" and data['status'] != "Approved" and original_funds_allocated == 1:
                # Return the funds to the available pool
                self.update_fund_allocation(-original_amount)
                data['funds_allocated'] = 0
                # Clear the approved date
                data['approved_date'] = ""
            
            # Check if loan amount is changing while status remains Approved
            if data['status'] == "Approved" and original_status == "Approved" and data['loan_amount'] != original_amount and original_funds_allocated == 1:
                # Calculate difference and update allocation
                difference = data['loan_amount'] - original_amount
                funds_available = self.get_available_funds()
                if difference > 0 and difference > funds_available:
                    messagebox.showerror("Error", f"Insufficient funds for amount increase. Required: ₹{difference:,.2f}, Available: ₹{funds_available:,.2f}")
                    return
                self.update_fund_allocation(difference)
            
            # Consistency check: ensure funds_allocated aligns with status
            if data['status'] == "Approved":
                data['funds_allocated'] = 1
            else:
                data['funds_allocated'] = 0

            updates = ', '.join([f"{key}=?" for key in data])
            values = tuple(data.values()) + (loan_id,)

            self.cursor.execute(f"UPDATE loans SET {updates} WHERE loan_id=?", values)
            self.conn.commit()
            messagebox.showinfo("Success", "Loan updated successfully")
            self.load_loans()
            self.refresh_fund_status()
            self.update_loan_summary()
            
            # Ensure canvas scrolling shows all content after update
            self.scrollable_frame.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_loan(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a loan to delete")
            return
        
        loan_id = self.tree.item(selected_item)['values'][0]
        
        # Check if this is an approved loan with allocated funds
        self.cursor.execute("SELECT status, loan_amount, funds_allocated FROM loans WHERE loan_id=?", (loan_id,))
        loan_data = self.cursor.fetchone()
        if loan_data and loan_data[0] == "Approved" and loan_data[2] == 1:
            # Return funds to available pool
            self.update_fund_allocation(-loan_data[1])
        
        self.cursor.execute("DELETE FROM loans WHERE loan_id=?", (loan_id,))
        self.conn.commit()
        messagebox.showinfo("Success", "Loan deleted successfully")
        self.load_loans()
        self.clear_form()
        self.refresh_fund_status()
        self.update_loan_summary()
        
        # Ensure canvas scrolling shows all content after update
        self.scrollable_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def clear_form(self):
        for field, entry in self.entries.items():
            if isinstance(entry, tk.Entry):
                state = entry['state']
                entry.config(state='normal')
                entry.delete(0, tk.END)
                if state == 'disabled':
                    entry.config(state='disabled')
            elif isinstance(entry, tk.StringVar):
                entry.set('')
            elif isinstance(entry, tk.IntVar):
                entry.set(0)

    def load_loans(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        # Check which columns exist
        try:
            self.cursor.execute("SELECT loan_id, applicant_name, group_name, loan_amount, purpose, duration_months, interest_rate, status, approved_date, funds_allocated FROM loans")
        except sqlite3.OperationalError:
            # Fallback to basic query without the new columns
            self.cursor.execute("SELECT loan_id, applicant_name, group_name, loan_amount, purpose, duration_months, interest_rate, status FROM loans")
            
        for i, row in enumerate(self.cursor.fetchall(), start=1):
            formatted_row = list(row)
            formatted_row[3] = f"₹{formatted_row[3]:,.2f}"  # Format amount
            formatted_row[6] = f"{formatted_row[6]}%"      # Format interest rate
            
            # Handle the case where we might not have all columns
            if len(formatted_row) > 8:  # If we have approved_date and funds_allocated
                if formatted_row[9] is not None:
                    formatted_row[9] = "Yes" if formatted_row[9] == 1 else "No"  # Format funds_allocated
                else:
                    formatted_row.append("")  # Empty placeholder for funds_allocated
            else:
                # Add empty values for missing columns
                formatted_row.append("")  # Empty placeholder for approved_date
                formatted_row.append("No")  # Default for funds_allocated
                
            self.tree.insert('', 'end', text=str(i), values=formatted_row)
    
    def update_loan_summary(self):
        """Update the loan summary information"""
        try:
            # Get total number of loans
            self.cursor.execute("SELECT COUNT(*) FROM loans")
            total_loans = self.cursor.fetchone()[0]
            
            # Get number of approved loans
            self.cursor.execute("SELECT COUNT(*) FROM loans WHERE status='Approved'")
            approved_loans = self.cursor.fetchone()[0]
            
            # Get number of pending loans
            self.cursor.execute("SELECT COUNT(*) FROM loans WHERE status='Pending'")
            pending_loans = self.cursor.fetchone()[0]
            
            # Get total amount of approved loans
            self.cursor.execute("SELECT SUM(loan_amount) FROM loans WHERE status='Approved'")
            total_approved_amount = self.cursor.fetchone()[0] or 0
            
            # Get total amount of pending loans
            self.cursor.execute("SELECT SUM(loan_amount) FROM loans WHERE status='Pending'")
            total_pending_amount = self.cursor.fetchone()[0] or 0
            
            # Try to get total with funds allocated
            try:
                self.cursor.execute("SELECT COUNT(*) FROM loans WHERE funds_allocated=1")
                funds_allocated_count = self.cursor.fetchone()[0]
            except sqlite3.OperationalError:
                funds_allocated_count = 0
            
            summary_text = (
                f"Total Loans: {total_loans}   |   "
                f"Approved: {approved_loans} (₹{total_approved_amount:,.2f})   |   "
                f"Pending: {pending_loans} (₹{total_pending_amount:,.2f})   |   "
                f"Funds Allocated: {funds_allocated_count}   |   "
                f"Available Funds: ₹{self.get_available_funds():,.2f}"
            )
            
            self.summary_label.config(text=summary_text)
            
            # Ensure summary is visible by adjusting canvas scroll region
            self.scrollable_frame.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
        except Exception as e:
            self.summary_label.config(text=f"Error updating summary: {str(e)}")

    def on_loan_select(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        loan_id = self.tree.item(selected_item)['values'][0]
        self.cursor.execute("SELECT * FROM loans WHERE loan_id=?", (loan_id,))
        loan_data = self.cursor.fetchone()
        if loan_data:
            columns = [desc[0] for desc in self.cursor.description]
            for i, field in enumerate(columns):
                if field in self.entries:
                    entry = self.entries[field]
                    if isinstance(entry, tk.Entry):
                        entry.config(state='normal')
                        entry.delete(0, tk.END)
                        entry.insert(0, str(loan_data[i]) if loan_data[i] is not None else "")
                        if field == 'loan_id':
                            entry.config(state='disabled')
                    elif isinstance(entry, tk.StringVar):
                        entry.set(str(loan_data[i]) if loan_data[i] is not None else "")
                    elif isinstance(entry, tk.IntVar):
                        entry.set(1 if loan_data[i] == 1 else 0)
    
    def get_contribution_net_total(self):
        """Get the net total from the contributions database"""
        try:
            # Connect to the contribution database
            contribution_conn = sqlite3.connect('contributiondb.db')
            contribution_cursor = contribution_conn.cursor()
            
            # Calculate total verified contributions
            contribution_cursor.execute("SELECT SUM(CAST(amount AS REAL)) FROM contributions WHERE status='Verified'")
            total_contributions = contribution_cursor.fetchone()[0] or 0
            
            # Calculate total credits
            contribution_cursor.execute("SELECT SUM(CAST(credit_amount AS REAL)) FROM credits")
            total_credits = contribution_cursor.fetchone()[0] or 0
            
            # Calculate net total (contributions - credits)
            net_total = total_contributions - total_credits
            
            contribution_conn.close()
            return net_total
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to access contribution data: {str(e)}")
            return 0
    
    def get_total_allocated_funds(self):
        """Get the total amount allocated to approve"""
        
    def get_total_allocated_funds(self):
        """Get the total amount allocated to approved loans"""
        try:
            self.cursor.execute("SELECT total_allocated FROM fund_allocation LIMIT 1")
            result = self.cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            return 0
    
    def update_fund_allocation(self, amount_change):
        """Update the fund allocation when approving/unapproving loans"""
        try:
            self.cursor.execute("SELECT total_allocated FROM fund_allocation LIMIT 1")
            current_allocated = self.cursor.fetchone()[0]
            new_allocated = current_allocated + amount_change
            self.cursor.execute("UPDATE fund_allocation SET total_allocated = ?, last_updated = ?", 
                              (new_allocated, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            self.conn.commit()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update fund allocation: {str(e)}")
    
    def get_available_funds(self):
        """Calculate available funds (net total - allocated)"""
        try:
            net_total = self.get_contribution_net_total()
            allocated = self.get_total_allocated_funds()
            return net_total - allocated
        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate available funds: {str(e)}")
            return 0
    
    def refresh_fund_status(self):
        """Refresh the fund status display"""
        try:
            net_total = self.get_contribution_net_total()
            allocated = self.get_total_allocated_funds()
            available = net_total - allocated
            
            # Update fund allocation database with latest net total
            self.cursor.execute("UPDATE fund_allocation SET total_available = ?, last_updated = ?", 
                              (net_total, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            self.conn.commit()
            
            status_text = (
                f"Total Fund: ₹{net_total:,.2f}\n"
                f"Allocated: ₹{allocated:,.2f}\n"
                f"Available: ₹{available:,.2f}"
            )
            self.fund_status_label.config(text=status_text)
            
            # After updating the fund status, make sure scrolling is updated
            self.scrollable_frame.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
        except Exception as e:
            self.fund_status_label.config(text=f"Error: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x800")
    root.title("Loan Management System")
    
    # Improve scrolling behavior by adding these settings
    root.update_idletasks()
    
    app = LoanManagement(root, "#F6DED8", "#D2665A")
    
    # Set window minimum size to ensure UI elements don't get too compressed
    root.minsize(1000, 700)
    
    # Add key bindings for Page Up/Page Down for faster scrolling
    def page_up(event):
        app.canvas.yview_scroll(-1, "pages")
        
    def page_down(event):
        app.canvas.yview_scroll(1, "pages")
        
    root.bind("<Prior>", page_up)  # Page Up key
    root.bind("<Next>", page_down)  # Page Down key
    
    # Make sure scroll region is properly set after everything is loaded
    root.after(100, lambda: app.canvas.config(scrollregion=app.canvas.bbox("all")))
    
    root.mainloop()
    
    