import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.font import Font
from PIL import Image, ImageTk
import os

class Dashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Self Help Group Management System - Dashboard")
        self.root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))
        self.root.configure(bg="#F6DED8")  # Background color
        
        # Colors
        self.bg_color = "#F6DED8"
        self.fg_color = "#D2665A"
        self.hover_color = "#E89A8D"
        self.active_color = "#B84A3A"
        
        # Fonts
        self.title_font = Font(family="Arial", size=24, weight="bold")
        self.section_font = Font(family="Arial", size=14, weight="bold")
        self.button_font = Font(family="Arial", size=12)
        
        # Create main container
        self.create_main_container()
        
        # Load icons
        self.load_icons()
        
        # Create dashboard sections
        self.create_header()
        self.create_navigation()
        self.create_main_content()
        
    def create_main_container(self):
        self.main_container = tk.Frame(self.root, bg=self.bg_color)
        self.main_container.pack(fill="both", expand=True)
        
    def load_icons(self):
        """Create proper image icons with text"""
        icon_size = (64, 64)
        icon_bg = (246, 222, 216)  # RGB for #F6DED8
        
        # Dictionary of icons with their Unicode characters
        icon_chars = {
            "users": "👥",
            "complaints": "📝",
            "staff": "👨‍💼",
            "member": "👤",
            "events": "📅",
            "contributions": "💰",
            "loanpayment": "🏦",
            "bankinfo": "🏛️",
            "loanrepayment": "💵"
        }
        
        self.icons = {}
        
        # Try to load image icons
        try:
            for key, char in icon_chars.items():
                # Create image with white background
                img = Image.new('RGB', icon_size, color=icon_bg)
                draw = ImageDraw.Draw(img)
                
                # Use a font that supports these characters
                try:
                    font = ImageFont.truetype("arial.ttf", 32)
                except:
                    font = ImageFont.load_default()
                
                # Calculate text position (centered)
                text_width, text_height = draw.textsize(char, font=font)
                position = ((icon_size[0] - text_width) // 2, (icon_size[1] - text_height) // 2)
                
                # Draw the text
                draw.text(position, char, font=font, fill=(0, 0, 0))  # Black text
                
                # Convert to PhotoImage
                self.icons[key] = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error creating icons: {e}")
            # Fallback to Unicode characters if image creation fails
            self.icons = icon_chars
    
    def create_header(self):
        header_frame = tk.Frame(self.main_container, bg=self.fg_color)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = tk.Label(header_frame, text="Self Help Group Management System", 
                             font=self.title_font, fg="white", bg=self.fg_color)
        title_label.pack(side="left", padx=20, pady=10)
        
        user_label = tk.Label(header_frame, text="Admin: selfhelpgroup", 
                            font=self.button_font, fg="white", bg=self.fg_color)
        user_label.pack(side="right", padx=20, pady=10)
        
    def create_navigation(self):
        nav_frame = tk.Frame(self.main_container, bg=self.bg_color)
        nav_frame.pack(fill="x", padx=10, pady=5)
        
        # Navigation buttons
        buttons = [
            ("Dashboard", self.show_dashboard),
            ("Users", self.show_users),
            ("Loan Applications", self.show_complaints),
            ("Staff", self.show_staff),
            ("Events", self.show_events),
            ("Contributions", self.show_contributions),
            ("Loan Approvals", self.show_loanpayments),
            ("Loan Repayments", self.show_loanrepayments),
            ("Bank Info", self.show_bankinfo),
            ("Logout", self.logout)
        ]
        
        for text, command in buttons:
            btn = tk.Button(nav_frame, text=text, command=command, 
                          font=self.button_font, bg=self.fg_color, fg="white",
                          activebackground=self.active_color, activeforeground="white",
                          relief="flat", bd=0, padx=15, pady=8)
            btn.pack(side="left", padx=5)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.hover_color))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.fg_color))
    
    def create_main_content(self):
        self.content_frame = tk.Frame(self.main_container, bg=self.bg_color)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create dashboard sections
        self.create_dashboard_sections()
        
    def create_dashboard_sections(self):
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Create a grid of sections
        sections = [
            ("Users", "users", self.show_users),
            ("Loan Applications", "complaints", self.show_complaints),
            ("Staff", "staff", self.show_staff),
            ("Events", "events", self.show_events),
            ("Contributions", "contributions", self.show_contributions),
            ("Loan Approvals", "loanpayment", self.show_loanpayments),
            ("Loan Repayments", "loanrepayment", self.show_loanrepayments),
            ("Bank Info", "bankinfo", self.show_bankinfo)
        ]
        
        # Calculate grid layout
        cols = 4
        rows = (len(sections) + cols - 1) // cols
        
        for i, (title, icon_key, command) in enumerate(sections):
            row = i // cols
            col = i % cols
            
            section_frame = tk.Frame(self.content_frame, bg="white", bd=2, relief="groove")
            section_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            section_frame.bind("<Button-1>", lambda e, c=command: c())
            
            # Icon
            if isinstance(self.icons.get(icon_key), str):
                icon_label = tk.Label(section_frame, text=self.icons[icon_key], 
                                   font=("Arial", 32), bg="white")
            else:
                icon_label = tk.Label(section_frame, image=self.icons[icon_key], 
                                   bg="white")
            icon_label.pack(pady=(15, 5))
            
            # Title
            title_label = tk.Label(section_frame, text=title, 
                                  font=self.section_font, bg="white")
            title_label.pack(pady=(0, 15))
            
            # Configure grid weights
            self.content_frame.grid_columnconfigure(col, weight=1)
            self.content_frame.grid_rowconfigure(row, weight=1)
    
    # Section display methods
    def show_dashboard(self):
        self.create_dashboard_sections()
   
    def show_users(self):
        self.clear_content()
    
        try:
            # Get the directory of the current script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            user_script = os.path.join(script_dir, "user.py")
        
            # Check if user.py exists
            if not os.path.exists(user_script):
                raise FileNotFoundError("user.py not found in the same directory")
        
            # Clear current content
            for widget in self.content_frame.winfo_children():
                widget.destroy()
            
            # Import the UserManagement class from user.py
            from user import UserManagement
        
            # Create an instance of UserManagement in the content frame
            user_mgmt = UserManagement(self.content_frame, self.bg_color, self.fg_color)
        
        except Exception as e:
            # Fallback to simple label if user.py can't be loaded
            error_label = tk.Label(self.content_frame, 
                                text=f"Failed to load user module: {str(e)}",
                                font=self.section_font, 
                                bg=self.bg_color,
                                fg="red")
            error_label.pack(pady=20)
     
    def show_complaints(self):
        self.clear_content()
        
        try:
            # Get the directory of the current script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            user_script = os.path.join(script_dir, "loanapplication.py")
        
            # Check if user.py exists
            if not os.path.exists(user_script):
                raise FileNotFoundError("loanapplication.py not found in the same directory")
        
            # Clear current content
            for widget in self.content_frame.winfo_children():
                widget.destroy()
            
            # Import the UserManagement class from user.py
            from loanapplication import LoanManagementSystem
        
            # Create an instance of UserManagement in the content frame
            staf_mgmt = LoanManagementSystem(self.content_frame, self.bg_color, self.fg_color)
        
        except Exception as e:
            # Fallback to simple label if user.py can't be loaded
            error_label = tk.Label(self.content_frame, 
                                text=f"Failed to load loanapplication module: {str(e)}",
                                font=self.section_font, 
                                bg=self.bg_color,
                                fg="red")
            error_label.pack(pady=20)
        
    def show_staff(self):
        self.clear_content()
        
        try:
            # Get the directory of the current script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            user_script = os.path.join(script_dir, "staff.py")
        
            # Check if user.py exists
            if not os.path.exists(user_script):
                raise FileNotFoundError("staff.py not found in the same directory")
        
            # Clear current content
            for widget in self.content_frame.winfo_children():
                widget.destroy()
            
            # Import the UserManagement class from user.py
            from staff import StaffManagement
        
            # Create an instance of UserManagement in the content frame
            staf_mgmt = StaffManagement(self.content_frame, self.bg_color, self.fg_color)
        
        except Exception as e:
            # Fallback to simple label if user.py can't be loaded
            error_label = tk.Label(self.content_frame, 
                                text=f"Failed to load user module: {str(e)}",
                                font=self.section_font, 
                                bg=self.bg_color,
                                fg="red")
            error_label.pack(pady=20)
    
    def show_events(self):
        self.clear_content()
        
        try:
            # Get the directory of the current script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            user_script = os.path.join(script_dir, "event.py")
        
            # Check if user.py exists
            if not os.path.exists(user_script):
                raise FileNotFoundError("event.py not found in the same directory")
        
            # Clear current content
            for widget in self.content_frame.winfo_children():
                widget.destroy()
            
            # Import the UserManagement class from user.py
            from event import EventManagement
        
            # Create an instance of UserManagement in the content frame
            user_mgmt = EventManagement(self.content_frame, self.bg_color, self.fg_color)
        
        except Exception as e:
            # Fallback to simple label if user.py can't be loaded
            error_label = tk.Label(self.content_frame, 
                                text=f"Failed to load event module: {str(e)}",
                                font=self.section_font, 
                                bg=self.bg_color,
                                fg="red")
            error_label.pack(pady=20)
         
    def show_contributions(self):
        self.clear_content()
        
        try:
            # Get the directory of the current script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            user_script = os.path.join(script_dir, "contribution.py")
        
            # Check if user.py exists
            if not os.path.exists(user_script):
                raise FileNotFoundError("contribution.py not found in the same directory")
        
            # Clear current content
            for widget in self.content_frame.winfo_children():
                widget.destroy()
            
            # Import the UserManagement class from user.py
            from contribution import ContributionManagement
        
            # Create an instance of UserManagement in the content frame
            user_mgmt = ContributionManagement(self.content_frame, self.bg_color, self.fg_color)
        
        except Exception as e:
            # Fallback to simple label if user.py can't be loaded
            error_label = tk.Label(self.content_frame, 
                                text=f"Failed to load contibution module: {str(e)}",
                                font=self.section_font, 
                                bg=self.bg_color,
                                fg="red")
            error_label.pack(pady=20)
        
    def show_loanpayments(self):
        self.clear_content()
        
        try:
            # Get the directory of the current script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            user_script = os.path.join(script_dir, "loandemo.py")
        
            # Check if user.py exists
            if not os.path.exists(user_script):
                raise FileNotFoundError("loandemo not found in the same directory")
        
            # Clear current content
            for widget in self.content_frame.winfo_children():
                widget.destroy()
            
            # Import the UserManagement class from user.py
            from loandemo import LoanManagement 
        
            # Create an instance of UserManagement in the content frame
            loan_mgmt = LoanManagement(self.content_frame, self.bg_color, self.fg_color)
        
        except Exception as e:
            # Fallback to simple label if user.py can't be loaded
            error_label = tk.Label(self.content_frame, 
                                text=f"Failed to load loan module: {str(e)}",
                                font=self.section_font, 
                                bg=self.bg_color,
                                fg="red")
            error_label.pack(pady=20)
            
    def show_loanrepayments(self):
        self.clear_content()
        
        try:
            # Get the directory of the current script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            user_script = os.path.join(script_dir, "loanrepayment.py")
        
            # Check if loanrepayment.py exists
            if not os.path.exists(user_script):
                raise FileNotFoundError("loanrepayment.py not found in the same directory")
        
            # Clear current content
            for widget in self.content_frame.winfo_children():
                widget.destroy()
            
            # Import the LoanRepaymentSystem from loanrepayment.py
            from loanrepayment import LoanRepaymentSystem
        
            # Create an instance of LoanRepaymentSystem in the content frame
            # Pass only the required number of arguments (2 instead of 4)
            repayment_mgmt = LoanRepaymentSystem(self.content_frame)
        
        except Exception as e:
            # Fallback to simple label if loanrepayment.py can't be loaded
            error_label = tk.Label(self.content_frame, 
                                text=f"Failed to load loan repayment module: {str(e)}",
                                font=self.section_font, 
                                bg=self.bg_color,
                                fg="red")
            error_label.pack(pady=20)
        
    def show_bankinfo(self):
        self.clear_content()
        
        try:
            # Get the directory of the current script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            user_script = os.path.join(script_dir, "bank.py")
        
            # Check if user.py exists
            if not os.path.exists(user_script):
                raise FileNotFoundError("bank.py not found in the same directory")
        
            # Clear current content
            for widget in self.content_frame.winfo_children():
                widget.destroy()
            
            # Import the UserManagement class from user.py
            from bank import BankAccountManagement
        
            # Create an instance of UserManagement in the content frame
            user_mgmt = BankAccountManagement(self.content_frame, self.bg_color, self.fg_color)
        
        except Exception as e:
            # Fallback to simple label if user.py can't be loaded
            error_label = tk.Label(self.content_frame, 
                                text=f"Failed to load bank module: {str(e)}",
                                font=self.section_font, 
                                bg=self.bg_color,
                                fg="red")
            error_label.pack(pady=20)
        
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.root.destroy()
            subprocess.Popen(["python", "login.py"])
            # Here you would typically return to the login screen

if __name__ == "__main__":
    root = tk.Tk()
    app = Dashboard(root)
    root.mainloop()