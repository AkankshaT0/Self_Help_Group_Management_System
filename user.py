import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

class UserManagement:
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
        self.conn = sqlite3.connect('shg_management.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                dob TEXT NOT NULL,
                gender TEXT NOT NULL,
                reg_date TEXT NOT NULL,
                account_status TEXT NOT NULL,
                primary_phone TEXT UNIQUE NOT NULL,
                secondary_phone TEXT,
                email TEXT UNIQUE,
                emergency_contact TEXT NOT NULL,
                street TEXT,
                city TEXT,
                state TEXT,
                postal_code TEXT,
                country TEXT,
                is_phone_verified INTEGER DEFAULT 0,
                is_email_verified INTEGER DEFAULT 0
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

        tk.Label(self.scrollable_frame, text="User Management", font=self.title_font, bg=self.bg_color, fg=self.fg_color).grid(row=0, column=0, columnspan=4, pady=20, sticky='w')

        form_frame = tk.LabelFrame(self.scrollable_frame, text="Add/Edit User", font=self.label_font, bg=self.bg_color, fg=self.fg_color)
        form_frame.grid(row=1, column=0, padx=20, pady=10, sticky='nsew')

        fields = [
            ('First Name*', 'first_name', 'text', 30),
            ('Last Name*', 'last_name', 'text', 30),
            ('Date of Birth* (YYYY-MM-DD)', 'dob', 'text', 15),
            ('Gender*', 'gender', 'option', ['Male', 'Female', 'Other']),
            ('User ID', 'user_id', 'text', 20, True),
            ('Registration Date', 'reg_date', 'text', 15, True),
            ('Account Status*', 'account_status', 'option', ['Active', 'Inactive', 'Pending']),
            ('Primary Phone*', 'primary_phone', 'text', 20),
            ('Secondary Phone', 'secondary_phone', 'text', 20),
            ('Email', 'email', 'text', 30),
            ('Emergency Contact*', 'emergency_contact', 'text', 20),
            ('Street', 'street', 'text', 40),
            ('City', 'city', 'text', 20),
            ('State', 'state', 'text', 20),
            ('Postal Code', 'postal_code', 'text', 15),
            ('Country', 'country', 'text', 20)
        ]

        self.entries = {}
        for i, field_data in enumerate(fields):
            label, field, field_type = field_data[0], field_data[1], field_data[2]
            width = field_data[3] if len(field_data) > 3 else 20
            disabled = field_data[4] if len(field_data) > 4 else False
            options = field_data[3] if field_type == 'option' else []

            row = i % 9
            col = i // 9 * 2

            tk.Label(form_frame, text=label, font=self.label_font, bg=self.bg_color).grid(row=row, column=col, sticky='e', padx=5, pady=5)

            if field_type == 'text':
                entry = tk.Entry(form_frame, width=width, font=self.entry_font)
                if disabled:
                    entry.config(state='disabled')
                entry.grid(row=row, column=col + 1, sticky='w', padx=5, pady=5, ipady=3)
                self.entries[field] = entry
            elif field_type == 'option':
                var = tk.StringVar()
                option = ttk.Combobox(form_frame, textvariable=var, values=options, width=20, font=self.entry_font)
                option.grid(row=row, column=col + 1, sticky='w', padx=5, pady=5, ipady=3)
                self.entries[field] = var

        button_frame = tk.Frame(form_frame, bg=self.bg_color)
        button_frame.grid(row=9, column=0, columnspan=4, pady=15)

        button_config = {'font': self.button_font, 'width': 12, 'padx': 10, 'pady': 8, 'bd': 0, 'highlightthickness': 0}

        tk.Button(button_frame, text="Add User", command=self.add_user, bg=self.fg_color, fg='white', **button_config).pack(side='left', padx=10)
        tk.Button(button_frame, text="Update", command=self.update_user, bg=self.fg_color, fg='white', **button_config).pack(side='left', padx=10)
        tk.Button(button_frame, text="Clear", command=self.clear_form, bg=self.fg_color, fg='white', **button_config).pack(side='left', padx=10)
        tk.Button(button_frame, text="Delete", command=self.delete_user, bg='red', fg='white', **button_config).pack(side='left', padx=10)

        table_frame = tk.LabelFrame(self.scrollable_frame, text="User Records", font=self.label_font, bg=self.bg_color, fg=self.fg_color)
        table_frame.grid(row=2, column=0, padx=20, pady=20, sticky='nsew')

        style = ttk.Style()
        style.configure("Treeview", font=('Arial', 11), rowheight=30)
        style.configure("Treeview.Heading", font=('Arial', 12, 'bold'))

        self.tree = ttk.Treeview(table_frame, columns=('ID', 'Name', 'Phone', 'Status', 'Email'), selectmode='browse', height=8)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        self.tree.column('#0', width=50, anchor='center')
        self.tree.heading('#0', text='#')
        self.tree.column('ID', width=150, anchor='w')
        self.tree.heading('ID', text='User ID')
        self.tree.column('Name', width=200, anchor='w')
        self.tree.heading('Name', text='Name')
        self.tree.column('Phone', width=150, anchor='w')
        self.tree.heading('Phone', text='Phone')
        self.tree.column('Status', width=100, anchor='center')
        self.tree.heading('Status', text='Status')
        self.tree.column('Email', width=200, anchor='w')
        self.tree.heading('Email', text='Email')

        self.tree.bind('<<TreeviewSelect>>', self.on_user_select)

        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.load_users()

    def add_user(self):
        try:
            now = datetime.now().strftime("%Y-%m-%d")
            user_id = f"USR{int(datetime.now().timestamp())}"
            self.entries['user_id'].config(state='normal')
            self.entries['user_id'].delete(0, tk.END)
            self.entries['user_id'].insert(0, user_id)
            self.entries['user_id'].config(state='disabled')

            self.entries['reg_date'].config(state='normal')
            self.entries['reg_date'].delete(0, tk.END)
            self.entries['reg_date'].insert(0, now)
            self.entries['reg_date'].config(state='disabled')

            data = {field: (entry.get() if isinstance(entry, tk.Entry) else entry.get()) for field, entry in self.entries.items()}

            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            values = tuple(data.values())

            self.cursor.execute(f"INSERT INTO users ({columns}) VALUES ({placeholders})", values)
            self.conn.commit()
            messagebox.showinfo("Success", "User added successfully")
            self.load_users()
            self.clear_form()
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Integrity error: {e}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_user(self):
        try:
            user_id = self.entries['user_id'].get()
            data = {field: (entry.get() if isinstance(entry, tk.Entry) else entry.get()) for field, entry in self.entries.items() if field not in ['user_id', 'reg_date']}
            updates = ', '.join([f"{key}=?" for key in data])
            values = tuple(data.values()) + (user_id,)

            self.cursor.execute(f"UPDATE users SET {updates} WHERE user_id=?", values)
            self.conn.commit()
            messagebox.showinfo("Success", "User updated successfully")
            self.load_users()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_user(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a user to delete")
            return
        user_id = self.tree.item(selected_item)['values'][0]
        self.cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        self.conn.commit()
        messagebox.showinfo("Success", "User deleted successfully")
        self.load_users()
        self.clear_form()

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

    def load_users(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.cursor.execute("SELECT user_id, first_name || ' ' || last_name AS name, primary_phone, account_status, email FROM users")
        for i, row in enumerate(self.cursor.fetchall(), start=1):
            self.tree.insert('', 'end', text=str(i), values=row)

    def on_user_select(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        values = self.tree.item(selected_item)['values']
        user_id = values[0]
        self.cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user = self.cursor.fetchone()
        if user:
            columns = [description[0] for description in self.cursor.description]
            for i, field in enumerate(columns):
                if field in self.entries:
                    if isinstance(self.entries[field], tk.Entry):
                        self.entries[field].config(state='normal')
                        self.entries[field].delete(0, tk.END)
                        self.entries[field].insert(0, user[i])
                        if field in ['user_id', 'reg_date']:
                            self.entries[field].config(state='disabled')
                    elif isinstance(self.entries[field], tk.StringVar):
                        self.entries[field].set(user[i])

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x800")
    root.title("User Management System")
    user_mgmt = UserManagement(root, "#F6DED8", "#D2665A")
    root.mainloop()
