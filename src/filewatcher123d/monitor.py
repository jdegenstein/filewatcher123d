import sys
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from jupyter_client import BlockingKernelClient


class IPythonRunHandler(FileSystemEventHandler):
    """A handler that executes a file in an IPython kernel on modification."""

    def __init__(self, file_to_watch, kernel_client):
        self.file_to_watch = os.path.abspath(file_to_watch)
        self.kernel_client = kernel_client
        self.last_run_time = 0
        print(f"[Monitor] Monitoring {self.file_to_watch}...")

    def execute_in_ipython(self):
        current_time = time.time()
        if current_time - self.last_run_time < 1:
            return

        self.last_run_time = current_time

        print(f"\n[Monitor] Change detected! Running: %run {self.file_to_watch}")
        try:
            msg_id = self.kernel_client.execute(f"%run {self.file_to_watch}")
            self.kernel_client.get_shell_msg(timeout=5)
            # This print() helps redraw the IPython prompt TODO: fix this
            print(f">>> ", end="", flush=True)

        except Exception as e:
            print(f"\n[Monitor] Error sending command: {e}")
            print(f">>> ", end="", flush=True)

    def on_modified(self, event):
        if event.is_directory:
            return
        if os.path.abspath(event.src_path) == self.file_to_watch:
            self.execute_in_ipython()


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print(
            "Usage: python -m filewatcher123d.monitor <file_to_watch.py> <kernel_connection_file.json>"
        )
        sys.exit(1)

    file_to_watch = sys.argv[1]
    connection_file_path = sys.argv[2]

    # Set up the kernel client
    client = BlockingKernelClient()
    client.load_connection_file(connection_file_path)
    client.start_channels()
    print("[Monitor] Successfully connected to IPython kernel.")

    # Set up watchdog
    watch_directory = os.path.dirname(os.path.abspath(file_to_watch))
    event_handler = IPythonRunHandler(file_to_watch, client)
    observer = Observer()
    observer.schedule(event_handler, watch_directory, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        client.stop_channels()
    observer.join()
