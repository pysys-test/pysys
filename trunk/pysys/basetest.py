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

import sys, os, os.path, re, string, time, thread, logging, copy

from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.filecopy import filecopy
from pysys.utils.filegrep import filegrep
from pysys.utils.filediff import filediff
from pysys.utils.filegrep import orderedgrep
from pysys.utils.linecount import linecount
from pysys.process.helper import ProcessWrapper
from pysys.process.monitor import ProcessMonitor
from pysys.manual.ui import ManualTester

log = logging.getLogger('pysys.test')
log.setLevel(logging.NOTSET)


class BaseTest:
	def __init__ (self, input, output, reference, mode, xargs):
		self.input = input
		self.output = output
		self.reference = reference
		self.mode = mode
		self.setKeywordArgs(xargs)
		self.processList = []
		self.monitorList = []
		self.manualTester = None
		self.outcome = []
		self.log = log


	def setKeywordArgs(self, xargs):
		for key in xargs.keys():
			try:
				exec("self.%s = xargs['%s']" % (key, key))
			except:
				pass


	# methods to add to and obtain the test outcome
	def addOutcome(self, outcome):
		self.outcome.append(outcome)


	def getOutcome(self):
		if len(self.outcome) == 0: return NOTVERIFIED
		list = copy.copy(self.outcome)
		list.sort(lambda x, y: cmp(PRECEDENT.index(x), PRECEDENT.index(y)))
		return list[0]


	# test mehtods for execution, validation and cleanup. THe execute and validate methods
	# are abstract and should be implemented by a subclass
	def execute(self):
		raise NotImplementedError, "The execute method of the BaseTest class must be implemented in a subclass"


	def validate(self):
		raise NotImplementedError, "The validate method of the BaseTest class must be implemented in a subclass"


	def cleanup(self):
		if self.manualTester and self.manualTester.running():
			self.stopManualTester()
	
		for monitor in self.monitorList:
			if monitor.running(): monitor.stop()

		for process in self.processList:
			if process.running(): process.stop()


	# process manipulation methods
	def startProcess(self, command, arguments, environs={}, workingDir=None, state=FOREGROUND, timeout=None, stdout=None, stderr=None, displayName=None):
		if workingDir == None: workingDir = r'%s' % self.output
		if displayName == None: displayName = os.path.basename(command)

		try:
			process = ProcessWrapper(command, arguments, environs, workingDir, state, timeout, os.path.join(workingDir, stdout), os.path.join(workingDir, stderr) )
			process.start()
			if state == FOREGROUND:
				log.info("Executed %s in foreground with exit status = %d", displayName, process.exitStatus)
			elif state == BACKGROUND:
				log.info("Started %s in background with process id %d", displayName, process.pid)
		except ProcessError:
			log.info("Unable to start process")
			self.addOutcome(BLOCKED)
		except ProcessTimeout:
			log.info("Process timedout after %d seconds", timeout)
			self.addOutcome(TIMEDOUT)
		else:
			self.processList.append(process)
			return process

		
	def stopProcess(self, process, hard=FALSE):
		if process.running():
			try:
				process.stop(hard)
				log.info("Stopped process with process id %d", process.pid)
			except ProcessError:
				log.info("Unable to start process")
				self.addOutcome(BLOCKED)


	def signalProcess(self, process, signal):
		if process.running():
			try:
				process.signal(signal)
				log.info("Sent %d signal to process with process id %d", signal, process.pid)
			except ProcessError:
				log.info("Unable to start process")
				self.addOutcome(BLOCKED)


	def waitProcess(self, process, timeout):
		try:
			log.info("Waiting %d secs for process with process id %d", timeout, process.pid)
			process.waitProcess(timeout)
		except ProcessTimeout:
			log.info("Unable to wait for process")
			self.addOutcome(TIMEDOUT)


	def startProcessMonitor(self, process, interval, file):
		monitor = ProcessMonitor(process, interval, file)
		try:
			monitor.start()
		except ProcessError:
			self.addOutcome(BLOCKED)
		else:
			self.monitorList.append(monitor)
			return monitor


	def stopProcessMonitor(self, monitor):
		if monitor.running: monitor.stop()


	# methods to control the manual tester user interface
	def startManualTester(self, file, filedir=None, state=FOREGROUND, timeout=TIMEOUTS['ManualTester']):
		if filedir == None: filedir = self.input
	
		if not self.manualTester or self.manualTester.running() == 0:
			self.manualTester = ManualTester(self, os.path.join(filedir, file), os.path.join(self.output, 'manual.log'))
			thread.start_new_thread(self.manualTester.start, ())
		
			if state == FOREGROUND:
				startTime = time.time()
				while self.manualTester.running() == 1:
					currentTime = time.time()
					if currentTime > startTime + timeout:
						self.addOutcome(TIMEDOUT)
						self.manualTester.stop()
						return
					time.sleep(1)
			else:
				time.sleep(1)
		else:
			self.addOutcome(BLOCKED)	


	def stopManualTester(self):
		if self.manualTester and self.manualTester.running():
			self.manualTester.stop()
			time.sleep(1)
		else:
			self.addOutcome(BLOCKED)	


	def waitManualTester(self, timeout=TIMEOUTS['ManualTester']):
		if self.manualTester and self.manualTester.running():
			startTime = time.time()
			while self.manualTester.running() == 1:
				currentTime = time.time()
				if currentTime > startTime + timeout:
					self.addOutcome(TIMEDOUT)
					self.manualTester.stop()
					return
				time.sleep(1)


	# test timing methods. These allow control flow of the test to be set
	# on various conditions i.e. a socket becoming available for connections,
	# a file to exist etc
	def wait(self, interval):
		time.sleep(interval)


	def waitForSocket(self, port, host='localhost', timeout=TIMEOUTS['WaitForSocket']):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
		startTime = time.time()
		while 1:
			try:
				s.connect((host, port))
				break
			except socket.error:
				if timeout:
					currentTime = time.time()
					if currentTime > startTime + timeout:
						break
			time.sleep(0.01)


	def waitForFile(self, filename, timeout=TIMEOUTS['WaitForFile']):
		startTime = time.time()
		while not os.path.exists(filename):
			if timeout:
				currentTime = time.time()
				if currentTime > startTime + timeout:
					break
			time.sleep(0.01)


	def waitForSignal(self, basename, expr, condition="==1", timeout=TIMEOUTS['WaitForSignal'], poll=0.25):
		file = os.path.join(self.output, basename)

		startTime = time.time()
		while 1:
			if os.path.exists(file):
				if eval("%d %s" % (linecount(file, expr), condition)):
					break
				
			currentTime = time.time()
			if currentTime > startTime + timeout:
				break
			time.sleep(poll)


	# test validation methods. These methods provide means to validate the outcome of
	# a test based on the occurrence of regular expressions in text files. All methods
	# directly append to the test outcome list
	def assertTrue(self, expr):
		if expr == TRUE:
			self.addOutcome(PASSED)
			log.info("Assertion on boolean expression equal to true ... passed")
		else:
			self.addOutcome(FAILED)
			log.info("Assertion on boolean expression equal to true ... failed")
	

	def assertFalse(self, expr):
		if expr == FALSE:
			self.addOutcome(PASSED)
			log.info("Assertion on boolean expression equal to true ... passed")
		else:
			self.addOutcome(FAILED)
			log.info("Assertion on boolean expression equal to true ... failed")
	

	def assertDiff(self, file1, file2, filedir1=None, filedir2=None, ignores=[], sort=FALSE, replace=[], includes=[]):
		if filedir1 == None: filedir1 = self.output
		if filedir2 == None: filedir2 = self.reference
		f1 = os.path.join(filedir1, file1)
		f2 = os.path.join(filedir2, file2)

		try:
			result = filediff(f1, f2, ignores, sort, replace, includes)
		except IOError, value:
			self.addOutcome(BLOCKED)
		else:
			if result == TRUE:
				result = PASSED
			else:
				result = FAILED
			self.outcome.append(result)
			log.info("File comparison between %s and %s ... %s", file1, file2, LOOKUP[result].lower())


	def assertGrep(self, file, filedir=None, expr='', contains=TRUE):
		if filedir == None: filedir = self.output
		f = os.path.join(filedir, file)

		try:
			result = filegrep(f, expr)
		except IOError, value:
			self.addOutcome(BLOCKED)
		else:
			if result == contains:
				result = PASSED
			else:
				result = FAILED
			self.outcome.append(result)
			log.info("Grep on input file %s ... %s", file, LOOKUP[result].lower())


	def assertOrderedGrep(self, file, filedir=None, exprList=[], contains=TRUE):   
		if filedir == None: filedir = self.output
		f = os.path.join(filedir, file)

		try:
			result = orderedgrep(f, exprList)
		except IOError, value:
			self.addOutcome(BLOCKED)
		else:
			if result == None and contains:
				result = PASSED
			elif result == None and not contains:
				result = FAILED
			elif result != None and not contains:
				result = PASSED
			else:
				result = FAILED
			self.outcome.append(result)
			log.info("Ordered grep on input file %s ... %s", file, LOOKUP[result].lower())


	def assertLineCount(self, file, filedir=None, expr='', condition="==1"):
		if filedir == None: filedir = self.output
		f = os.path.join(filedir, file)

		try:
			numberLines = linecount(f, expr)
		except IOError, value:
			self.addOutcome(BLOCKED)
		else:
			if (eval("%d %s" % (numberLines, condition))):
				result = PASSED
			else:
				result = FAILED
			self.outcome.append(result)
			log.info("Line count on input file %s ... %s", file, LOOKUP[result].lower())



	
