import argparse
import sys
import time
from pathlib import Path
from typing import Optional

from jupyter_client import BlockingKernelClient
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class IPythonRunHandler(FileSystemEventHandler):
    """Watchdog event handler that detects changes to a target file and

    triggers re-execution in a connected IPython kernel.
    """

    def __init__(
        self,
        file_to_watch: Path,
        kernel_client: BlockingKernelClient,
        debounce_seconds: float = 0.15,
    ):
        super().__init__()
        self.file_to_watch = Path(file_to_watch).resolve()
        self.kernel_client = kernel_client
        self.debounce_seconds = debounce_seconds
        self._last_trigger_time: float = 0.0

    def on_any_event(self, event):
        if event.is_directory:
            return

        # Resolve paths to handle relative paths, symlinks, and OS path normalization
        src = Path(event.src_path).resolve()
        dest = (
            Path(event.dest_path).resolve()
            if getattr(event, "dest_path", None)
            else None
        )

        # Trigger on direct modifications or atomic save renames (e.g. Geany, Vim, VS Code)
        if src == self.file_to_watch or dest == self.file_to_watch:
            now = time.time()
            if now - self._last_trigger_time >= self.debounce_seconds:
                self._last_trigger_time = now
                self._trigger_execution()

    def _trigger_execution(self):
        """Send a %run magic command to the IPython kernel to re-execute the target file."""
        code = f'%run -i "{self.file_to_watch}"'
        print(
            f"\n[filewatcher123d] Change detected. Executing: {self.file_to_watch.name}..."
        )
        try:
            self.kernel_client.execute(code)
        except Exception as err:
            print(
                f"[filewatcher123d] Error executing code in kernel: {err}",
                file=sys.stderr,
            )


def start_monitoring(
    file_to_watch: Path,
    connection_file: Optional[Path] = None,
    debounce_seconds: float = 0.15,
):
    """Connect to the IPython kernel, set up the directory watchdog, and block until interrupted."""
    file_path = Path(file_to_watch).resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"Target file does not exist: {file_path}")

    # Initialize IPython Kernel Client connection
    kc = BlockingKernelClient()
    if connection_file:
        kc.load_connection_file(str(connection_file))
    else:
        kc.load_connection_file()
    kc.start_channels()

    handler = IPythonRunHandler(
        file_to_watch=file_path,
        kernel_client=kc,
        debounce_seconds=debounce_seconds,
    )

    observer = Observer()
    # Watch the parent directory so watchdog catches FileMovedEvent from atomic saves
    watch_dir = file_path.parent
    observer.schedule(handler, path=str(watch_dir), recursive=False)
    observer.start()

    print(f"[filewatcher123d] Monitoring '{file_path.name}' in '{watch_dir}'...")

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[filewatcher123d] Stopping file monitor...")
        observer.stop()
    finally:
        observer.join()
        kc.stop_channels()


def main():
    parser = argparse.ArgumentParser(
        description="Monitor a Python script and re-execute it in an active IPython kernel on save."
    )
    parser.add_argument(
        "file_to_watch",
        type=Path,
        help="Path to the Python script to monitor.",
    )
    parser.add_argument(
        "--connection-file",
        type=Path,
        default=None,
        help="Path to the IPython kernel connection JSON file.",
    )
    parser.add_argument(
        "--debounce",
        type=float,
        default=0.15,
        help="Debounce window in seconds (default: 0.15).",
    )

    args = parser.parse_args()

    try:
        start_monitoring(
            file_to_watch=args.file_to_watch,
            connection_file=args.connection_file,
            debounce_seconds=args.debounce,
        )
    except Exception as exc:
        print(f"[filewatcher123d] Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
