
import os
import pathlib
import platform
import webbrowser
import ctypes
import customtkinter
from tkinter import filedialog, messagebox
from modules.file_analyzer import analyze_file


# Maps line prefixes to color tag names
_PREFIX_TO_TAG = {
    "[KEYWORD]":   "keyword",
    "[SCRAPE]":    "scrape",
    "[APP]":       "app",
    "[RSID]":      "rsid",
    "[TIMESTAMP]": "timestamp",
    "[REVISION]":  "revision",
    "[AUTHOR]":    "author",
    "[CONTENT]":   "content",
    "[TRACK]":     "track",
    "[COMMENT]":   "comment",
    "[FORMAT]":    "format",
    "[GDOCS]":      "gdocs",
    "[PERPLEXITY]": "perplexity",
    "[BURST]":      "burst",
}


def _get_tag(line):
    """Return the color tag name for a result line, or None for plain text."""
    stripped = line.strip()
    if stripped.startswith("---") or stripped.startswith("==="):
        return "header"
    for prefix, tag in _PREFIX_TO_TAG.items():
        if stripped.startswith(prefix):
            return tag
    return None


def create_and_run_gui():
    """Creates and runs the main GUI for the application."""

    if platform.system() == "Windows":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass

    customtkinter.set_appearance_mode("System")
    customtkinter.set_default_color_theme("blue")

    app = customtkinter.CTk()
    app.title("AI Characteristic & RSID Detector")
    app.geometry("700x600")

    app.grid_columnconfigure(0, weight=1)
    app.grid_rowconfigure(1, weight=1)

    # --- Top control frame ---
    frame_top = customtkinter.CTkFrame(app)
    frame_top.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
    frame_top.grid_columnconfigure(0, weight=1)
    frame_top.grid_columnconfigure(1, weight=1)

    # Tracks the last set of result strings (used by save + clipboard)
    current_results = []

    # Paragraph-level AI scores from the most recent .docx analysis.
    # Each entry: {'filename': str, 'scores': list[dict]}
    _report_data = []

    # --- Helper: render results into the text area with color tags ---
    def _display_results(results):
        result_text.configure(state="normal")
        result_text.delete("1.0", "end")
        for line in results:
            tag = _get_tag(line)
            if tag:
                result_text.insert("end", line + "\n", tag)
            else:
                result_text.insert("end", line + "\n")
        result_text.configure(state="disabled")

    # --- Browse single file ---
    def browse_file():
        filepath = filedialog.askopenfilename(
            title="Select a .docx, .pdf, or .xml file",
            filetypes=(("Supported Files", "*.docx *.pdf *.xml"), ("Word Documents", "*.docx"), ("PDF Files", "*.pdf"), ("XML Files", "*.xml"), ("All files", "*.*"))
        )
        if not filepath:
            return
        results = analyze_file(filepath)
        current_results.clear()
        current_results.extend(results)
        _display_results(current_results)
        label_file.configure(text=f"Analyzed: {os.path.basename(filepath)}")

        # Collect per-paragraph scores for the HTML report (docx only)
        _report_data.clear()
        if filepath.lower().endswith('.docx'):
            try:
                from modules.content.perplexity_checker import get_cached_paragraph_scores
                _report_data.append({
                    'filename': os.path.basename(filepath),
                    'scores': get_cached_paragraph_scores(),
                })
            except Exception:
                pass

    # --- Browse folder (batch) ---
    def browse_folder():
        folder = filedialog.askdirectory(title="Select Folder Containing .docx Files")
        if not folder:
            return
        supported_files = sorted(
            f for f in os.listdir(folder)
            if f.lower().endswith('.docx') or f.lower().endswith('.pdf')
        )
        if not supported_files:
            current_results.clear()
            current_results.append("No .docx or .pdf files found in the selected folder.")
            _display_results(current_results)
            label_file.configure(text="No files found.")
            return
        combined = []
        _report_data.clear()
        for fname in supported_files:
            sep = "=" * 60
            combined.append(sep)
            combined.append(f"=== FILE: {fname} ===")
            combined.append(sep)
            combined.extend(analyze_file(os.path.join(folder, fname)))
            combined.append("")
            # Collect per-paragraph scores for HTML report (docx only)
            if fname.lower().endswith('.docx'):
                try:
                    from modules.content.perplexity_checker import get_cached_paragraph_scores
                    _report_data.append({
                        'filename': fname,
                        'scores': get_cached_paragraph_scores(),
                    })
                except Exception:
                    pass
        current_results.clear()
        current_results.extend(combined)
        _display_results(current_results)
        label_file.configure(text=f"Analyzed {len(supported_files)} file(s) from folder.")

    # --- Save report ---
    def save_report():
        if not current_results:
            return
        filepath = filedialog.asksaveasfilename(
            title="Save Report",
            defaultextension=".txt",
            filetypes=(("Text Files", "*.txt"), ("All files", "*.*"))
        )
        if not filepath:
            return
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(current_results))

    # --- Download AI Report ---
    def download_report():
        if not _report_data:
            messagebox.showinfo(
                "No Report Data",
                "Please analyse a .docx file first to generate an AI report.",
            )
            return
        filepath = filedialog.asksaveasfilename(
            title="Save AI Analysis Report",
            defaultextension=".html",
            filetypes=(("HTML Report", "*.html"), ("All files", "*.*")),
        )
        if not filepath:
            return
        from modules.report_generator import generate_html_report
        html_content = generate_html_report(_report_data)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        webbrowser.open(pathlib.Path(filepath).as_uri())

    # --- Copy to clipboard ---
    def copy_to_clipboard():
        if not current_results:
            return
        app.clipboard_clear()
        app.clipboard_append("\n".join(current_results))

    # --- Buttons (2 x 2 grid) ---
    browse_button = customtkinter.CTkButton(
        frame_top, text="Browse File (.docx / .pdf / .xml)", command=browse_file
    )
    browse_button.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")

    batch_button = customtkinter.CTkButton(
        frame_top, text="Browse Folder (Batch)", command=browse_folder
    )
    batch_button.grid(row=0, column=1, padx=10, pady=(10, 5), sticky="ew")

    save_button = customtkinter.CTkButton(
        frame_top, text="Save Report", command=save_report
    )
    save_button.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="ew")

    clipboard_button = customtkinter.CTkButton(
        frame_top, text="Copy to Clipboard", command=copy_to_clipboard
    )
    clipboard_button.grid(row=1, column=1, padx=10, pady=(5, 5), sticky="ew")

    report_button = customtkinter.CTkButton(
        frame_top, text="Download AI Report (.html)", command=download_report
    )
    report_button.grid(row=2, column=0, columnspan=2, padx=10, pady=(5, 10), sticky="ew")

    label_file = customtkinter.CTkLabel(frame_top, text="No file selected", text_color="gray")
    label_file.grid(row=3, column=0, columnspan=2, padx=10, pady=(0, 10))

    # --- Results text area ---
    result_text = customtkinter.CTkTextbox(app, wrap="word", state="disabled")
    result_text.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

    # --- Color tags ---
    result_text.tag_config("header",    foreground="#888888")
    result_text.tag_config("keyword",   foreground="#FFA500")
    result_text.tag_config("scrape",    foreground="#FF6B6B")
    result_text.tag_config("app",       foreground="#87CEEB")
    result_text.tag_config("rsid",      foreground="#6495ED")
    result_text.tag_config("timestamp", foreground="#B0B0B0")
    result_text.tag_config("revision",  foreground="#DA70D6")
    result_text.tag_config("author",    foreground="#48D1CC")
    result_text.tag_config("content",   foreground="#237B35")
    result_text.tag_config("track",     foreground="#FFD700")
    result_text.tag_config("comment",   foreground="#DDA0DD")
    result_text.tag_config("format",    foreground="#5FA8F2")
    result_text.tag_config("gdocs",      foreground="#4285F4")
    result_text.tag_config("perplexity", foreground="#9B59B6")
    result_text.tag_config("burst",      foreground="#1ABC9C")

    app.mainloop()
