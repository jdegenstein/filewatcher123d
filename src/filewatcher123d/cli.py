import sys
import os
import atexit
import subprocess
import time
import threading
from jupyter_client import KernelManager


def _filter_and_print_output(process, suppress_list):
    """
    A function to run in a thread.
    It reads output from a process line by line, filters it,
    and prints the lines that are *not* noisy.
    """
    try:
        for line in iter(process.stdout.readline, ""):
            line_strip = line.strip()
            is_noisy = any(s in line_strip for s in suppress_list)
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

    # --- Check for file argument ---
    if len(sys.argv) != 2:
        print("Usage: fw123d <file_to_watch.py>")
        sys.exit(1)

    file_to_watch = sys.argv[1]
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

    OCP_NOISY_STRINGS = ["DEBUG:", "INFO: [ocp_vscode]" "127.0.0.1 - -"]

    ocp_cmd = [sys.executable, "-m", "ocp_vscode"]

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

    # 4. Give the monitor a moment to connect
    time.sleep(0.5)

    # 5. Start the jupyter console (REPL) as the main process
    console_cmd = ["jupyter", "console", "--existing", connection_file]

    print(f"[Launcher] Handing over to Jupyter console. (File: {file_to_watch})")
    print("---------------------------------------------------------------")

    subprocess.run(console_cmd)

    print("\n---------------------------------------------------------------")
    print("[Launcher] Console exited. Shutting down all processes...")


if __name__ == "__main__":
    main()
