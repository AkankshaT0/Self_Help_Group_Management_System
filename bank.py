import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

class BankAccountManagement:
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

    def setup_db(self):
        self.conn = sqlite3.connect('bankdb.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bank_accounts (
                account_id TEXT PRIMARY KEY,
                member_id TEXT NOT NULL CHECK (LENGTH(member_id) > 0),
                account_holder_name TEXT NOT NULL CHECK (LENGTH(account_holder_name) > 0),
                account_number TEXT NOT NULL UNIQUE CHECK (LENGTH(account_number) >= 10),
                bank_name TEXT NOT NULL CHECK (LENGTH(bank_name) > 0),
                ifsc_code TEXT NOT NULL CHECK (LENGTH(ifsc_code) = 11),
                account_type TEXT NOT NULL CHECK (account_type IN ('Savings', 'Current', 'Joint')),
                linked_mobile TEXT NOT NULL CHECK (linked_mobile GLOB '[6-9][0-9]{9}'),
                verification_status TEXT NOT NULL CHECK (verification_status IN ('Pending', 'Verified', 'Rejected'))
            )
        ''')
        self.conn.commit()

    def create_ui(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

        tk.Label(self.parent, text="Bank Account Management", font=self.title_font,
                 bg=self.bg_color, fg=self.fg_color).pack(pady=20)

        form_frame = tk.Frame(self.parent, bg=self.bg_color)
        form_frame.pack(pady=10)

        labels = [
            "Member ID", "Account Holder Name", "Account Number", "Bank Name",
            "IFSC Code", "Account Type", "Linked Mobile", "Verification Status"
        ]

        self.entries = {}
        for i, label in enumerate(labels):
            tk.Label(form_frame, text=label, font=self.label_font, bg=self.bg_color).grid(row=i, column=0, sticky='e', padx=5, pady=5)

            if label == "Account Type":
                var = tk.StringVar()
                combo = ttk.Combobox(form_frame, textvariable=var, values=["Savings", "Current", "Joint"], font=self.entry_font)
                combo.grid(row=i, column=1, padx=5, pady=5)
                self.entries['account_type'] = var

            elif label == "Verification Status":
                var = tk.StringVar()
                combo = ttk.Combobox(form_frame, textvariable=var, values=["Pending", "Verified", "Rejected"], font=self.entry_font)
                combo.grid(row=i, column=1, padx=5, pady=5)
                self.entries['verification_status'] = var

            else:
                entry = tk.Entry(form_frame, font=self.entry_font)
                entry.grid(row=i, column=1, padx=5, pady=5)
                self.entries[label.lower().replace(" ", "_")] = entry

        button_frame = tk.Frame(self.parent, bg=self.bg_color)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Add Account", command=self.add_account,
                  bg=self.fg_color, fg="white", font=self.button_font).pack(side='left', padx=10)

        tk.Button(button_frame, text="Update", command=self.update_account,
                  bg=self.fg_color, fg="white", font=self.button_font).pack(side='left', padx=10)

        tk.Button(button_frame, text="Delete", command=self.delete_account,
                  bg=self.fg_color, fg="white", font=self.button_font).pack(side='left', padx=10)

        self.tree = ttk.Treeview(self.parent, columns=list(self.entries.keys()), show='headings')
        for col in self.entries:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=150)

        self.tree.pack(pady=10, fill='x')
        self.tree.bind("<Double-1>", self.on_tree_select)

    def generate_account_id(self):
        return f"ACC{int(datetime.now().timestamp())}"

    def get_form_data(self):
        data = {key: var.get() if isinstance(var, tk.StringVar) else var.get() for key, var in self.entries.items()}
        return data

    def add_account(self):
        try:
            data = self.get_form_data()
            data['account_id'] = self.generate_account_id()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            values = tuple(data.values())
            self.cursor.execute(f"INSERT INTO bank_accounts ({columns}) VALUES ({placeholders})", values)
            self.conn.commit()
            self.refresh_table()
            messagebox.showinfo("Success", "Account added successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.cursor.execute("SELECT member_id, account_holder_name, account_number, bank_name, ifsc_code, account_type, linked_mobile, verification_status FROM bank_accounts")
        for row in self.cursor.fetchall():
            self.tree.insert('', 'end', values=row)

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0])['values']
            keys = list(self.entries.keys())
            for i in range(len(keys)):
                field = keys[i]
                entry = self.entries[field]
                if isinstance(entry, tk.StringVar):
                    entry.set(values[i])
                else:
                    entry.delete(0, tk.END)
                    entry.insert(0, values[i])

    def update_account(self):
        try:
            selected = self.tree.selection()
            if not selected:
                messagebox.showwarning("Select Record", "Please select a record to update")
                return

            member_id = self.entries['member_id'].get()
            data = self.get_form_data()
            values = list(data.values()) + [member_id]
            query = f"UPDATE bank_accounts SET {', '.join([f'{k}=?' for k in data])} WHERE member_id = ?"
            self.cursor.execute(query, values)
            self.conn.commit()
            self.refresh_table()
            messagebox.showinfo("Success", "Account updated successfully")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_account(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Record", "Please select a record to delete")
            return
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this account?")
        if confirm:
            values = self.tree.item(selected[0])['values']
            member_id = values[0]
            self.cursor.execute("DELETE FROM bank_accounts WHERE member_id = ?", (member_id,))
            self.conn.commit()
            self.refresh_table()
            messagebox.showinfo("Deleted", "Account deleted successfully")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x700")
    root.title("Bank Account Management System")
    app = BankAccountManagement(root, "#F6DED8", "#D2665A")
    root.mainloop()
