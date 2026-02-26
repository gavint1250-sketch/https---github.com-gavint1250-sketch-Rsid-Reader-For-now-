
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import platform

def install_package(package, progress_text_widget):
    """Install a package using pip, providing feedback to the GUI."""
    progress_text_widget.insert(tk.END, f"Installing {package}...\n")
    progress_text_widget.update_idletasks()
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        progress_text_widget.insert(tk.END, f"{package} installed successfully.\n")
        return True
    except subprocess.CalledProcessError:
        progress_text_widget.insert(tk.END, f"Failed to install {package}. Please install it manually.\n")
        if platform.system() == "Darwin" and "arm" in platform.machine():
             progress_text_widget.insert(tk.END, "Note: On ARM Macs, some packages might require manual installation via 'pip3 install'.\n")
        return False

def check_and_install_dependencies():
    """Check for dependencies and install them if missing, using a GUI."""
    try:
        __import__("docx")
        __import__("customtkinter")
        return True
    except ImportError:
        pass

    installer_root = tk.Tk()
    installer_root.title("Checking Dependencies")
    installer_root.geometry("450x250")
    
    label = ttk.Label(installer_root, text="Please wait, checking and installing required libraries...", padding="10")
    label.pack()

    progress_text = tk.Text(installer_root, height=8, wrap=tk.WORD, state=tk.NORMAL)
    progress_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    dependencies = {
        "python-docx": "docx",
        "customtkinter": "customtkinter"
    }
    
    missing_dependencies = []
    for package, import_name in dependencies.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_dependencies.append(package)

    if not missing_dependencies:
        installer_root.destroy()
        return True

    def do_install():
        all_installed = True
        for package in missing_dependencies:
            if not install_package(package, progress_text):
                all_installed = False
        
        if all_installed:
            progress_text.insert(tk.END, "\nAll dependencies are ready. Launching application...")
            installer_root.after(2000, installer_root.destroy)
        else:
            progress_text.insert(tk.END, "\nCould not install all dependencies. Please see the messages above and install manually.")

    installer_root.after(100, do_install)
    installer_root.mainloop()
    
    try:
        __import__("docx")
        __import__("customtkinter")
        return True
    except ImportError:
        # Show a final error if dependencies are still missing
        error_root = tk.Tk()
        error_root.withdraw() # Hide root window
        messagebox.showerror("Startup Error", "Could not start the application due to missing dependencies.\nPlease check the installation messages and install them manually.")
        error_root.destroy()
        return False
