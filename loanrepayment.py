import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
from fpdf import FPDF
import os

class LoanRepaymentSystem:
    def __init__(self, root):
        self.root = root
        #self.root.title("Loan Repayment System")
        #self.root.geometry("1100x800")  # Reduced width since we removed a column
        #self.root.configure(bg="#F6DED8")

        # Connect to databases and ensure tables exist
        self.setup_databases()
        self.create_widgets()
        self.load_data()
        self.load_loan_ids()

    def setup_databases(self):
        """Set up and connect to all required databases and create tables if they don't exist"""
        # Set up loan database
        self.loan_conn = sqlite3.connect('loandb.db')
        self.loan_cursor = self.loan_conn.cursor()
        
        # Create loans table if it doesn't exist
        self.loan_cursor.execute('''
            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                loan_id TEXT UNIQUE,
                borrower_name TEXT,
                loan_amount REAL,
                loan_date TEXT,
                loan_term TEXT
            )
        ''')
        self.loan_conn.commit()
        
        # Set up repayment database
        self.repay_conn = sqlite3.connect('repaymentdb.db')
        self.repay_cursor = self.repay_conn.cursor()
        
        # Create repayments table if it doesn't exist
        self.repay_cursor.execute('''
            CREATE TABLE IF NOT EXISTS repayments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                loan_id TEXT,
                repay_amount REAL,
                repay_date TEXT,
                remaining REAL
            )
        ''')
        self.repay_conn.commit()

    def create_widgets(self):
        # Main frame with padding
        main_frame = tk.Frame(self.root, bg="#F6DED8")
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Form
        frame = tk.LabelFrame(main_frame, text="Repayment Entry", padx=20, pady=20, 
                            bg="#F6DED8", fg="#D2665A", font=("Arial", 14, "bold"))
        frame.pack(fill="x", pady=10)

        # Loan ID with dropdown
        tk.Label(frame, text="Loan ID:", bg="#F6DED8", fg="#D2665A", 
                font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="e", pady=10)
        self.loan_id_var = tk.StringVar()
        self.loan_id_combobox = ttk.Combobox(frame, textvariable=self.loan_id_var, 
                                            font=("Arial", 12), width=38)
        self.loan_id_combobox.grid(row=0, column=1, padx=10)
        self.loan_id_combobox.bind("<FocusOut>", self.validate_loan_id)

        # Other fields
        tk.Label(frame, text="Repay Amount:", bg="#F6DED8", fg="#D2665A", 
                font=("Arial", 12, "bold")).grid(row=1, column=0, sticky="e", pady=10)
        self.repay_amount_entry = tk.Entry(frame, font=("Arial", 12), width=40)
        self.repay_amount_entry.grid(row=1, column=1, padx=10)

        tk.Label(frame, text="Repay Date:", bg="#F6DED8", fg="#D2665A", 
                font=("Arial", 12, "bold")).grid(row=2, column=0, sticky="e", pady=10)
        self.date_entry = DateEntry(frame, date_pattern="yyyy-mm-dd", 
                                  font=("Arial", 12), width=37)
        self.date_entry.grid(row=2, column=1, padx=10)

        # Buttons
        button_frame = tk.Frame(frame, bg="#F6DED8")
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        style = {"font": ("Arial", 12, "bold"), "bg": "#D2665A", 
                "fg": "white", "width": 15}

        tk.Button(button_frame, text="Add", command=self.add_repayment, **style).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="Update", command=self.update_repayment, **style).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="Delete", command=self.delete_repayment, **style).grid(row=0, column=2, padx=5)
        tk.Button(button_frame, text="Clear", command=self.clear_form, **style).grid(row=0, column=3, padx=5)
       # tk.Button(button_frame, text="Generate PDF", command=self.generate_pdf, **style).grid(row=0, column=4, padx=5)

        # Table with scrollbars
        table_frame = tk.Frame(main_frame)
        table_frame.pack(fill="both", expand=True)
        
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        # Removed "Total Amount" column
        self.tree = ttk.Treeview(table_frame, 
                                columns=("ID", "Loan ID", "Repay Amount", "Repay Date", "Remaining"), 
                                show="headings", height=15)
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Configure style
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), foreground="#D2665A")
        style.configure("Treeview", font=("Arial", 11), rowheight=30)

        # Configure columns - removed "Total Amount"
        columns = [
            ("ID", 100),
            ("Loan ID", 200),
            ("Repay Amount", 200),
            ("Repay Date", 200),
            ("Remaining", 200)
        ]

        for col_name, width in columns:
            self.tree.heading(col_name, text=col_name)
            self.tree.column(col_name, width=width, anchor="center")

        self.tree.bind('<<TreeviewSelect>>', self.on_select)

    def load_loan_ids(self):
        """Load all valid loan IDs from the loans database"""
        try:
            self.loan_cursor.execute("SELECT loan_id FROM loans")
            loan_ids = [row[0] for row in self.loan_cursor.fetchall()]
            self.loan_id_combobox['values'] = loan_ids
        except sqlite3.Error as e:
            messagebox.showwarning("Warning", f"Could not load loan IDs: {str(e)}")

    def validate_loan_id(self, event=None):
        """Validate that the entered loan ID exists"""
        loan_id = self.loan_id_var.get().strip()
        if loan_id:
            try:
                self.loan_cursor.execute("SELECT 1 FROM loans WHERE loan_id = ?", (loan_id,))
                if not self.loan_cursor.fetchone():
                    messagebox.showerror("Error", "Invalid Loan ID. Please select from the dropdown.")
                    self.loan_id_var.set('')
                    return False
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Failed to validate loan ID: {str(e)}")
                return False
        return True

    def add_repayment(self):
        if not self.validate_loan_id():
            return

        loan_id = self.loan_id_var.get().strip()
        try:
            repay_amount = float(self.repay_amount_entry.get().strip())
            if repay_amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid positive amount")
            return

        repay_date = self.date_entry.get()

        # Get loan details
        try:
            self.loan_cursor.execute("SELECT loan_amount FROM loans WHERE loan_id = ?", (loan_id,))
            loan_data = self.loan_cursor.fetchone()
            if not loan_data:
                messagebox.showerror("Error", "Loan not found. Please select a valid loan ID.")
                return

            loan_amount = float(loan_data[0])

            # Calculate total paid so far
            self.repay_cursor.execute("SELECT SUM(repay_amount) FROM repayments WHERE loan_id = ?", (loan_id,))
            total_paid = self.repay_cursor.fetchone()[0] or 0.0
            new_total_paid = total_paid + repay_amount

            if new_total_paid > loan_amount:
                messagebox.showerror("Error", 
                                   f"Repayment exceeds loan amount. Maximum payment allowed: {loan_amount - total_paid:,.2f}")
                return

            remaining = loan_amount - new_total_paid

            self.repay_cursor.execute(
                "INSERT INTO repayments (loan_id, repay_amount, repay_date, remaining) VALUES (?, ?, ?, ?)",
                (loan_id, repay_amount, repay_date, remaining)
            )
            self.repay_conn.commit()
            self.load_data()
            self.clear_form()
            messagebox.showinfo("Success", "Repayment added successfully!")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to add repayment: {str(e)}")

    def update_repayment(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a record to update.")
            return

        if not self.validate_loan_id():
            return

        item = self.tree.item(selected)
        repay_id = item["values"][0]
        loan_id = self.loan_id_var.get().strip()

        try:
            repay_amount = float(self.repay_amount_entry.get().strip())
            if repay_amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid positive amount")
            return

        repay_date = self.date_entry.get()

        try:
            # Get loan details
            self.loan_cursor.execute("SELECT loan_amount FROM loans WHERE loan_id = ?", (loan_id,))
            loan_data = self.loan_cursor.fetchone()
            if not loan_data:
                messagebox.showerror("Error", "Loan not found. Please select a valid loan ID.")
                return

            loan_amount = float(loan_data[0])

            # Calculate total paid excluding current record
            self.repay_cursor.execute(
                "SELECT SUM(repay_amount) FROM repayments WHERE loan_id = ? AND id != ?",
                (loan_id, repay_id)
            )
            other_paid = self.repay_cursor.fetchone()[0] or 0.0

            if repay_amount + other_paid > loan_amount:
                messagebox.showerror("Error", 
                                   f"Updated amount exceeds loan limit. Maximum payment allowed: {loan_amount - other_paid:,.2f}")
                return

            remaining = loan_amount - (repay_amount + other_paid)

            self.repay_cursor.execute(
                "UPDATE repayments SET loan_id = ?, repay_amount = ?, repay_date = ?, remaining = ? WHERE id = ?",
                (loan_id, repay_amount, repay_date, remaining, repay_id)
            )
            self.repay_conn.commit()
            self.load_data()
            self.clear_form()
            messagebox.showinfo("Success", "Repayment updated successfully!")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to update repayment: {str(e)}")

    def delete_repayment(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a record to delete.")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this repayment record?"):
            repay_id = self.tree.item(selected)["values"][0]
            try:
                self.repay_cursor.execute("DELETE FROM repayments WHERE id = ?", (repay_id,))
                self.repay_conn.commit()
                self.load_data()
                self.clear_form()
                messagebox.showinfo("Success", "Repayment deleted successfully.")
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Failed to delete repayment: {str(e)}")

    def clear_form(self):
        self.loan_id_var.set('')
        self.repay_amount_entry.delete(0, tk.END)
        self.date_entry.set_date('')

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        try:
            # Load repayment data without total amount column
            self.repay_cursor.execute('''
                SELECT id, loan_id, repay_amount, repay_date, remaining 
                FROM repayments
                ORDER BY repay_date DESC
            ''')
            
            for row in self.repay_cursor.fetchall():
                # Format money values
                formatted_row = [
                    row[0],                  # ID
                    row[1],                  # Loan ID
                    f"{row[2]:,.2f}",        # Repay amount
                    row[3],                  # Date
                    f"{row[4]:,.2f}"         # Remaining
                ]
                self.tree.insert("", "end", values=formatted_row)
                
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load repayment data: {str(e)}")

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        
        values = self.tree.item(selected)["values"]
        if not values:
            return
        
        # Extract values correctly
        self.loan_id_var.set(values[1])  # Loan ID
        
        # Handle repay amount (may need to remove formatting)
        repay_amount = values[2]
        if isinstance(repay_amount, str):
            repay_amount = repay_amount.replace(',', '')
        
        self.repay_amount_entry.delete(0, tk.END)
        self.repay_amount_entry.insert(0, repay_amount)
        
        # Set date if available
        try:
            self.date_entry.set_date(values[3])
        except:
            # If date format is incompatible or empty
            pass

    def generate_pdf(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a record to generate PDF.")
            return
        
        values = self.tree.item(selected)["values"]
        if not values:
            return
        
        try:
            # Get loan amount from database for PDF
            loan_id = values[1]
            self.loan_cursor.execute("SELECT loan_amount FROM loans WHERE loan_id = ?", (loan_id,))
            loan_data = self.loan_cursor.fetchone()
            total_amount = "Unknown"
            if loan_data and loan_data[0]:
                total_amount = f"{float(loan_data[0]):,.2f}"
                
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=14)
            
            # Header
            pdf.cell(200, 10, txt="Loan Repayment Receipt", ln=True, align="C")
            pdf.ln(10)
            
            # Loan details
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Repayment ID: {values[0]}", ln=True)
            pdf.cell(200, 10, txt=f"Loan ID: {values[1]}", ln=True)
            pdf.cell(200, 10, txt=f"Total Loan Amount: {'' if total_amount == 'Unknown' else '₹'}{total_amount}", ln=True)
            pdf.cell(200, 10, txt=f"Amount Paid: ₹{values[2]}", ln=True)
            pdf.cell(200, 10, txt=f"Payment Date: {values[3]}", ln=True)
            pdf.cell(200, 10, txt=f"Remaining Balance: ₹{values[4]}", ln=True)
            
            filename = f"Repayment_Receipt_{values[0]}.pdf"
            pdf.output(filename)
            
            messagebox.showinfo("Success", f"PDF receipt generated: {filename}")
            
            # Try to open the file with default application
            try:
                os.startfile(filename)
            except AttributeError:
                # For non-Windows platforms
                import subprocess
                try:
                    subprocess.call(('xdg-open', filename))  # Linux
                except:
                    try:
                        subprocess.call(('open', filename))  # macOS
                    except:
                        messagebox.showinfo("Info", f"PDF saved as {filename}, but could not be opened automatically.")
                        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF: {str(e)}")

    def __del__(self):
        """Clean up database connections when object is destroyed"""
        try:
            if hasattr(self, 'loan_conn'):
                self.loan_conn.close()
            if hasattr(self, 'repay_conn'):
                self.repay_conn.close()
        except:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = LoanRepaymentSystem(root)
    root.mainloop()