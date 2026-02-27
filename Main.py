from modules.dependency_checker import check_and_install_dependencies

def main():
    """
    Main entry point for the application.
    Checks dependencies and launches the GUI.
    """
    if check_and_install_dependencies():
        from gui.main_window import create_and_run_gui
        create_and_run_gui()

if __name__ == "__main__":
    main()