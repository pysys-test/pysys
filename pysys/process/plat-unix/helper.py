#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2016  M.B.Grieve

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

import signal, time, copy, logging, Queue, thread, errno, threading

from pysys import log
from pysys import process_lock
from pysys.constants import *
from pysys.exceptions import *
from pysys.process.commonwrapper import CommonProcessWrapper, _stringToUnicode


class ProcessWrapper(CommonProcessWrapper):
	"""Unix process wrapper for process execution and management. 
	
	The unix process wrapper provides the ability to start and stop an external process, setting 
	the process environment, working directory and state i.e. a foreground process in which case 
	a call to the L{start()} method will not return until the process has exited, or a background 
	process in which case the process is started in a separate thread allowing concurrent execution 
	within the testcase. Processes started in the foreground can have a timeout associated with them, such
	that should the timeout be exceeded, the process will be terminated and control	passed back to the 
	caller of the method. The wrapper additionally allows control over logging of the process stdout 
	and stderr to file, and writing to the process stdin.
	
	Usage of the class is to first create an instance, setting all runtime parameters of the process 
	as data attributes to the class instance via the constructor. The process can then be started 
	and stopped via the L{start()} and L{stop()} methods of the class, as well as interrogated for 
	its executing status via the L{running()} method, and waited for its completion via the L{wait()}
	method. During process execution the C{self.pid} and C{seld.exitStatus} data attributes are set 
	within the class instance, and these values can be accessed directly via it's object reference.  

	@ivar pid: The process id for a running or complete process (as set by the OS)
	@type pid: integer
	@ivar exitStatus: The process exit status for a completed process	
	@type exitStatus: integer
	
	"""

	def __init__(self, command, arguments, environs, workingDir, state, timeout, stdout=None, stderr=None, displayName=None, **kwargs):
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
		CommonProcessWrapper.__init__(self, command, arguments, environs, workingDir, 
			state, timeout, stdout, stderr, displayName, **kwargs)
		
		self.stdout = '/dev/null'
		self.stderr = '/dev/null'
		try:
			if stdout is not None: self.stdout = stdout
		except:
			log.info('Unable to create file to capture stdout - using the null device')
		try:
			if stderr is not None: self.stderr = stderr
		except:
			log.info('Unable to create file to capture stdout - using the null device')

		# private instance variables
		self.__lock = threading.Lock() # to protect access to the fields that get updated while process is running


	def writeStdin(self):
		"""Thread method to write to the process stdin pipe.
		
		"""
		while self._outQueue:
			try:
				data = self._outQueue.get(block=True, timeout=0.25)
			except Queue.Empty:
				if not self.running(): 
					# no need to close stdin here, as previous call's setExitCode() method will do it
					break
			else:
				with self.__lock:
					if self.__stdin:
						os.write(self.__stdin, data)	
	

	def startBackgroundProcess(self):
		"""Method to start a process running in the background.
		
		"""
		with process_lock:

			try:
				stdin_r, stdin_w = os.pipe()
				self.pid = os.fork()

				if self.pid == 0:
					# change working directory of the child process
					os.chdir(self.workingDir)
						
					# duplicate the read end of the pipe to stdin	
					os.dup2(stdin_r, 0)

					# create and duplicate stdout and stderr to open file handles
					stdout_w = os.open(self.stdout, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
					stderr_w = os.open(self.stderr, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
					os.dup2(stdout_w, 1)
					os.dup2(stderr_w, 2)

					# close any stray file descriptors (within reason)
					try:
						maxfd = os.sysconf("SC_OPEN_MAX")
					except:
						maxfd=256
					for fd in range(3, maxfd):
						try:
							os.close(fd)
						except:
							pass
				
					# execve the process to start it
					arguments = copy.copy(self.arguments)
					arguments.insert(0, os.path.basename(self.command))
					os.execve(self.command, arguments, self.environs)
				else:
					# close the read end of the pipe in the parent
					# and start a thread to write to the write end
					os.close(stdin_r)
					self.__stdin = stdin_w
			except:
				if self.pid == 0: os._exit(os.EX_OSERR)	

		if not self.running() and self.exitStatus == os.EX_OSERR:
			raise ProcessError, "Error creating process %s" % (self.command)


	def setExitStatus(self):
		"""Method to set the exit status of the process.
		
		Returns the new value
		
		"""
		with self.__lock:
			if self.exitStatus is not None: return self.exitStatus
	
			retries = 3
			while retries > 0:	
				try:
					pid, status = os.waitpid(self.pid, os.WNOHANG)
					if pid == self.pid:
						if os.WIFEXITED(status):
							self.exitStatus = os.WEXITSTATUS(status)
						elif os.WIFSIGNALED(status):
							self.exitStatus = os.WTERMSIG(status)
						else:
							self.exitStatus = status
						self._outQueue = None
					retries=0
				except OSError, e:
					if e.errno == errno.ECHILD:
						time.sleep(0.01)
						retries=retries-1
					else:
						retries=0
			
			if self.exitStatus != None:
				if self.__stdin:
					try: os.close(self.__stdin)
					except: pass # just being conservative, should never happen
					self.__stdin = None # MUST not close this more than once

			
			return self.exitStatus


	def stop(self, timeout=TIMEOUTS['WaitForProcessStop']):
		"""Stop a process running.
		
		@raise ProcessError: Raised if an error occurred whilst trying to stop the process
		
		"""
		try:
			with self.__lock:
				if self.exitStatus is not None: return 
				os.kill(self.pid, signal.SIGTERM)
			
			self.wait(timeout=timeout)
		except:
			raise ProcessError, "Error stopping process"


	def signal(self, signal):
		"""Send a signal to a running process. 
	
		@param signal:  The integer signal to send to the process
		@raise ProcessError: Raised if an error occurred whilst trying to signal the process
		
		"""
		try:
			os.kill(self.pid, signal)
		except:
			raise ProcessError, "Error signaling process"



