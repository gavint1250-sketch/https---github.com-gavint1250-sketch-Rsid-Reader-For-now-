
import customtkinter
import os
from tkinter import filedialog
from modules.file_analyzer import analyze_file

def create_and_run_gui():
    """Creates and runs the main GUI for the application."""

    customtkinter.set_appearance_mode("System")
    customtkinter.set_default_color_theme("blue")

    def browse_file():
        filepath = filedialog.askopenfilename(
            title="Select a .docx or .xml file",
            filetypes=(("Word Documents", "*.docx"), ("XML Files", "*.xml"), ("All files", "*.*"))
        )
        if not filepath:
            return

        results = analyze_file(filepath)
        
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
