#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2015  M.B.Grieve

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

import string, os.path, time, thread, logging, Queue
import win32api, win32pdh, win32security, win32process, win32file, win32pipe, win32con, pywintypes, threading

from pysys import log
from pysys import process_lock
from pysys.constants import *
from pysys.exceptions import *

# check for new lines on end of a string
EXPR = re.compile(".*\n$")

def _stringToUnicode(s):
	""" Converts a unicode string or a utf-8 bit string into a unicode string. 
	
	"""
	if isinstance(s, unicode):
		return s
	else:
		return unicode(s, "utf8")

class CommonProcessWrapper(object):
	"""Common process wrapper superclass for process execution and management. 
	
	The process wrapper provides the ability to start and stop an external process, setting 
	the process environment, working directory and state i.e. a foreground process in which case 
	a call to the L{start} method will not return until the process has exited, or a background 
	process in which case the process is started in a separate thread allowing concurrent execution 
	within the testcase. Processes started in the foreground can have a timeout associated with them, such
	that should the timeout be exceeded, the process will be terminated and control	passed back to the 
	caller of the method. The wrapper additionally allows control over logging of the process stdout 
	and stderr to file, and writing to the process stdin.
	
	Usage of the class is to first create an instance, setting all runtime parameters of the process 
	as data attributes to the class instance via the constructor. The process can then be started 
	and stopped via the L{start} and L{stop} methods of the class, as well as interrogated for 
	its executing status via the L{running} method, and waited for its completion via the L{wait}
	method. During process execution the C{self.pid} and C{seld.exitStatus} data attributes are set 
	within the class instance, and these values can be accessed directly via it's object reference.  

	@ivar pid: The process id for a running or complete process (as set by the OS)
	@type pid: integer
	@ivar exitStatus: The process exit status for a completed process	
	@type exitStatus: integer
	
	"""

	def __init__(self, command, arguments, environs, workingDir, state, timeout, stdout=None, stderr=None, displayName=None):
		"""Create an instance of the process wrapper.
		
		@param command:  The full path to the command to execute
		@param arguments:  A list of arguments to the command
		@param environs:  A dictionary of environment variables (key, value) for the process context execution
		@param workingDir:  The working directory for the process
		@param state:  The state of the process (L{pysys.constants.FOREGROUND} or L{pysys.constants.BACKGROUND}
		@param timeout:  The timeout in seconds to be applied to the process
		@param stdout:  The full path to the filename to write the stdout of the process
		@param stderr:  The full path to the filename to write the sdterr of the process
		@param displayName: Display name for this process

		"""
		self.displayName = displayName if displayName else os.path.basename(command)
		self.command = command
		self.arguments = arguments
		self.environs = {}
		for key in environs: self.environs[_stringToUnicode(key)] = _stringToUnicode(environs[key])
		self.workingDir = workingDir
		self.state = state
		self.timeout = timeout

		# 'publicly' available data attributes set on execution
		self.pid = None
		self.exitStatus = None

		# print process debug information
		log.debug("Process parameters for executable %s" % os.path.basename(self.command))
		log.debug("  command      : %s", self.command)
		for a in self.arguments: log.debug("  argument     : %s", a)
		log.debug("  working dir  : %s", self.workingDir)
		log.debug("  stdout       : %s", stdout)
		log.debug("  stderr       : %s", stderr)
		keys=self.environs.keys()
		keys.sort()
		for e in keys: log.debug("  environment  : %s=%s", e, self.environs[e])

		# private
		self._outQueue = Queue.Queue()		


	def __str__(self): return self.displayName
	def __repr__(self): return '%s(pid %s)'%(self.displayName, self.pid)

	# these abstract methods msut be implemented by subclasses
	def _setExitStatus(self): raise Exception('Not implemented')
	def _startBackgroundProcess(self): raise Exception('Not implemented')
	def _writeStdin(self, fd): raise Exception('Not implemented')
	def stop(self): raise Exception('Not implemented')
	def signal(self): raise Exception('Not implemented')

	def write(self, data, addNewLine=True):
		"""Write data to the stdin of the process.
		
		Note that when the addNewLine argument is set to true, if a new line does not 
		terminate the input data string, a newline character will be added. If one 
		already exists a new line character will not be added. Should you explicitly 
		require to add data without the method appending a new line charater set 
		addNewLine to false.
		
		@param data:       The data to write to the process stdout
		@param addNewLine: True if a new line character is to be added to the end of 
		                   the data string
		
		"""
		if addNewLine and not EXPR.search(data): data = "%s\n" % data
		self._outQueue.put(data)
		
	def running(self):
		"""Check to see if a process is running, returning true if running.
		
		@return: The running status (True / False)
		@rtype: integer
		
		"""
		return self._setExitStatus() is None


	def wait(self, timeout):
		"""Wait for a process to complete execution.
		
		The method will block until either the process is no longer running, or the timeout 
		is exceeded. Note that the method will not terminate the process if the timeout is 
		exceeded. 
		
		@param timeout: The timeout to wait in seconds
		@raise ProcessTimeout: Raised if the timeout is exceeded.
		
		"""
		startTime = time.time()
		while self.running():
			if timeout:
				currentTime = time.time()
				if currentTime > startTime + timeout:
					raise ProcessTimeout, "Process timedout"
			time.sleep(0.05)
		


	def start(self):
		"""Start a process using the runtime parameters set at instantiation.
		
		@raise ProcessError: Raised if there is an error creating the process
		@raise ProcessTimeout: Raised in the process timed out (foreground process only)
		
		"""
		if self.state == FOREGROUND:
			self._startBackgroundProcess()
			self.wait(self.timeout)
		else:
			self._startBackgroundProcess()
