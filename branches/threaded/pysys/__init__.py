#!/usr/bin/env python
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and any associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# The software is provided "as is", without warranty of any
# kind, express or implied, including but not limited to the
# warranties of merchantability, fitness for a particular purpose
# and noninfringement. In no event shall the authors or copyright
# holders be liable for any claim, damages or other liability,
# whether in an action of contract, tort or otherwise, arising from,
# out of or in connection with the software or the use or other
# dealings in the software
"""
PySys System Test Framework.

PySys has been designed to provide a generic extensible framework for the organisation and execution of system level testcases. 
It provides a clear model of what a testcases is, how it is structured on disk, how it is executed and validated, and how the 
outcome is reported for test auditing purposes. 

Testcases are instances of a base test class (L{pysys.basetest.BaseTest}) which provides core functionality for cross platform 
process management and manipulation; in this manner an application under test (AUT) can be started and manipulated directly 
within the testcase. The base test class additionally provides a set of standard validation techniques based predominantly 
on regular expression matching within text files (e.g. stdout, logfile of the AUT etc). Testcases are executed through a base 
runner (L{pysys.baserunner.BaseRunner}) which provides the mechanism to control testcase flow and auditing. In both cases the 
base test and runner classes have been designed to be extended for a particular AUT, e.g. to allow a higher level of abstraction 
of AUT manipulation, tear up and tear down prior to executing a set of testcases etc. 

PySys allows automated regression testcases to be built rapidly. Where an AUT cannot be tested in an automated fashion, testcases 
can be written to make use of a manual test user interface application (L{pysys.manual.ui.ManualTester}) which allows the steps 
required to execute the test to be presented to a tester in a concise and navigable manner. The tight integration of both manual 
and automated testcases provides a single framework for all test organisation requirements. 

"""

import sys, logging, thread
logging._levelNames[50] = 'CRIT'
logging._levelNames[30] = 'WARN'

__author__  = "Moray Grieve"
"""The author of PySys."""

__author_email__ = "moraygrieve@users.sourceforge.net"
"""The author's email address."""

__status__  = "alpha"
"""The status of this release."""

__version__ = "0.6.1"
"""The version of this release."""

__date__    = "24 Nov 2008"
"""The date of this release."""

__all__     = [ "constants",
                "exceptions",
                "baserunner",
                "basetest",
                "interfaces",
                "launcher",
                "manual",
                "process",
                "utils",
                "writer",
                "xml"]
"""The submodules of PySys."""


class ThreadedStdoutHandler(logging.StreamHandler):
	"""Stream handler to only log from the creating thread."""
	
	def __init__(self, strm):
		self.threadId = thread.get_ident()
		logging.StreamHandler.__init__(self, strm)
				
	def emit(self, record):
		if self.threadId != thread.get_ident(): return
		logging.StreamHandler.emit(self, record)
		
		
class ThreadedFileHandler(logging.FileHandler):
	"""File handler to only log from the creating thread."""
	
	def __init__(self, filename):
		self.threadId = thread.get_ident()
		self.buffer = []
		logging.FileHandler.__init__(self, filename, "a")
				
	def emit(self, record):
		if self.threadId != thread.get_ident(): return
		self.buffer.append(record.getMessage())
		logging.FileHandler.emit(self, record)
		
	def getBuffer(self):
		return self.buffer

rootLogger = logging.getLogger()
"""The root logger for all logging within PySys."""

rootLogger.setLevel(logging.DEBUG)
"""The root logger log level (set to DEBUG as all filtering is done by the handlers)."""

stdoutHandler = ThreadedStdoutHandler(sys.stdout)
"""The default stdout logging handler for all logging within PySys."""

stdoutFormatter = logging.Formatter('%(asctime)s %(levelname)-5s %(message)s')
"""The formatter for output to stdout."""

stdoutHandler.setFormatter(stdoutFormatter)
stdoutHandler.setLevel(logging.INFO)
rootLogger.addHandler(stdoutHandler)

