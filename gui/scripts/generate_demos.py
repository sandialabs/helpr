#!/usr/bin/env python
"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

Generates demo .hpr files for each study type using current default parameter values.

Usage:
    cd repo/gui
    python scripts/generate_demos.py

"""
import sys
from pathlib import Path

# Add the src directory to path so we can import helprgui
script_dir = Path(__file__).parent
gui_src_dir = script_dir.parent / 'src'
sys.path.insert(0, str(gui_src_dir))

# Initialize app settings before importing State (required for logging and paths)
from helprgui import app_settings
app_settings.init()

from helprgui.models.models import State
from helprgui.models.enums import StudyTypes


DEMO_DIR = gui_src_dir / 'helprgui' / 'assets' / 'demo'

STUDY_TYPE_FILES = {
    StudyTypes.det: 'det_demo.hpr',
    StudyTypes.prb: 'prb_demo.hpr',
    StudyTypes.sam: 'sam_demo.hpr',
    StudyTypes.bnd: 'bnd_demo.hpr',
}


def generate_demo_file(study_type: str, output_path: Path) -> None:
    """Generate a demo file for the specified study type.

    Parameters
    ----------
    study_type : str
        One of 'det', 'prb', 'sam', 'bnd'
    output_path : Path
        Full path to the output .hpr file
    """
    state = State(defaults=study_type)
    state.save_to_file(output_path)
    print(f"  Generated: {output_path.name}")


def main():
    """Generate all demo files."""
    print(f"Generating demo files in: {DEMO_DIR}")
    print()

    if not DEMO_DIR.exists():
        print(f"Error: Demo directory does not exist: {DEMO_DIR}")
        sys.exit(1)

    for study_type, filename in STUDY_TYPE_FILES.items():
        output_path = DEMO_DIR / filename
        generate_demo_file(study_type, output_path)

    print()
    print("Done. All demo files regenerated.")


if __name__ == '__main__':
    main()
