#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2019 M.B.Grieve

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

# Contains internal (non-API) utilities for initializing logging

import sys, os, io, locale, logging, threading

# must not import any pysys packages here, as this module's code needs to execute first

PY2 = sys.version_info[0] == 2
binary_type = str if PY2 else bytes

class _UnicodeSafeStreamWrapper(object):
	"""
	Non-public API - for internal use only, may change at any time. 
	
	Wraps a stream, forwarding calls to flush()/close() and ensuring all 
	write() calls are forwarded with either unicode or byte strings 
	(depending on the writebytes argument) but not a mixture, with conversions 
	performed safely replacing invalid characters rather than generating exceptions. 
	
	There is no __del__ implementation to automatically close the stream, 
	to faciliate having multiple wrappers using the same underlying stream. 
	"""
	def __init__(self, underlying, writebytes, encoding=None):
		"""
		@param underlying: the underlying stream. May optionally have an "encoding" field. 
		@param writebytes: if True, bytes are written, if False unicode characters are written. 
		@param encoding: encoding which all written bytes/chars are guaranteed to be present in; 
		if None, will be taken from underlying encoding or getpreferredencoding(). 
		"""
		self.stream = underlying
		# on python 2 stdout.encoding=None if redirected, and falling back on getpreferredencoding is the best we can do
		self.__encoding = encoding or getattr(underlying, 'encoding', None) or locale.getpreferredencoding()
		assert self.__encoding
		self.__writebytes = writebytes
	
	def write(self, s):
		if not s: return
		if self.__writebytes:
			if isinstance(s, binary_type):
				self.stream.write(s) # always safe in python 2 and not supported in python 3
			else:
				self.stream.write(s.encode(self.__encoding, errors='replace'))
		else:
			if isinstance(s, binary_type):
				s = s.decode(self.__encoding, errors='replace')
			# even if it's already a unicode string it could contain characters that aren't supported in this encoding 
			# (e.g. unicode replacement characters - such as the decode above generates - aren't supported by ascii); 
			# so check it round-trips
			s = s.encode(self.__encoding, errors='replace')
			s = s.decode(self.__encoding, errors='replace')
			self.stream.write(s)
				
	def flush(self): 
		if self.stream is None: return
		self.stream.flush()
	
	def close(self): 
		"""
		Flush and close the stream, and prevent any more writes to it. 
		This method is idempotent. 
		"""
		if self.stream is None: return
		self.stream.flush()
		self.stream.close()
		self.stream = None


# class extensions for supporting multi-threaded nature

class ThreadedStreamHandler(logging.StreamHandler):
	"""Stream handler to only log from the creating thread.
	
	Overrides logging.StreamHandler to only allow logging to a stream 
	from the thread that created the class instance and added to the root 
	logger via log.addHandler(ThreadedStreamHandler(stream)).

	This is used to pass log output from the specific test that creates this 
	handler to stdout, either immediately or (when multiple threads are in use) 
	at the end of each test's execution. 
	
	@deprecated: For internal use only, do not use. 
	"""
	def __init__(self, strm=None, streamFactory=None):
		"""Overrides logging.StreamHandler.__init__.
		@param strm: the stream
		@param streamFactory: a function that returns the stream, if strm is not specified. 
		"""
		self.threadId = threading.current_thread().ident
		self.__streamfactory = streamFactory if streamFactory else (lambda:strm)
		logging.StreamHandler.__init__(self, self.__streamfactory())
		
	def emit(self, record):
		"""Overrides logging.StreamHandler.emit."""
		if self.threadId != threading.current_thread().ident: return
		logging.StreamHandler.emit(self, record)

	def _updateUnderlyingStream(self):
		""" Update the stream this handler uses by calling again the stream factory; 
		used only for testing. 
		"""
		assert self.stream # otherwise assigning to it wouldn't do anything
		self.stream = self.__streamfactory()

class ThreadedFileHandler(logging.FileHandler):
	"""File handler to only log from the creating thread.
	
	Overrides logging.FileHandler to only allow logging to file from 
	the thread than created the class instance and added to the root 
	logger via log.addHandler(ThreadFileHandler(filename)).
	
	This is used to pass log output from the specific test 
	that creates this handler to the associated run.log. 

	@deprecated: No longer used, will be removed. 
	"""
	def __init__(self, filename, encoding=None):
		"""Overrides logging.FileHandler.__init__"""
		self.threadId = threading.current_thread().ident
		logging.FileHandler.__init__(self, filename, "a", encoding=self.__streamencoding)

	def emit(self, record):
		"""Overrides logging.FileHandler.emit."""
		if self.threadId != threading.current_thread().ident: return
		# must put formatted messages into the buffer otherwise we lose log level 
		# and (critically) exception tracebacks from the output
		logging.FileHandler.emit(self, record)
		

class ThreadFilter(logging.Filterer):
	"""Filter to disallow log records from the current thread.
	
	Within pysys, logging to standard output is only enabled from the main thread 
	of execution (that in which the test runner class executes). When running with
	more than one test worker thread, logging to file of the test run log is 
	performed through a file handler, which only allows logging from that thread. 
	To disable either of these, use an instance of this class from the thread in 
	question, adding to the root logger via log.addFilter(ThreadFilter()).
	
	"""
	def __init__(self):
		"""Overrides logging.Filterer.__init__"""
		self.threadId = threading.current_thread().ident
		logging.Filterer.__init__(self)
		
	def filter(self, record):
		"""Implementation of logging.Filterer.filter to block from the creating thread."""
		if self.threadId != threading.current_thread().ident: return True
		return False


#####################################

# Initialize Python logging for PySys

# avoids a bug where error handlers using the Python root handler could mess up 
# subsequent logging if no handlers are defined
logging.getLogger().addHandler(logging.NullHandler())

rootLogger = logging.getLogger('pysys')
"""The root logger for logging within PySys."""

log = rootLogger

stdoutHandler = ThreadedStreamHandler(streamFactory=lambda: _UnicodeSafeStreamWrapper(sys.stdout, writebytes=PY2))
"""The handler that sends pysys.* log output from the main thread to stdout, 
including buffered output from completed tests when running in parallel."""


# customize the default logging names for display
logging.addLevelName(50, 'CRIT')
logging.addLevelName(30, 'WARN')
stdoutHandler.setLevel(logging.INFO)
rootLogger.setLevel(logging.DEBUG) # The root logger log level (set to DEBUG as all filtering is done by the handlers).
rootLogger.addHandler(stdoutHandler)

