# filewatcher123d
A file watcher oriented towards use with build123d and ocp_vscode. What this does is spawn several processes:

1. starts an ipython kernel (really a jupyter-console)
2. starts a watchdog monitor (using the excellent watchdog package)
3. starts an ocp_vscode process and filters the output (in another thread) to remove excessive messages

Usage examples:
```
fw123d [--autoreload] demo_watcher.py
```

Note that the autoreload flag will enable the ipython autoreload extension. The purpose
of this extension / flag is to monitor the files **imported by** the watched file. I have added another
demo file `otherparameters.py` which can be changed to illustrate the benefit of this flag.

or alternatively:
```
python -m filewatcher123d.cli [--autoreload] demo_watcher.py
```

Then you need to open the viewer in a browser, should be something like http://127.0.0.1:3939/viewer

From there when you save demo_watcher.py, the watcher should detect any changes and rerun the code in the ipython session.
Also, the ipython console is still available and allows to inspect any variables / build123d objects interactively.

How to install (currently only on github):
```
pip install git+https://github.com/jdegenstein/filewatcher123d
```
