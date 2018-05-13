#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2018 M.B.Grieve

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

import copy, logging

from pysys.constants import *

class BaseLogFormatter(logging.Formatter):
	"""Base class for formatting log messages.
	
	This implementation delegates everything to L{logging.Formatter} using the messagefmt and datefmt
	properties. Subclasses may be implemented to provide required customizations, and can be registered
	by specifying classname in the formatter node of the project configuration file.
	"""

	# the key to add to the extra={} dict of a logger call to specify the category
	CATEGORY = 'log_category'

	# the key to add to the extra={} dict of a logger call to specify the arg index for the category
	ARG_INDEX = 'log_arg_index'

	@classmethod
	def tag(cls, category, arg_index=None):
		"""Return  dictionary to tag a string to format with color encodings.

		@param category: The category, as defined in L{ColorLogFormatter.COLOR_CATEGORIES}
		@param arg_index: The index of a string in the format message to color
		@return: A dictionary that can then be used in calls to the logger
		"""
		if arg_index is None: return {cls.CATEGORY:category}
		else: return {cls.CATEGORY:category, cls.ARG_INDEX:arg_index}


	def __init__(self, propertiesDict):
		"""Create an instance of the formatter class.

		The class is constructed with a dictionary of properties, which are configured by providing
		<property name="..." value="..."/> elements or attributes on the formatter node of the project
		configuration file. Entries in the properties should be specific to the class, and removed
		when passing the properties to the super class, which will throw an exception if any unexpected
		options are present
		
		@param propertiesDict: dictionary of formatter-specific options

		"""
		self.name = propertiesDict.pop('name', None)

		super(BaseLogFormatter, self).__init__(
			propertiesDict.pop('messagefmt', DEFAULT_FORMAT),
			propertiesDict.pop('datefmt', None) )
		
		if propertiesDict: raise Exception('Unknown formatter option(s) specified: %s'%', '.join(list(propertiesDict.keys())))


class ColorLogFormatter(BaseLogFormatter):
	"""Formatter supporting colored output to a console.
	
	This implementation supports color coding of messages based on the category of the message,
	and the index of the string in the format encoding. This implementation is the default for
	console output, with the color coding enabled either by the color option on the formatter
	set to true. 
	
	The PYSYS_COLOR environment variable can be set to true or false, overriding any 
	setting specified in the project configuration.
	
	The colors used for each category defined by this class can be overridden 
	by specifying "color:XXX" options, e.g.
	<formatter><property name="color:dumped core" value="YELLOW"/></formatter>

	"""

	# use a lookup map from message "categories" to colors,
	COLOR_CATEGORIES = {
		LOG_WARN:'MAGENTA',
		LOG_ERROR:'RED',
		LOG_TRACEBACK:'RED',
		LOG_DEBUG:'BLUE',
		LOG_FILE_CONTENTS:'BLUE',
		LOG_TEST_DETAILS:'CYAN',
		LOG_TEST_OUTCOMES: 'CYAN',
		LOG_TEST_PROGRESS: 'CYAN',
		LOG_TIMEOUTS: 'MAGENTA',
		LOG_FAILURES: 'RED',
		LOG_PASSES: 'GREEN',
		LOG_SKIPS: 'YELLOW',
		LOG_END:'END',
	}
	
	# by default we use standard ANSI escape sequences, supported by most unix terminals
	COLOR_ESCAPE_CODES = {
		'BLUE': '\033[94m',
		'GREEN':'\033[92m',
		'YELLOW':'\033[93m',
		'RED':'\033[91m',
		'MAGENTA':'\033[95m',
		'CYAN':'\033[96m',
		'WHITE':'\033[97m',
		'BLACK':'\033[30m',
		'END':'\033[0m',
	}


	def __init__(self, propertiesDict):
		"""Create an instance of the formatter class."""

		# extract to override entries in the color map from properties
		for prop in list(propertiesDict.keys()):
			if prop.startswith('color:'):
				self.COLOR_CATEGORIES[prop[len('color:'):].lower()] = propertiesDict.pop(prop).upper()

		self.color = propertiesDict.pop('color','').lower() == 'true'
		if os.getenv('PYSYS_COLOR',None):
			self.color = os.getenv('PYSYS_COLOR').lower() == 'true'
		
		if self.color: self.initColoringLibrary()

		super(ColorLogFormatter, self).__init__(propertiesDict)

		# ensure all outcomes are permitted as possible precedents		
		for outcome in PRECEDENT:
			if LOOKUP[outcome].lower() not in self.COLOR_CATEGORIES:
				self.COLOR_CATEGORIES[LOOKUP[outcome].lower()] = self.COLOR_CATEGORIES[LOG_FAILURES] if outcome in FAILS else self.COLOR_CATEGORIES[LOG_PASSES]
		for cat in self.COLOR_CATEGORIES: assert self.COLOR_CATEGORIES[cat] in self.COLOR_ESCAPE_CODES, cat


	def formatException(self, exc_info):
		"""Format an exception for logging, returning the new value.

		@param exc_info: The exception info
		@return: The formatted message ready for logging

		"""
		return self.colorCategoryToEscapeSequence(LOG_TRACEBACK)+ super(ColorLogFormatter, self).formatException(exc_info) + \
			   self.colorCategoryToEscapeSequence(LOG_END)


	def format(self, record):
		"""Format a log record for logging, returning the new value.

		@param record: The message to be formatted
		@return: The formatted message ready for logging

		"""
		if self.color:
			try:
				cat = getattr(record, self.CATEGORY, None)
				if not cat:
					if record.levelname == 'WARN': cat = LOG_WARN
					elif record.levelname == 'ERROR': cat = LOG_ERROR
					elif record.levelname == 'DEBUG': cat = LOG_DEBUG
				if cat:
					cat = cat.lower()
					record = copy.copy(record)
					i = getattr(record, self.ARG_INDEX, None)
					if i == None or not isinstance(record.args[i], str):
						record.msg = self.colorCategoryToEscapeSequence(cat)+record.msg+self.colorCategoryToEscapeSequence(LOG_END)
					else:
						args = list(record.args)
						args[i] = self.colorCategoryToEscapeSequence(cat)+args[i]+self.colorCategoryToEscapeSequence(LOG_END)
						record.args = tuple(args)
					
			except Exception as e:
				log.debug('Failed to format log message "%s": %s'%(record.msg, repr(e)))

		return super(ColorLogFormatter, self).format(record)


	def colorCategoryToEscapeSequence(self, category):
		""" Return the escape sequence to be used for the specified category of logging output. 
		
		@param category: The category of the log message
		@return: The escape sequence

		"""
		color = self.COLOR_CATEGORIES.get(category, '<%s>'%category)
		return self.COLOR_ESCAPE_CODES.get(color.upper(), '<%s>'%color)


	def initColoringLibrary(self):
		"""Initialize any python library required for ensuring ANSI escape sequences can be processed.

		The default implementation does nothing on Unix but on Windows attempts to load the "Colorama"
		library if is is present.

		"""
		if OSFAMILY=='windows':
			try:
				import colorama
				colorama.init()
			except Exception as e:
				logging.getLogger('pysys.utils.logutils').debug('Failed to load coloring library: %s', repr(e))
			
		# since sys.stdout may be been redirected using the above, we need to change the 
		# stream that our handler points at
		assert stdoutHandler.stream
		stdoutHandler.stream = sys.stdout