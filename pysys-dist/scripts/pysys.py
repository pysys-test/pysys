#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2018  M.B.Grieve

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

# Contact: moraygrieve@users.sourceforge.net

import os, sys, logging

# the sys.path starts with the directory containing pysys.py which we want to remove as
# that dir might be anywhere and could contain anything; it's not needed for locating 
# the pysys modules since those will be in site-packages once pysys is installed
script_path = os.path.abspath(sys.path[0])
sys.path = [p for p in sys.path if os.path.abspath(p) != script_path]

# before anything else, configure the logger
logging.getLogger().addHandler(logging.NullHandler())
from pysys import log, stdoutHandler
stdoutHandler.setLevel(logging.INFO)
log.addHandler(stdoutHandler)

from pysys.constants import loadproject
loadproject(os.getcwd())

from pysys import __version__
from pysys.constants import *
from pysys.utils.loader import import_module
from pysys.launcher.console import main

if __name__ == "__main__":
	main(sys.argv[1:])