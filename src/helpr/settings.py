# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights
# in this software.
#
# You should have received a copy of the BSD License along with HELPR.

from datetime import datetime
from enum import Enum
from pathlib import Path
import tempfile


"""General analysis settings such as directory locations and analysis state.

Notes
-----
To change a setting, reference it directly (e.g. import settings; settings.RUN_STATUS = ...)
Directory settings will be changed by GUI after this module is already initialized.

"""


class Status(Enum):
    """ Defines analysis status flags. """
    RUNNING = 1,
    STOPPING = 2,
    STOPPED = 3,
    FINISHED = 4,


INIT_TIME = datetime.now()
INIT_TIME_STR = INIT_TIME.strftime("%Y%m%d-%H%M")
RUN_STATUS = Status.RUNNING
CWD = Path.cwd()

# These are the only data the backend has that "know" about the GUI. If GUI is in use, it will update these values.
USING_GUI = False
GUI_STATUS_DICT = {}
ANALYSIS_ID = 0

# Use child temp dir if exists, otherwise platform-specific temp dir
OUTPUT_DIR = CWD.parent.joinpath('temp') if CWD.parent.joinpath('temp').is_dir() else Path(tempfile.gettempdir())
SESSION_DIR = OUTPUT_DIR.joinpath(f"session_{INIT_TIME_STR}")


def get_settings_str():
    msg = (f"==== Active Settings ====\n"
           f"Init time: {INIT_TIME_STR}\n"
           f"Output dir: {OUTPUT_DIR}\n"
           f"Session dir: {SESSION_DIR}\n"
           f"Run status: {RUN_STATUS}\n"
           f"Using GUI? {USING_GUI}\n"
           f"GUI data {GUI_STATUS_DICT}\n"
           f"Analysis id {ANALYSIS_ID}\n"
           "\n"
           )
    return msg


def is_finished():
    """Checks if analysis ran to completion. """
    return RUN_STATUS == Status.FINISHED


def is_stopped():
    """Checks if analysis was stopped. """
    return RUN_STATUS == Status.STOPPED


def is_stopping():
    """Checks if analysis stopping flag is set. """
    # GUI process manager is in sep process and can't change flag directly; it will update the shared status dict
    if USING_GUI and ANALYSIS_ID in GUI_STATUS_DICT and GUI_STATUS_DICT[ANALYSIS_ID] is False:
        return True

    else:
        return RUN_STATUS == Status.STOPPING
