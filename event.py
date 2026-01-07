import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime

class EventManagement:
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
        self.conn = sqlite3.connect('eventdb.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                event_type TEXT NOT NULL,
                start_datetime TEXT NOT NULL,
                end_datetime TEXT NOT NULL,
                location TEXT NOT NULL,
                organizer TEXT NOT NULL,
                status TEXT NOT NULL
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

        tk.Label(self.scrollable_frame, text="Event Management", font=self.title_font,
                 bg=self.bg_color, fg=self.fg_color).grid(row=0, column=0, columnspan=4, pady=20, sticky='w')

        form_frame = tk.LabelFrame(self.scrollable_frame, text="Add/Edit Event", font=self.label_font,
                                   bg=self.bg_color, fg=self.fg_color)
        form_frame.grid(row=1, column=0, padx=20, pady=10, sticky='nsew')

        fields = [
            ('Event Title*', 'title', 'text', 30),
            ('Event Type*', 'event_type', 'option', ['Meeting', 'Training', 'Collection', 'Social']),
            ('Start DateTime*', 'start_datetime', 'datetime'),
            ('End DateTime*', 'end_datetime', 'datetime'),
            ('Location*', 'location', 'text', 40),
            ('Organizer*', 'organizer', 'text', 25),
            ('Status*', 'status', 'option', ['Upcoming', 'Ongoing', 'Completed', 'Cancelled']),
            ('Event ID', 'event_id', 'text', 30, True)
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

            elif field_type == 'datetime':
                date_entry = DateEntry(form_frame, width=12, font=self.entry_font, background='darkblue', foreground='white', borderwidth=2)
                date_entry.grid(row=i, column=1, sticky='w', padx=5, pady=5)
                
                time_frame = tk.Frame(form_frame, bg=self.bg_color)
                time_frame.grid(row=i, column=2, sticky='w')
                hour_var = tk.StringVar(value='00')
                minute_var = tk.StringVar(value='00')
                hours = [f"{h:02d}" for h in range(24)]
                minutes = [f"{m:02d}" for m in range(0, 60, 5)]

                hour_box = ttk.Combobox(time_frame, textvariable=hour_var, values=hours, width=3, font=self.entry_font)
                minute_box = ttk.Combobox(time_frame, textvariable=minute_var, values=minutes, width=3, font=self.entry_font)

                hour_box.grid(row=0, column=0)
                tk.Label(time_frame, text=":", font=self.label_font, bg=self.bg_color).grid(row=0, column=1)
                minute_box.grid(row=0, column=2)
                self.entries[field] = (date_entry, hour_var, minute_var)

        button_frame = tk.Frame(form_frame, bg=self.bg_color)
        button_frame.grid(row=len(fields), column=0, columnspan=3, pady=15)

        btn_cfg = {'font': self.button_font, 'width': 12, 'padx': 10, 'pady': 8, 'bd': 0, 'highlightthickness': 0}
        tk.Button(button_frame, text="Add Event", command=self.add_event, bg=self.fg_color, fg='white', **btn_cfg).pack(side='left', padx=10)
        tk.Button(button_frame, text="Update", command=self.update_event, bg=self.fg_color, fg='white', **btn_cfg).pack(side='left', padx=10)
        tk.Button(button_frame, text="Clear", command=self.clear_form, bg=self.fg_color, fg='white', **btn_cfg).pack(side='left', padx=10)
        tk.Button(button_frame, text="Delete", command=self.delete_event, bg='red', fg='white', **btn_cfg).pack(side='left', padx=10)

        table_frame = tk.LabelFrame(self.scrollable_frame, text="Event Records", font=self.label_font, bg=self.bg_color, fg=self.fg_color)
        table_frame.grid(row=2, column=0, padx=20, pady=20, sticky='nsew')

        style = ttk.Style()
        style.configure("Treeview", font=('Arial', 11), rowheight=30)
        style.configure("Treeview.Heading", font=('Arial', 12, 'bold'))

        self.tree = ttk.Treeview(table_frame, columns=('ID', 'Title', 'Type', 'Start', 'End', 'Status'), selectmode='browse', height=8)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        self.tree.column('#0', width=50, anchor='center')
        self.tree.heading('#0', text='#')
        for col in ['ID', 'Title', 'Type', 'Start', 'End', 'Status']:
            self.tree.column(col, width=150, anchor='w')
            self.tree.heading(col, text=col)

        self.tree.bind('<<TreeviewSelect>>', self.on_event_select)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.load_events()

    def get_form_data(self, include_event_id=True):
        data = {}
        for field, entry in self.entries.items():
            if not include_event_id and field == 'event_id':
                continue
            if isinstance(entry, tuple):  # datetime field
                date_widget, hour_var, min_var = entry
                datetime_str = f"{date_widget.get()} {hour_var.get()}:{min_var.get()}"
                data[field] = datetime_str
            elif isinstance(entry, tk.Entry):
                data[field] = entry.get()
            elif isinstance(entry, tk.StringVar):
                data[field] = entry.get()
        return data

    def add_event(self):
        try:
            event_id = f"EVT{int(datetime.now().timestamp())}"
            self.entries['event_id'].config(state='normal')
            self.entries['event_id'].delete(0, tk.END)
            self.entries['event_id'].insert(0, event_id)
            self.entries['event_id'].config(state='disabled')

            data = self.get_form_data()

            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            values = tuple(data.values())

            self.cursor.execute(f"INSERT INTO events ({columns}) VALUES ({placeholders})", values)
            self.conn.commit()
            messagebox.showinfo("Success", "Event added successfully")
            self.load_events()
            self.clear_form()
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Integrity error: {e}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_event(self):
        try:
            event_id = self.entries['event_id'].get()
            data = self.get_form_data(include_event_id=False)
            updates = ', '.join([f"{key}=?" for key in data])
            values = tuple(data.values()) + (event_id,)

            self.cursor.execute(f"UPDATE events SET {updates} WHERE event_id=?", values)
            self.conn.commit()
            messagebox.showinfo("Success", "Event updated successfully")
            self.load_events()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_event(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select an event to delete")
            return
        event_id = self.tree.item(selected_item)['values'][0]
        self.cursor.execute("DELETE FROM events WHERE event_id=?", (event_id,))
        self.conn.commit()
        messagebox.showinfo("Success", "Event deleted successfully")
        self.load_events()
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
            elif isinstance(entry, tuple):
                date_widget, hour_var, min_var = entry
                date_widget.set_date(datetime.today())
                hour_var.set('00')
                min_var.set('00')

    def load_events(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.cursor.execute("SELECT event_id, title, event_type, start_datetime, end_datetime, status FROM events")
        for i, row in enumerate(self.cursor.fetchall(), start=1):
            self.tree.insert('', 'end', text=str(i), values=row)

    def on_event_select(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        event_id = self.tree.item(selected_item)['values'][0]
        self.cursor.execute("SELECT * FROM events WHERE event_id=?", (event_id,))
        event_data = self.cursor.fetchone()
        if event_data:
            columns = [desc[0] for desc in self.cursor.description]
            for i, field in enumerate(columns):
                if field in self.entries:
                    entry = self.entries[field]
                    if isinstance(entry, tk.Entry):
                        entry.config(state='normal')
                        entry.delete(0, tk.END)
                        entry.insert(0, event_data[i])
                        if field == 'event_id':
                            entry.config(state='disabled')
                    elif isinstance(entry, tk.StringVar):
                        entry.set(event_data[i])
                    elif isinstance(entry, tuple):
                        date_widget, hour_var, min_var = entry
                        dt_obj = datetime.strptime(event_data[i], "%Y-%m-%d %H:%M")
                        date_widget.set_date(dt_obj.date())
                        hour_var.set(f"{dt_obj.hour:02d}")
                        min_var.set(f"{dt_obj.minute:02d}")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x800")
    root.title("Event Management System")
    app = EventManagement(root, "#F6DED8", "#D2665A")
    root.mainloop()
