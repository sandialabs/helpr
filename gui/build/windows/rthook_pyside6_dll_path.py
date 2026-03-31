# Copyright 2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
# You should have received a copy of the BSD License along with HELPR.
#
# Runtime hook: ensures PySide6 DLL directory is on PATH so QML plugins can find Qt DLLs.
import os
import sys

if sys.platform.startswith('win'):
    pyside6_dir = os.path.join(sys._MEIPASS, 'PySide6')
    if os.path.isdir(pyside6_dir):
        os.environ['PATH'] = pyside6_dir + os.pathsep + os.environ.get('PATH', '')
