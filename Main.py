import sys
import platform
import importlib.util


def _check_tkinter():
    """
    Verify tkinter is available before any other imports load it.
    On Linux it is not bundled with Python and must be installed via
    the system package manager (pip cannot install it).
    """
    if importlib.util.find_spec("tkinter") is None:
        print("Error: tkinter is not installed.")
        if platform.system() == "Linux":
            distro_info = ""
            try:
                with open("/etc/os-release") as f:
                    distro_info = f.read().lower()
            except OSError:
                pass

            if any(d in distro_info for d in ["ubuntu", "debian", "linuxmint", "pop"]):
                cmd = "sudo apt install python3-tk"
            elif any(d in distro_info for d in ["fedora", "rhel", "centos", "rocky", "alma"]):
                cmd = "sudo dnf install python3-tkinter"
            elif "arch" in distro_info:
                cmd = "sudo pacman -S tk"
            elif "suse" in distro_info:
                cmd = "sudo zypper install python3-tk"
            else:
                cmd = None

            if cmd:
                print(f"To install: {cmd}")
            else:
                print("Please install python3-tk using your distribution's package manager.")
                print("  Ubuntu/Debian: sudo apt install python3-tk")
                print("  Fedora/RHEL:   sudo dnf install python3-tkinter")
                print("  Arch:          sudo pacman -S tk")
                print("  openSUSE:      sudo zypper install python3-tk")
        else:
            print("Please reinstall Python and ensure tkinter is included.")
        sys.exit(1)


_check_tkinter()

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