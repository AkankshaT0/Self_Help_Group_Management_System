import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

class StaffManagement:
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
        self.conn = sqlite3.connect('staffdb.db')  # Changed to 'staffdb' database
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                staff_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                contact_info TEXT NOT NULL,
                assigned_groups TEXT NOT NULL,
                last_login TEXT,
                activity TEXT,
                status TEXT NOT NULL,
                emergency_contact TEXT NOT NULL,
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

        tk.Label(self.scrollable_frame, text="Staff Management", font=self.title_font, bg=self.bg_color, fg=self.fg_color).grid(row=0, column=0, columnspan=4, pady=20, sticky='w')

        form_frame = tk.LabelFrame(self.scrollable_frame, text="Add/Edit Staff", font=self.label_font, bg=self.bg_color, fg=self.fg_color)
        form_frame.grid(row=1, column=0, padx=20, pady=10, sticky='nsew')

        fields = [
            ('Full Name*', 'full_name', 'text', 30),
            ('Role*', 'role', 'option', ['Admin', 'Moderator', 'Support']),
            ('Staff ID', 'staff_id', 'text', 20, True),
            ('Contact Info*', 'contact_info', 'text', 30),
            ('Assigned Groups*', 'assigned_groups', 'text', 30),
            ('Last Login', 'last_login', 'text', 15, True),
            ('Activity', 'activity', 'text', 30),
            ('Status*', 'status', 'option', ['Active', 'Inactive', 'Pending']),
            ('Emergency Contact*', 'emergency_contact', 'text', 20)
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

        tk.Button(button_frame, text="Add Staff", command=self.add_staff, bg=self.fg_color, fg='white', **button_config).pack(side='left', padx=10)
        tk.Button(button_frame, text="Update", command=self.update_staff, bg=self.fg_color, fg='white', **button_config).pack(side='left', padx=10)
        tk.Button(button_frame, text="Clear", command=self.clear_form, bg=self.fg_color, fg='white', **button_config).pack(side='left', padx=10)
        tk.Button(button_frame, text="Delete", command=self.delete_staff, bg='red', fg='white', **button_config).pack(side='left', padx=10)

        table_frame = tk.LabelFrame(self.scrollable_frame, text="Staff Records", font=self.label_font, bg=self.bg_color, fg=self.fg_color)
        table_frame.grid(row=2, column=0, padx=20, pady=20, sticky='nsew')

        style = ttk.Style()
        style.configure("Treeview", font=('Arial', 11), rowheight=30)
        style.configure("Treeview.Heading", font=('Arial', 12, 'bold'))

        self.tree = ttk.Treeview(table_frame, columns=('ID', 'Full Name', 'Role', 'Status', 'Contact Info'), selectmode='browse', height=8)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        self.tree.column('#0', width=50, anchor='center')
        self.tree.heading('#0', text='#')
        self.tree.column('ID', width=150, anchor='w')
        self.tree.heading('ID', text='Staff ID')
        self.tree.column('Full Name', width=200, anchor='w')
        self.tree.heading('Full Name', text='Full Name')
        self.tree.column('Role', width=100, anchor='w')
        self.tree.heading('Role', text='Role')
        self.tree.column('Status', width=100, anchor='center')
        self.tree.heading('Status', text='Status')
        self.tree.column('Contact Info', width=200, anchor='w')
        self.tree.heading('Contact Info', text='Contact Info')

        self.tree.bind('<<TreeviewSelect>>', self.on_staff_select)

        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.load_staff()

    def add_staff(self):
        try:
            now = datetime.now().strftime("%Y-%m-%d")
            staff_id = f"STF{int(datetime.now().timestamp())}"
            self.entries['staff_id'].config(state='normal')
            self.entries['staff_id'].delete(0, tk.END)
            self.entries['staff_id'].insert(0, staff_id)
            self.entries['staff_id'].config(state='disabled')

            data = {field: (entry.get() if isinstance(entry, tk.Entry) else entry.get()) for field, entry in self.entries.items()}

            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            values = tuple(data.values())

            self.cursor.execute(f"INSERT INTO staff ({columns}) VALUES ({placeholders})", values)
            self.conn.commit()
            messagebox.showinfo("Success", "Staff added successfully")
            self.load_staff()
            self.clear_form()
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Integrity error: {e}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_staff(self):
        try:
            staff_id = self.entries['staff_id'].get()
            data = {field: (entry.get() if isinstance(entry, tk.Entry) else entry.get()) for field, entry in self.entries.items() if field not in ['staff_id']}
            updates = ', '.join([f"{key}=?" for key in data])
            values = tuple(data.values()) + (staff_id,)

            self.cursor.execute(f"UPDATE staff SET {updates} WHERE staff_id=?", values)
            self.conn.commit()
            messagebox.showinfo("Success", "Staff updated successfully")
            self.load_staff()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_staff(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a staff to delete")
            return
        staff_id = self.tree.item(selected_item)['values'][0]
        self.cursor.execute("DELETE FROM staff WHERE staff_id=?", (staff_id,))
        self.conn.commit()
        messagebox.showinfo("Success", "Staff deleted successfully")
        self.load_staff()
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

    def load_staff(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.cursor.execute("SELECT staff_id, full_name, role, status, contact_info FROM staff")
        for i, row in enumerate(self.cursor.fetchall(), start=1):
            self.tree.insert('', 'end', text=str(i), values=row)

    def on_staff_select(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        values = self.tree.item(selected_item)['values']
        staff_id = values[0]
        self.cursor.execute("SELECT * FROM staff WHERE staff_id=?", (staff_id,))
        staff = self.cursor.fetchone()
        if staff:
            columns = [description[0] for description in self.cursor.description]
            for i, field in enumerate(columns):
                if field in self.entries:
                    if isinstance(self.entries[field], tk.Entry):
                        self.entries[field].config(state='normal')
                        self.entries[field].delete(0, tk.END)
                        self.entries[field].insert(0, staff[i])
                        if field in ['staff_id']:
                            self.entries[field].config(state='disabled')
                    elif isinstance(self.entries[field], tk.StringVar):
                        self.entries[field].set(staff[i])

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x800")
    root.title("Staff Management System")
    user_mgmt = StaffManagement(root, "#F6DED8", "#D2665A")
    root.mainloop()
