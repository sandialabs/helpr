# Resource object code (Python 3)
# Created by: object code
# Created by: The Resource Compiler for Qt version 6.6.0
# WARNING! All changes made in this file will be lost!

from PySide6 import QtCore

qt_resource_data = b"\
\x00\x00\x00p\
#\
 Note: file unus\
ed for now\x0d\x0a[Con\
trols]\x0d\x0aStyle=Ma\
terial\x0d\x0a\x0d\x0a[Mater\
ial]\x0d\x0aTheme=Ligh\
t\x0d\x0aVariant=Dense\
\x0d\x0aAccent=Blue\x0d\x0a\
"

qt_resource_name = b"\
\x00\x15\
\x08\x1e\x16f\
\x00q\
\x00t\x00q\x00u\x00i\x00c\x00k\x00c\x00o\x00n\x00t\x00r\x00o\x00l\x00s\x002\x00.\
\x00c\x00o\x00n\x00f\
"

qt_resource_struct = b"\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x01\
\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\
\x00\x00\x01\x8b\x1a\xc1\x06v\
"

def qInitResources():
    QtCore.qRegisterResourceData(0x03, qt_resource_struct, qt_resource_name, qt_resource_data)

def qCleanupResources():
    QtCore.qUnregisterResourceData(0x03, qt_resource_struct, qt_resource_name, qt_resource_data)

qInitResources()
