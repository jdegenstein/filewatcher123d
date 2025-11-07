import sys
import os
from pathlib import Path
import time
import queue
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from jupyter_client import BlockingKernelClient


class IPythonRunHandler(FileSystemEventHandler):
    """A handler that executes a file in an IPython kernel on modification."""

    def __init__(self, file_to_watch, kernel_client):
        self.file_to_watch = file_to_watch
        self.kernel_client = kernel_client
        self.last_run_time = 0
        print(f"[Monitor] Monitoring {self.file_to_watch.absolute()}...")

    def execute_in_ipython(self):
        current_time = time.time()
        if current_time - self.last_run_time < 1:
            return

        self.last_run_time = current_time

        print(f'\n[Monitor] Change detected! %run "{self.file_to_watch}"')

        try:
            # Send the execution request
            msg_id = self.kernel_client.execute(
                f'%run "{self.file_to_watch.absolute()}"'
            )

            # This loop waits for the "execute_reply" message on the shell channel,
            # while simultaneously processing all "stream" (stdout/stderr)
            # messages on the iopub channel.

            while True:
                try:
                    # Check for print statements (or errors)
                    # This waits for 0.2s for any IO message
                    io_msg = self.kernel_client.get_iopub_msg(timeout=0.2)

                    # Check if it's a stream message (stdout/stderr)
                    # and that it belongs to our request
                    if (
                        io_msg["msg_type"] == "stream"
                        and io_msg["parent_header"]["msg_id"] == msg_id
                    ):

                        # Print the content directly to the console
                        print(io_msg["content"]["text"], end="")

                except queue.Empty:
                    # No IO message, check if the shell reply (execution done) is in
                    try:
                        reply_msg = self.kernel_client.get_shell_msg(timeout=0)
                        if reply_msg["parent_header"]["msg_id"] == msg_id:
                            # We got the final "all done" reply, break the loop
                            break
                    except queue.Empty:
                        # No shell reply yet, just loop again
                        pass

            # Flush stdout to ensure all prints are shown
            sys.stdout.flush()

        except Exception as e:
            print(f"\n[Monitor] Error sending command: {e}")

        # Redraw the jupyter-console prompt
        print(f"\n>>> ", end="", flush=True)

    def on_modified(self, event):
        if event.is_directory:
            return
        if Path(event.src_path).absolute() == self.file_to_watch.absolute():
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
    watch_pathobj = Path(file_to_watch)
    watch_directory = watch_pathobj.parent
    event_handler = IPythonRunHandler(watch_pathobj, client)
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
