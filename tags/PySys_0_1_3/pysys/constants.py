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

import sys, re, os, socket

# constants used in testing
FALSE=0
TRUE=1
BACKGROUND = 10
FOREGROUND = 11
PASSED = 20
INSPECT = 21
NOTVERIFIED = 22
FAILED = 23
TIMEDOUT = 24
DUMPEDCORE = 25
BLOCKED = 26
SKIPPED = 27
WARN = 30
INFO = 31
DEBUG = 32

LOOKUP = {}
LOOKUP[PASSED] = "PASSED"
LOOKUP[INSPECT] = "REQUIRES INSPECTION"
LOOKUP[NOTVERIFIED] = "NOT VERIFIED"
LOOKUP[FAILED] = "FAILED"
LOOKUP[TIMEDOUT] = "TIMED OUT"
LOOKUP[DUMPEDCORE] = "DUMPED CORE"
LOOKUP[BLOCKED] = "BLOCKED"
LOOKUP[SKIPPED] = "SKIPPED"


# set the precedent for the test outcomes
PRECEDENT = [SKIPPED, BLOCKED, DUMPEDCORE, TIMEDOUT, FAILED, NOTVERIFIED, INSPECT, PASSED]
FAILS = [ BLOCKED, DUMPEDCORE, TIMEDOUT, FAILED ]


# set the default descriptor filename, input, output and reference directory names
DEFAULT_DESCRIPTOR = 'descriptor.xml'
DEFAULT_MODULE = 'run'
DEFAULT_SUITE = "Test Suite"
DEFAULT_TESTCLASS = 'PySysTest'
DEFAULT_INPUT = "Input"
DEFAULT_OUTPUT = "Output"
DEFAULT_REFERENCE = "Reference"


# set the directories to not recursively walk when looking for the descriptors
OSWALK_IGNORES = [ DEFAULT_INPUT, DEFAULT_OUTPUT, DEFAULT_REFERENCE, 'CVS', '.svn' ]


# set the timeout values for specific executables when executing a test
DEFAULT_TIMEOUT = 600
TIMEOUTS = {}
TIMEOUTS['WaitForSocket'] = 60
TIMEOUTS['WaitForFile'] = 30
TIMEOUTS['WaitForSignal'] = 60
TIMEOUTS['ManualTester'] = 1800


# set the platform and platform related constants
HOSTNAME = socket.getfqdn()
if re.search('win32', sys.platform):
	PLATFORM='win32'	
	DEVNULL = 'nul'
	WINDIR = os.getenv('windir', 'c:\WINDOWS')
	PATH = r"%s;%s\system32;%s\System32\Wbem" % (WINDIR, WINDIR, WINDIR)
	LD_LIBRARY_PATH = ""

elif re.search('sunos', sys.platform):
	PLATFORM='sunos'
	DEVNULL = '/dev/null'
	PATH = "/bin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/ccs/bin:/usr/openwin/bin:/opt/SUNWspro/bin"
	LD_LIBRARY_PATH = "/usr/local/lib" 

elif re.search('linux', sys.platform):
	PLATFORM='linux'	
	DEVNULL = '/dev/null'
	PATH = "/bin:/usr/bin:/usr/sbin:/usr/local/bin"
	LD_LIBRARY_PATH = "/usr/lib"
