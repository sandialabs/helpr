# -*- mode: python ; coding: utf-8 -*-

"""
Copyright 2023-2025 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

You should have received a copy of the BSD License along with HELPR.

"""

import os
import shutil
import sys
from pathlib import Path

# Ensure dev environment is not active, as it contains many modules that must not be included in build.
try:
    import jupyter
    print("ERROR - successful Jupyter import indicates development environment is active. Halting build.")
    sys.exit(0)
except ImportError or ModuleNotFoundError:
    pass

"""
Creates code bundle for Windows distribution.

    cd build\windows\
    pyinstaller .\build_win.spec --noconfirm

This script also excludes license-incompatible modules according to:
https://doc.qt.io/qt-6/qtmodules.html#gpl-licensed-addons

"""

# Specify included Qt directories and files to ensure incompatible (GPL) modules are excluded.
do_filtering = True
version_str = "2.1.0"
appname = "HELPR"

build_dir = Path(os.getcwd())
repo_dir = build_dir.parent.parent.parent
app_dir = repo_dir.joinpath('gui/src/helprgui')
lib_dir = repo_dir.joinpath('src')
dist_dir = build_dir.joinpath(f'dist/{appname}')
pyside_dir = build_dir.joinpath(f'dist/{appname}/PySide6')

print(f"Repo dir exists {repo_dir.exists()}: {repo_dir}")
print(f"App dir exists {app_dir.exists()}: {app_dir}")
print(f"Lib dir exists {lib_dir.exists()}: {lib_dir}")
print(f"Build dir exists {build_dir.exists()}: {build_dir}")


# GPL v3-only modules (MUST exclude - incompatible with HELPR's BSD license)
# See: https://doc.qt.io/qt-6/licensing.html and individual module pages
gpl_only_blacklist = [
    'QtCharts',
    'QtCoAP',
    'DataVisualization',
    'QtDataVisualization',
    'QtGraphs',
    'QtGrpc',
    'QtHttpServer',
    'Lottie',
    'MQTT',
    'NetworkAuthorization',
    'QtQuick3D',
    'QtQuick3DPhysics',
    'Timeline',
    'QtQuickTimeline',
    'VirtualKeyboard',
    'Wayland',
    'Qt5Compat',
]

# Additional modules excluded by project policy (not needed, reduces size/attack surface)
additional_blacklist = [
    'Scene3D',
    'QtRemoteObjects',
    'QtSensors',
    'QtWebChannel',
    'QtWebSockets',
]

pyside_dir_blacklist = gpl_only_blacklist + additional_blacklist

pyside_qml_subdir_whitelist = [
    'QtCore',
    'QtQml',
    'QtQuick',
    'QtTest',
]

qt_file_whitelist = [
    'opengl32sw.dll',
    'pyside6.abi3.dll',
    'pyside6qml.abi3.dll',

    'Qt6Concurrent.dll',
    'Qt6Core.dll',
    'Qt6Gui.dll',
    'Qt6Network.dll',
    'Qt6OpenGL.dll',

    'Qt6Qml.dll',
    'Qt6QmlCore.dll',
    'Qt6QmlLocalStorage.dll',
    'Qt6QmlModels.dll',
    'Qt6QmlWorkerScript.dll',
    'Qt6QmlXmlListModel.dll',

    'Qt6Quick.dll',
    'Qt6QuickControls2.dll',
    'Qt6QuickControls2Impl.dll',

    'Qt6QuickDialogs2.dll',
    'Qt6QuickDialogs2QuickImpl.dll',
    'Qt6QuickDialogs2Utils.dll',

    'Qt6QuickLayouts.dll',
    'Qt6QuickTemplates2.dll',
    'Qt6QuickTest.dll',

    'Qt6Svg.dll',
    'Qt6Test.dll',
    'Qt6Widgets.dll',

    'QtCore.pyd',
    'QtGui.pyd',
    'QtNetwork.pyd',
    'QtOpenGL.pyd',
    'QtQml.pyd',
    'QtSvg.pyd',
    'QtWidgets.pyd',
]

# Misc. dirs not caught by above, that should be removed
dirs_to_delete = [
    pyside_dir.joinpath('qml/Qt/labs/animation'),
    pyside_dir.joinpath('qml/Qt/labs/platform'),
    pyside_dir.joinpath('qml/Qt/labs/sharedimage'),
    pyside_dir.joinpath('qml/Qt/labs/wavefrontmesh'),
]


def filter_output_files(lst):
    """
    Excludes GPL-licensed Qt modules from the build.
    DO NOT DISABLE THIS - it ensures only license-compatible modules are included.

    Uses a blacklist approach: keep everything except known GPL-incompatible modules.
    """
    to_keep = []
    for (dest, source, kind) in lst:
        fpath = Path(dest)
        parts = fpath.parts

        # Check against GPL module blacklist
        skip = False
        for entry in pyside_dir_blacklist:
            if entry in parts:
                skip = True
                break
        if skip:
            print(f"Excluding (GPL): {fpath}")
            continue

        # Exclude translations (not needed, reduces size)
        if 'PySide6' in dest and 'translations' in parts:
            print(f"Excluding (translations): {fpath}")
            continue

        # Exclude specific plugin dirs that aren't needed
        if 'PySide6' in dest and 'plugins' in parts:
            if 'platforminputcontexts' in parts or 'qmltooling' in parts:
                print(f"Excluding (plugin): {fpath}")
                continue

        to_keep.append((dest, source, kind))

    return to_keep


def post_build_cleanup():
    """Remove GPL-licensed modules that may have been pulled in by binary dependency analysis."""
    print('== POST-BUILD CLEANUP ==')

    # Delete specific directories
    for dirpath in dirs_to_delete:
        print(dirpath.as_posix())
        if dirpath.exists():
            try:
                shutil.rmtree(dirpath)
                print(f"Deleted {dirpath.as_posix()}")
            except OSError as e:
                print(f"Could not remove dir: {dirpath} - {e.strerror}")

    # Scan entire dist tree and remove anything matching blacklisted entries.
    # For DLL matching, normalize Qt6XYZ -> QtXYZ to match blacklist entries like 'QtCharts'.
    def matches_blacklist(fpath):
        for entry in pyside_dir_blacklist:
            if entry in fpath.parts:
                return True
            # Normalize stem: Qt6Charts -> QtCharts, Qt63DCore -> Qt3DCore
            stem = fpath.stem
            normalized = stem.replace('Qt6', 'Qt', 1)
            if entry in stem or entry in normalized:
                return True
        return False

    for fpath in sorted(dist_dir.rglob('*'), reverse=True):
        if matches_blacklist(fpath) and fpath.exists():
            if fpath.is_dir():
                shutil.rmtree(fpath)
                print(f"Deleted dir: {fpath}")
            else:
                fpath.unlink()
                print(f"Deleted file: {fpath}")


res = Analysis(
        [app_dir.joinpath('main.py')],
        pathex=[
            app_dir,
            lib_dir,
        ],
        datas=[
            (app_dir.joinpath('ui'), 'ui/'),
            (app_dir.joinpath('hygu/ui'), 'hygu/ui/'),
            (app_dir.joinpath('hygu/resources'), 'hygu/resources/'),
            (app_dir.joinpath('assets'), 'assets/'),
            (repo_dir.joinpath('src/helpr/data'), 'data/')
        ],
        binaries=[],
        hiddenimports=[],
        hookspath=[],
        hooksconfig={},
        runtime_hooks=['rthook_pyside6_dll_path.py'],
        excludes=[],
        noarchive=False,
)

if do_filtering:
    # empty PySide6 dir
    if dist_dir.exists():
        shutil.rmtree(dist_dir.as_posix())
    if pyside_dir.exists():
        shutil.rmtree(pyside_dir.as_posix())

    # filter based on above whitelists
    res.binaries = filter_output_files(res.binaries)
    res.datas = filter_output_files(res.datas)


pyz = PYZ(res.pure)

exe = EXE(
        pyz,
        res.scripts,
        [],
        exclude_binaries=True,
        name=f'{appname}',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        icon="icon.ico",
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        contents_directory='.',
)
coll = COLLECT(
        exe,
        res.binaries,
        res.zipfiles,
        res.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=f'{appname}',
)

if do_filtering:
    post_build_cleanup()


# Spot-check that filtering was applied
assert pyside_dir.joinpath('Qt6Core.dll').exists()
assert pyside_dir.joinpath('qml/QtQuick/Layouts').exists()

assert not pyside_dir.joinpath('Qt6Charts.dll').exists()
assert not pyside_dir.joinpath('Qt6QuickTimeline.dll').exists()

assert not pyside_dir.joinpath('qml/QtQuick/Timeline').exists()
assert not pyside_dir.joinpath('QtCharts').exists()

for item in pyside_dir_blacklist:
    fpath = pyside_dir.joinpath(item)
    assert not fpath.exists()

assert do_filtering

print('\a')  # terminal bell
print(f'== BUILD COMPLETE: {appname} {version_str} ==')