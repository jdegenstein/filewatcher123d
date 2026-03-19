# filewatcher123d

**A live-coding, interactive environment for building 3D models with Python.**

If you are new to the world of Code-CAD (using code to generate 3D CAD models), you'll quickly find that restarting your Python scripts over and over to see small visual changes can be tedious and slow. `filewatcher123d` is designed to solve that by providing a seamless, instant-feedback loop for the `build123d` library. 

## Why use this?

* **Instant Visual Feedback:** Every time you save your Python file, your 3D model automatically updates in your web browser. No need to switch windows and manually re-run your script.
* **Lightning Fast Executions:** Standard Python scripts load heavy CAD libraries from scratch every single time they run. This tool keeps a Python session open in the background, meaning your script re-runs instantly without the heavy startup delay.
* **Interactive Inspection:** Because your code runs in a persistent console, you don't just get a visual model -- you get an interactive terminal. After your script runs, you can type commands directly into the terminal to inspect variables, measure distances, or test new `build123d` operations on the fly.
* **Zero-Config Viewer:** It automatically handles the background server needed to display your 3D models (using `ocp_vscode`), keeping your focus on the code.

## How it Works

Under the hood, `filewatcher123d` acts as an orchestra conductor for three powerful tools:

1. **IPython (Jupyter Console):** It starts an interactive Python session that holds your variables and CAD libraries in memory.
2. **Watchdog:** It silently monitors your specific Python file (and optionally its dependencies) for any "Save" events.
3. **OCP VSCode Server:** It launches a local web server that receives the 3D geometry from your code and renders it in your browser. 

When a save is detected, the watcher tells IPython to re-run your code, which immediately updates the web viewer. It also filters out unnecessary background noise in the console so you only see what matters.

---

## Getting Started

### Installation
Currently, the package can be installed directly from GitHub using pip:

```bash
pip install git+https://github.com/jdegenstein/filewatcher123d
```

### Basic Usage

To start watching a file (for example, `demo_watcher.py`), run the following command in your terminal:

```bash
fw123d demo_watcher.py
```
*(Alternatively, you can run: `python -m filewatcher123d.cli demo_watcher.py`)*

Once the command is running, open your web browser and navigate to the viewer:
**[http://127.0.0.1:3939/viewer](http://127.0.0.1:3939/viewer)**

Now, whenever you save changes to `demo_watcher.py`, the browser will automatically refresh with your updated 3D model. The terminal where you started the command is now an active IPython console -- feel free to type Python commands there to interact with your code!

### Advanced Features

**Auto-reloading Dependencies (`-a` flag)**
If your main script imports other Python files (like a file containing configuration parameters), you'll want the viewer to update when you change *those* files, too. You can enable the autoreload feature using the `-a` or `--autoreload` flag:

```bash
fw123d -a demo_watcher.py
```

**Manual Execution (`%r`)**
If you ever want to force your watched file to re-run without actually saving a change to the file, simply type the special magic command `%r` into the running console and press Enter.

**Help Menu**
To see a full list of available arguments, run:
```bash
fw123d --help
```
