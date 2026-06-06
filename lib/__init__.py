"""lib package — ensure project root is on sys.path before submodules load.

Streamlit Cloud's multi-page app loader on Python 3.14 reruns scripts
in a way that occasionally loses sys.path tweaks done in page files.
Doing it here guarantees `lib.X` resolves no matter how the loader
reaches this package.
"""
import sys
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
