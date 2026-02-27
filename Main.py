import os
import sys
import shutil
import subprocess
import platform


def _check_tkinter():
    """
    Verify tkinter is available. If missing, attempt automatic installation
    via brew (macOS) or sudo + system package manager (Linux), then re-check.
    """
    try:
        import tkinter
        return
    except ImportError:
        pass

    print("tkinter is not installed. Attempting automatic installation...")

    system = platform.system()
    install_ok = False

    if system == "Darwin":
        brew = shutil.which("brew")
        if not brew:
            print("Homebrew (brew) is not installed. It is required to install tkinter on macOS.")
            answer = input("Would you like to install Homebrew now? [y/N]: ").strip().lower()
            if answer != "y":
                print("Cannot install tkinter without Homebrew.")
                print("Please reinstall Python from https://www.python.org ensuring tkinter is included.")
                sys.exit(1)
            print("Installing Homebrew (this may take a few minutes and will require your password)...")
            result = subprocess.run(
                '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
                shell=True
            )
            if result.returncode != 0:
                print("Homebrew installation failed.")
                print("Please visit https://brew.sh to install it manually, then re-run this program.")
                sys.exit(1)
            for candidate in ["/opt/homebrew/bin/brew", "/usr/local/bin/brew"]:
                if os.path.exists(candidate):
                    brew = candidate
                    break
            if not brew:
                print("Homebrew was installed but 'brew' could not be found. Please restart your terminal and re-run.")
                sys.exit(1)
        version = f"{sys.version_info.major}.{sys.version_info.minor}"
        formula = f"python-tk@{version}"
        print(f"Running: {brew} install {formula}")
        result = subprocess.run([brew, "install", formula])
        install_ok = result.returncode == 0

    elif system == "Linux":
        distro_info = ""
        try:
            with open("/etc/os-release") as f:
                distro_info = f.read().lower()
        except OSError:
            pass

        if any(d in distro_info for d in ["ubuntu", "debian", "linuxmint", "pop"]):
            cmd = ["sudo", "apt", "install", "-y", "python3-tk"]
        elif any(d in distro_info for d in ["fedora", "rhel", "centos", "rocky", "alma"]):
            cmd = ["sudo", "dnf", "install", "-y", "python3-tkinter"]
        elif "arch" in distro_info:
            cmd = ["sudo", "pacman", "-S", "--noconfirm", "tk"]
        elif "suse" in distro_info:
            cmd = ["sudo", "zypper", "install", "-y", "python3-tk"]
        else:
            print("Unrecognised Linux distribution. Cannot auto-install tkinter.")
            print("Please install python3-tk using your distribution's package manager.")
            sys.exit(1)

        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        install_ok = result.returncode == 0

    elif system == "Windows":
        print("Error: tkinter is not installed.")
        print("Please reinstall Python from https://www.python.org")
        print("During installation, ensure the 'tcl/tk and IDLE' optional feature is checked.")
        sys.exit(1)

    else:
        print("Error: tkinter is not installed.")
        print("Please reinstall Python from https://www.python.org ensuring tkinter is included.")
        sys.exit(1)

    if install_ok:
        try:
            import tkinter
            print("tkinter installed successfully. Continuing...")
            return
        except ImportError:
            pass

    print("Error: tkinter installation did not succeed.")
    if system == "Darwin":
        print("Please reinstall Python from https://www.python.org ensuring tkinter is included.")
    else:
        print("Please install python3-tk manually using your distribution's package manager.")
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