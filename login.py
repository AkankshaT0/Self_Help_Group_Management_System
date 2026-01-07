import subprocess
import tkinter as tk
from tkinter import messagebox, font

class LoginSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Self Help Group Management System")
        self.root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))
        self.root.configure(bg="#F6DED8")
        
        # Admin credentials
        self.admin_username = "selfhelpgroup"
        self.admin_password = "selfhelp123"
        
        # Member credentials
        self.member_username = "akanksha"
        self.member_password = "akanksha123"
        
        # Create fonts
        self.title_font = font.Font(family="Arial", size=24, weight="bold")
        self.label_font = font.Font(family="Arial", size=16)
        self.button_font = font.Font(family="Arial", size=14, weight="bold")
        self.entry_font = font.Font(family="Arial", size=14)
        self.checkbox_font = font.Font(family="Arial", size=12)
        
        self.create_widgets()
        
    def create_widgets(self):
        title_frame = tk.Frame(self.root, bg="#F6DED8")
        title_frame.pack(pady=30)
        
        title_label = tk.Label(title_frame, text="Self Help Group Management System", 
                               font=self.title_font, bg="#F6DED8", fg="#D2665A")
        title_label.pack()
        
        main_frame = tk.Frame(self.root, bg="#F6DED8")
        main_frame.pack(pady=20)
        
        choice_frame = tk.Frame(main_frame, bg="#F6DED8")
        choice_frame.pack(pady=20)
        
        login_label = tk.Label(choice_frame, text="Select Login Type:", 
                               font=self.label_font, bg="#F6DED8", fg="#D2665A")
        login_label.pack(pady=10)
        
        self.admin_btn = tk.Button(choice_frame, text="Admin Login", 
                                   font=self.button_font, bg="#D2665A", fg="white",
                                   width=20, height=2, command=self.open_admin_login_window)
        self.admin_btn.pack(pady=10)
        
        self.member_btn = tk.Button(choice_frame, text="Member Login", 
                                    font=self.button_font, bg="#D2665A", fg="white",
                                    width=20, height=2, command=self.open_member_login_window)
        self.member_btn.pack(pady=10)
        
    def open_admin_login_window(self):
        admin_window = tk.Toplevel(self.root)
        admin_window.title("Admin Login")
        admin_window.geometry("500x400")
        admin_window.configure(bg="#F6DED8")

        window_width = 500
        window_height = 400
        screen_width = admin_window.winfo_screenwidth()
        screen_height = admin_window.winfo_screenheight()
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        admin_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        login_title = tk.Label(admin_window, text="Admin Login", 
                               font=self.title_font, bg="#F6DED8", fg="#D2665A")
        login_title.pack(pady=20)
        
        form_frame = tk.Frame(admin_window, bg="#F6DED8")
        form_frame.pack(pady=20)
        
        username_label = tk.Label(form_frame, text="Username:", 
                                  font=self.label_font, bg="#F6DED8", fg="#D2665A")
        username_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        
        username_entry = tk.Entry(form_frame, font=self.entry_font, width=25)
        username_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        password_label = tk.Label(form_frame, text="Password:", 
                                  font=self.label_font, bg="#F6DED8", fg="#D2665A")
        password_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        
        password_entry = tk.Entry(form_frame, font=self.entry_font, show="*", width=25)
        password_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        
        show_password_var = tk.BooleanVar()
        show_password_var.set(False)
        
        def toggle_password():
            if show_password_var.get():
                password_entry.config(show="")
            else:
                password_entry.config(show="*")
        
        show_password_check = tk.Checkbutton(form_frame, text="Show Password", 
                                             variable=show_password_var, 
                                             onvalue=True, offvalue=False,
                                             font=self.checkbox_font,
                                             bg="#F6DED8", fg="#D2665A",
                                             selectcolor="#F6DED8",
                                             command=toggle_password)
        show_password_check.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        def admin_login():
            username = username_entry.get()
            password = password_entry.get()
            
            if username == self.admin_username and password == self.admin_password:
                messagebox.showinfo("Login Successful", "Welcome Admin!")
                admin_window.destroy()
                subprocess.Popen(["python", "dash.py"])
                
            else:
                messagebox.showerror("Login Failed", "Invalid admin credentials")
        
        login_button = tk.Button(admin_window, text="Login", 
                                 font=self.button_font, bg="#D2665A", fg="white",
                                 width=15, command=admin_login)
        login_button.pack(pady=20)
        
        close_button = tk.Button(admin_window, text="Cancel", 
                                 font=self.button_font, bg="#D2665A", fg="white",
                                 width=15, command=admin_window.destroy)
        close_button.pack(pady=10)
        
    def open_member_login_window(self):
        member_window = tk.Toplevel(self.root)
        member_window.title("Member Login")
        member_window.geometry("500x400")
        member_window.configure(bg="#F6DED8")

        window_width = 500
        window_height = 400
        screen_width = member_window.winfo_screenwidth()
        screen_height = member_window.winfo_screenheight()
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        member_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        login_title = tk.Label(member_window, text="Member Login", 
                               font=self.title_font, bg="#F6DED8", fg="#D2665A")
        login_title.pack(pady=20)
        
        form_frame = tk.Frame(member_window, bg="#F6DED8")
        form_frame.pack(pady=20)
        
        username_label = tk.Label(form_frame, text="Username:", 
                                  font=self.label_font, bg="#F6DED8", fg="#D2665A")
        username_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        
        username_entry = tk.Entry(form_frame, font=self.entry_font, width=25)
        username_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        password_label = tk.Label(form_frame, text="Password:", 
                                  font=self.label_font, bg="#F6DED8", fg="#D2665A")
        password_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        
        password_entry = tk.Entry(form_frame, font=self.entry_font, show="*", width=25)
        password_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        
        show_password_var = tk.BooleanVar()
        show_password_var.set(False)
        
        def toggle_password():
            if show_password_var.get():
                password_entry.config(show="")
            else:
                password_entry.config(show="*")
        
        show_password_check = tk.Checkbutton(form_frame, text="Show Password", 
                                             variable=show_password_var, 
                                             onvalue=True, offvalue=False,
                                             font=self.checkbox_font,
                                             bg="#F6DED8", fg="#D2665A",
                                             selectcolor="#F6DED8",
                                             command=toggle_password)
        show_password_check.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        def member_login():
            username = username_entry.get()
            password = password_entry.get()
            
            if username == self.member_username and password == self.member_password:
                messagebox.showinfo("Login Successful", f"Welcome {username}!")
                member_window.destroy()
                # You can add member dashboard opening code here
                subprocess.Popen(["python", "member.py"])
            else:
                messagebox.showerror("Login Failed", "Invalid member credentials")
        
        login_button = tk.Button(member_window, text="Login", 
                                 font=self.button_font, bg="#D2665A", fg="white",
                                 width=15, command=member_login)
        login_button.pack(pady=20)
        
        close_button = tk.Button(member_window, text="Cancel", 
                                 font=self.button_font, bg="#D2665A", fg="white",
                                 width=15, command=member_window.destroy)
        close_button.pack(pady=10)
        
    def open_admin_dashboard(self, username):
        try:
            import dash
            dashboard_root = tk.Toplevel(self.root)
            dashboard_root.protocol("WM_DELETE_WINDOW", lambda: self.on_dashboard_close(dashboard_root))
            dash.Dashboard(dashboard_root, username)
        except ImportError:
            messagebox.showerror("Error", "dash.py module not found!")

    def on_dashboard_close(self, dashboard_window):
        dashboard_window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginSystem(root)
    root.mainloop()