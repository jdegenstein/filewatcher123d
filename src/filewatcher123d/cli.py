import sys
import os
import atexit
import subprocess
import time
import threading
import argparse
import glob
from jupyter_client import KernelManager
from jupyter_client import BlockingKernelClient


def interactive_file_prompt():
    print("No file specified.")
    py_files = glob.glob("*.py")

    if py_files:
        print("Found the following Python files in the current directory:")
        for i, f in enumerate(py_files):
            print(f"  [{i+1}] {f}")
        print(f"  [{len(py_files)+1}] Create a new file")
    else:
        print("No .py files found in the current directory.")

    while True:
        print("-" * 40)
        choice = input(
            "Select a number, or type a file path directly [default: main.py]: "
        ).strip()

        if not choice:
            choice = "main.py"

        # 1. Handle Menu Selection
        if choice.isdigit() and py_files:
            idx = int(choice) - 1
            if 0 <= idx < len(py_files):
                return os.path.abspath(py_files[idx])
            elif idx == len(py_files):
                choice = input("Enter new filename: ").strip()
                if not choice:
                    choice = "main.py"
                if not choice.endswith(".py"):
                    choice += ".py"

        # 2. Path canonicalization (handles ~ and converts to absolute path)
        choice = os.path.expanduser(choice)
        abs_path = os.path.abspath(choice)

        # 3. File validation and creation
        if not os.path.exists(abs_path):
            create = (
                input(
                    f"Warning: '{abs_path}' does not exist. Create it with a template? [Y/n]: "
                )
                .strip()
                .lower()
            )
            if create in ["", "y", "yes"]:

                # Ensure the parent directories exist before trying to create the file
                parent_dir = os.path.dirname(abs_path)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)

                with open(abs_path, "w") as f:
                    f.write(
                        "from build123d import *\nfrom ocp_vscode import *\n\nset_port(3939)\n\nshow(Box(1,1,1))\n"
                    )
                print(f"Created {abs_path}.")
                return abs_path
            else:
                print("Please select an existing file or provide a valid path.")
                continue

        return abs_path


def _filter_and_print_output(process, suppress_list):
    """
    A function to run in a thread.
    It reads output from a process line by line, filters it,
    and prints the lines that are *not* noisy.
    """
    try:
        for line in iter(process.stdout.readline, ""):
            # We still strip whitespace so the startswith check is reliable
            line_strip = line.strip()

            is_noisy = any(line_strip.startswith(s) for s in suppress_list)
            if line_strip and not is_noisy:
                print(f"[ocp_vscode] {line_strip}")

    except Exception as e:
        print(f"[Launcher] ocp_vscode filter thread error: {e}")
    finally:
        process.stdout.close()


def main():
    """
    Starts an IPython kernel, a watchdog monitor, ocp_vscode,
    and a jupyter console.
    """
    # Set up argparse for cleaner CLI flag handling and automatic --help output
    parser = argparse.ArgumentParser(
        description="""
A tool to watch a file and run it in a persistent, auto-reloading IPython kernel with ocp_vscode.
You can use %r from the running console to force re-execution of the watched script.
"""
    )
    parser.add_argument(
        "-a",
        "--autoreload",
        action="store_true",
        help="Enable the IPython autoreload extension to reload imported modules.",
    )

    # Change file_to_watch to be optional
    parser.add_argument(
        "file_to_watch",
        nargs="?",
        help="The path to the Python file you want to watch and execute.",
    )

    args = parser.parse_args()
    use_autoreload = args.autoreload

    # Trigger the interactive prompt if omitted
    if not args.file_to_watch:
        file_to_watch = interactive_file_prompt()
    else:
        file_to_watch = os.path.abspath(os.path.expanduser(args.file_to_watch))

    if use_autoreload:
        print("[Launcher] Autoreload mode enabled.")

    if not os.path.exists(file_to_watch):
        print(f"Error: File not found: {file_to_watch}")
        sys.exit(1)

    # 1. Start the IPython kernel
    print("[Launcher] Starting IPython kernel...")
    km = KernelManager()
    km.start_kernel()
    connection_file = km.connection_file
    print(f"[Launcher] Kernel started. Connection file: {connection_file}")
    atexit.register(km.shutdown_kernel, now=True)

    # 2. Start the watchdog monitor in a separate process
    monitor_cmd = [
        sys.executable,
        "-m",
        "filewatcher123d.monitor",
        file_to_watch,
        connection_file,
    ]
    # -------------------------------

    print("[Launcher] Starting monitor process...")
    monitor_process = subprocess.Popen(monitor_cmd)
    atexit.register(monitor_process.terminate)

    # 3. Start ocp_vscode and its filter
    print("[Launcher] Starting ocp_vscode...")

    OCP_NOISY_STRINGS = ["DEBUG:", "INFO: [ocp_vscode]", "127.0.0.1 - -"]

    ocp_cmd = [sys.executable, "-u", "-m", "ocp_vscode"]

    ocp_process = subprocess.Popen(
        ocp_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
    atexit.register(ocp_process.terminate)

    filter_thread = threading.Thread(
        target=_filter_and_print_output,
        args=(ocp_process, OCP_NOISY_STRINGS),
        daemon=True,
    )
    filter_thread.start()
    print("[Launcher] ocp_vscode filter thread started.")

    # 4. Inject setup commands (custom magics and optionally autoreload)
    try:
        # Connect a client to inject setup commands
        kc = BlockingKernelClient()
        kc.load_connection_file(connection_file)
        kc.start_channels()

        print("[Launcher] Injecting setup commands...")

        # Inject the %r magic command
        magic_injection_code = f"""
from IPython.core.magic import register_line_magic
from IPython import get_ipython

@register_line_magic
def r(line):
    print('\\n[Manual Run] Executing "{file_to_watch}"...')
    get_ipython().run_line_magic('run', '"{file_to_watch}"')
"""
        kc.execute(magic_injection_code)
        kc.get_shell_msg(timeout=5)  # Wait for reply

        if use_autoreload:
            # Send %load_ext autoreload
            kc.execute("%load_ext autoreload")
            kc.get_shell_msg(timeout=5)  # Wait for reply

            # Send %autoreload 2
            kc.execute("%autoreload 2")
            kc.get_shell_msg(timeout=5)  # Wait for reply

            # Send a confirmation message to the user's console
            kc.execute("print('[Launcher] Autoreload extension loaded.')")
            kc.get_shell_msg(timeout=5)

        kc.stop_channels()
        print(
            "[Launcher] Setup complete. You can use `%r` in the console to force re-run."
        )

    except Exception as e:
        print(f"[Launcher] Error injecting setup commands: {e}")

    # 5. Give the monitor a moment to connect
    time.sleep(0.5)

    # 6. Start the jupyter console (REPL) as the main process
    console_cmd = [
        sys.executable,
        "-m",
        "jupyter_console",
        "--existing",
        connection_file,
    ]

    print(f"[Launcher] Handing over to Jupyter console. (File: {file_to_watch})")
    print("---------------------------------------------------------------")

    subprocess.run(console_cmd)

    print("\n---------------------------------------------------------------")
    print("[Launcher] Console exited. Shutting down all processes...")


if __name__ == "__main__":
    main()
