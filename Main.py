
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog
import platform

# This section should install dependencies. (Update as more are added/Taken away) 
# It should also run a check for dependencies and if they are already installed, it should skip installation.

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
        return False


# --- Main Application ---

def launch_main_app():
    """The main application logic."""
    from Scraper import detect_ai_and_rsid
    import customtkinter

    customtkinter.set_appearance_mode("System")
    customtkinter.set_default_color_theme("blue")


    def browse_file():
        filepath = filedialog.askopenfilename(
            title="Select a .docx or .xml file",
            filetypes=(("Word Documents", "*.docx"), ("XML Files", "*.xml"), ("All files", "*.*"))
        )
        if not filepath:
            return

        results = detect_ai_and_rsid(filepath)
        
        result_text.configure(state="normal")
        result_text.delete("1.0", "end")
        for result in results:
            result_text.insert("end", result + "\n")
        result_text.configure(state="disabled")
        
        label_file.configure(text=f"Analyzed: {os.path.basename(filepath)}")

    # --- GUI Setup ---
    app = customtkinter.CTk()
    app.title("AI Characteristic & RSID Detector")
    app.geometry("700x550")

    app.grid_columnconfigure(0, weight=1)
    app.grid_rowconfigure(1, weight=1)

    frame_top = customtkinter.CTkFrame(app)
    frame_top.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
    frame_top.grid_columnconfigure(0, weight=1)

    browse_button = customtkinter.CTkButton(frame_top, text="Browse for .docx or .xml File", command=browse_file)
    browse_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

    label_file = customtkinter.CTkLabel(frame_top, text="No file selected", text_color="gray")
    label_file.grid(row=1, column=0, padx=10, pady=(0, 10))

    result_text = customtkinter.CTkTextbox(app, wrap="word", state="disabled")
    result_text.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
    
    app.mainloop()

if __name__ == "__main__":
    if check_and_install_dependencies():
        launch_main_app()
    else:
        error_root = tk.Tk()
        error_root.withdraw() # Hide root window
        messagebox.showerror("Startup Error", "Could not start the application due to missing dependencies.\nPlease check the installation messages and install them manually.")
        error_root.destroy()
