# filewatcher123d
A file watcher oriented towards use with build123d and ocp_vscode. What this does is spawn several processes:

1. starts an ipython kernel (really a jupyter-console)
2. starts a watchdog monitor (using the excellent watchdog package)
3. starts an ocp_vscode process and filters the output (in another thread) to remove excessive messages

Usage examples:
```
fw123d demo_watcher.py
```

or alternatively:
```
python -m filewatcher123d.cli demo_watcher.py
```

Then you need to open the viewer in a browser, should be something like http://127.0.0.1:3939/viewer

From there when you save demo_watcher.py, the watcher should detect any changes and rerun the code in the ipython session.
Also, the ipython console is still available and allows to inspect any variables / build123d objects interactively.

TODO: check that errors in the watched file are properly routed/displayed in the ipython session

How to install (currently only on github):
```
pip install git+https://github.com/jdegenstein/filewatcher123d
```
