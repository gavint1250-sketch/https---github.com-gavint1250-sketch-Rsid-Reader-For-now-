
import os
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
        # Retry with --break-system-packages for externally-managed Python environments (e.g. Homebrew)
        if platform.system() != "Windows":
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                progress_text_widget.insert(tk.END, f"{package} installed successfully.\n")
                return True
            except subprocess.CalledProcessError:
                pass
        progress_text_widget.insert(tk.END, f"Failed to install {package}. Please install it manually.\n")
        return False


def get_import_name(package_name):
    """Get the import name from the package name."""
    # This is a simple mapping, for more complex cases a more robust solution is needed
    if "python-docx" in package_name:
        return "docx"
    if "Pillow" in package_name:
        return "PIL"
    # For many packages, the import name is the same as the package name (or similar)
    return package_name.split("==")[0].replace("-", "_")

def check_and_install_dependencies():
    """Check for dependencies from requirements.txt and install them if missing, using a GUI."""
    
    _here = os.path.dirname(os.path.abspath(__file__))
    req_path = os.path.join(_here, "..", "requirements.txt")
    try:
        with open(req_path) as f:
            required_packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        _err_root = tk.Tk()
        _err_root.withdraw()
        messagebox.showerror("Error", "requirements.txt not found.")
        _err_root.destroy()
        return False

    missing_dependencies = []
    for package in required_packages:
        import_name = get_import_name(package)
        try:
            __import__(import_name)
        except ImportError:
            missing_dependencies.append(package)

    if not missing_dependencies:
        return True

    installer_root = tk.Tk()
    installer_root.title("Checking Dependencies")
    installer_root.geometry("450x250")
    
    label = ttk.Label(installer_root, text="Please wait, checking and installing required libraries...", padding="10")
    label.pack()

    progress_text = tk.Text(installer_root, height=8, wrap=tk.WORD, state=tk.NORMAL)
    progress_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
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
    
    # Final check to see if dependencies were actually installed
    for package in missing_dependencies:
        import_name = get_import_name(package)
        try:
            __import__(import_name)
        except ImportError:
            error_root = tk.Tk()
            error_root.withdraw()
            messagebox.showerror("Startup Error", "Could not start the application due to missing dependencies.\nPlease check the installation messages and install them manually.")
            error_root.destroy()
            return False
            
    return True

