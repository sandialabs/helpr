"""
Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""
import logging
import os
import sys
from pathlib import Path
import tempfile

# Default interactive backend causes bouncing dock icons in macOS.
import matplotlib
matplotlib.use("Agg")


"""
This module contains application-wide settings and parameters. Functionality and parameters here must be idempotent.

"""

DEBUG = False
VERBOSE = True
USE_LOGFILE = True

VERSION = "1.0.0"

# STARTED_AT = datetime.now()
IS_WINDOWS = False  # Assume macOS if false
WINDOWS_APP_ID = ""

# Ascertain platform (Windows or Mac)
try:
    from ctypes import windll  # Only exists on Windows.
    WINDOWS_APP_ID = 'com.SandiaNationalLaboratories.HELPR.V1_0_0'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(WINDOWS_APP_ID)
    IS_WINDOWS = True
except ImportError:
    IS_WINDOWS = False

# Disable to see exceptions in dev terminal
USE_SUBPROCESS = True
MP_POOL = None

# Max delay time, in seconds, in which to gracefully shut down thread and pool after user quits app.
SHUTDOWN_TIMER = 30

BASE_DIR = Path(os.path.dirname(__file__))
TEMP_DIR = Path(tempfile.gettempdir())

# session_dir is based on time and is created and set during app startup. Sub-processes must be passed its value directly.
SESSION_DIR = None

# Check if running from pyinstaller bundle, i.e. installed as app
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    APPLICATION_MODE = True
    CWD_DIR = Path(sys._MEIPASS)
else:
    APPLICATION_MODE = False
    # CWD_DIR = Path.cwd()
    CWD_DIR = BASE_DIR

# Dev-only access to in-development helpr module code without reloading/reinstalling
if not APPLICATION_MODE:
    helpr_pkg_path = Path.cwd().parents[1].joinpath('src')
    sys.path.insert(0, helpr_pkg_path.as_posix())


def setup_logging(output_dir: Path = None):
    """Activates stream and file logging based on app settings. """
    log_fmt = "%(asctime)s - %(process)d - %(levelname)s - %(message)s"
    log_dt_fmt = "%d-%b-%y %H:%M:%S"

    root = logging.getLogger("HELPR")
    root.setLevel(logging.DEBUG)

    if USE_LOGFILE and output_dir is not None and output_dir.exists():
        log_file = output_dir.joinpath('helpr.log')
        f_handler = logging.FileHandler(log_file.as_posix())
        f_handler.setLevel(logging.INFO)
        f_format = logging.Formatter(log_fmt, datefmt=log_dt_fmt)
        f_handler.setFormatter(f_format)
        root.addHandler(f_handler)

    # Output to console during dev
    if not APPLICATION_MODE:
        c_handler = logging.StreamHandler()
        c_handler.setLevel(logging.INFO)
        c_format = logging.Formatter(log_fmt, datefmt=log_dt_fmt)
        c_handler.setFormatter(c_format)
        root.addHandler(c_handler)
