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

"""
Contains implementations of test output writers used to output test results during runtime execution. 

There are currently three kinds of writer, any number of which can be configured in the 
project XML file, and which are enabled under different circumstances according to their babse class: 
- "Record" writers log results only when a test run is started with the --record flag, typically to 
a file or database. Any results writer that does not subclass BaseProgressResultsWriter or 
BaseSummaryResultsWriter is treated as a record writer, although best practice is to 
subclass L{BaseRecordResultsWriter}. 
- "Progress" writers subclass L{BaseProgressResultWriter) and log results as they occur 
during a test run to give an indication of how far and how well the run is progressing, 
and are enabled only when the --progress flag is specified or when the PYSYS_PROGRESS=true 
environment variable is set. If none are explicitly configured in the project XML, 
an instance of the default progress writer L{ConsoleProgressResultsWriter} is used. 
- "Summary" writers subclass L{BaseSummaryResultWriter) and log a summary of results 
at the end of the test run. Summary writers are always enabled regardless of the flags 
specified on the command line. If none are explicitly configured in the project XML, 
an instance of the default summary writer L{ConsoleSummaryResultsWriter} is used. 

There are currently four implementations of record writers distributed with the PySys framework,
namely the L{writer.TextResultsWriter}, the L{writer.XMLResultsWriter}, the
L{writer.JUnitXMLResultsWriter} and the L{writer.CSVResultsWriter}, which all subclass L{BaseResultsWriter}. 

Project configuration of the writers is through the PySys project file using the <writer> tag - multiple writers may
be configured and their individual properties set through the nested <property> tag. Writer
properties are set as attributes to the class through the setattr() function. Custom (site
specific) modules can be created and configured by users of the PySys framework (e.g. to
output test results into a relational database etc), though they must adhere to the interface
demonstrated by the implementations demonstrated here.

The writers are instantiated and invoked by the L{pysys.baserunner.BaseRunner} class
instance. This calls the class constructors of all configured test writers, and then 
the setup (prior to executing the set of tests), processResult (process a test result), 
and cleanup (upon completion of the execution of all tests). The **kwargs method parameter
is used for variable argument passing in the interface methods to allow modification of 
the PySys framework without breaking writer implementations already in existence.

"""

__all__ = ["BaseResultsWriter", "BaseRecordResultsWriter", "BaseSummaryResultsWriter", "BaseProgressResultsWriter", "TextResultsWriter", "XMLResultsWriter", "CSVResultsWriter", "JUnitXMLResultsWriter", "ConsoleSummaryResultsWriter", "ConsoleProgressResultsWriter"]

import logging, time, urlparse, os, stat

from pysys import log
from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.logutils import DefaultPySysLoggingFormatter

from xml.dom.minidom import getDOMImplementation

class BaseResultsWriter(object):
	"""Base class for objects that get notified as and when test results are available and 
	can write them out to a file, to the console or anywhere else, either during execution 
	or at the end. 

	"""
	def __init__(self, logfile=None):
		""" Create an instance of the TextResultsWriter class.

		@param logfile: Optional configuration property specifying a file to store output in. 
		Does not apply to all writers, can be ignored if not needed. 

		"""
		pass


	def setup(self, numTests=0, cycles=1, xargs=None, threads=0, **kwargs):
		""" Called before any tests begin, and after any configuration properties have been 
		set on this object. 

		@param numTests: The total number of tests (cycles*testids) to be executed
		@param cycles: The number of cycles. 
		@param xargs: The runner's xargs
		@param threads: The number of threads used for running tests. 
		@param kwargs: Additional keyword arguments may be added in a future release. 

		"""
		pass


	def cleanup(self, **kwargs):
		""" Called after all tests have finished executing (or been cancelled). 
		
		This is where file headers can be written, and open handles should be closed. 

		@param kwargs: Additional keyword arguments may be added in a future release. 
		"""
		pass

	def processResult(self, testObj, cycle=0, testTime=0, testStart=0, **kwargs):
		""" Called when each test has completed. 
		
		This method is always invoked from the same thread as setup() and cleanup(), even 
		when multiple tests are running in parallel. 

		@param testObj: Reference to an instance of a L{pysys.basetest.BaseTest} class. The writer 
		can extract data from this object but should not store a reference to it. 
		The testObj.descriptor.id indicates the test that ran. 
		@param cycle: The cycle number. These start from 0, so please add 1 to this value before using. 
		@param testTime: Duration of the test in seconds. 
		@param testStart: The time when the test started. 
		@param kwargs: Additional keyword arguments may be added in a future release. 
		"""
		pass

	def processTestStarting(self, testObj, cycle=-1, **kwargs):
		""" Called when a test is just about to begin executing. 

		Note on thread-safety: unlike the other methods on this interface, 
		this is usually executed on a worker thread, so any data structures 
		accessed in this method and others on this class must be synchronized 
		if performing non-atomic operations. 
		
		@param testObj: Reference to an instance of a L{pysys.basetest.BaseTest} class. The writer 
		can extract data from this object but should not store a reference to it. 
		The testObj.descriptor.id indicates the test that ran. 
		@param cycle: The cycle number. These start from 0, so please add 1 to this value before using. 
		@param kwargs: Additional keyword arguments may be added in a future release. 
		"""
		pass

class BaseRecordResultsWriter(BaseResultsWriter):
	"""
	Base class for writers that record the results of tests, 
	and are enabled only when the --record flag is specified. 
	
	For compatibility reasons writers that do not subclass 
	BaseSummaryResultsWriter or BaseProgressResultsWriter are 
	treated as "record" writers even if they do not inherit from 
	this class. 
	"""
	pass


class BaseSummaryResultsWriter(BaseResultsWriter):
	"""
	Base class for writers that display a summary of test results. 
	
	Summary writers are always enabled (regardless of whether 
	--progress or --record are specified). If no "summary" writers 
	are configured, a default ConsoleSummaryResultsWriter instance will be added automatically. 
	"""
	pass

class BaseProgressResultsWriter(BaseResultsWriter):
	"""
	Base class for writers that display progress information 
	while tests are running, which are only enabled if the --progress flag is specified. 
	"""
	pass


class flushfile(): 
	"""Utility class to flush on each write operation - for internal use only.  
	
	"""
	fp=None 
	
	def __init__(self, fp): 
		"""Create an instance of the class. 
		
		@param fp: The file object
		
		"""
		self.fp = fp
	
	def write(self, msg):
		"""Perform a write to the file object.
		
		@param msg: The string message to write. 
		
		"""
		if self.fp is not None:
			self.fp.write(msg) 
			self.fp.flush() 
	
	def seek(self, index):
		"""Perform a seek on the file objet.
		
		"""
		if self.fp is not None: self.fp.seek(index)
	
	def close(self):
		"""Close the file objet.
		
		"""
		if self.fp is not None: self.fp.close()


class TextResultsWriter(BaseRecordResultsWriter):
	"""Class to log results to logfile in text format.
	
	Writing of the test summary file defaults to the working directory. This can be be overridden in the PySys 
	project file using the nested <property> tag on the <writer> tag.
	 
	@ivar outputDir: Path to output directory to write the test summary files
	@type outputDir: string
	
	"""
	outputDir = None
	
	def __init__(self, logfile):
		"""Create an instance of the TextResultsWriter class.
		
		@param logfile: The filename template for the logging of test results
		
		"""	
		self.logfile = time.strftime(logfile, time.gmtime(time.time()))
		self.cycle = -1
		self.fp = None


	def setup(self, **kwargs):
		"""Implementation of the setup method.

		Creates the file handle to the logfile and logs initial details of the date, 
		platform and test host. 
				
		@param kwargs: Variable argument list
		
		"""		
		self.logfile = os.path.join(self.outputDir, self.logfile) if self.outputDir is not None else self.logfile

		self.fp = flushfile(open(self.logfile, "w"))
		self.fp.write('DATE:       %s (GMT)\n' % (time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time())) ))
		self.fp.write('PLATFORM:   %s\n' % (PLATFORM))
		self.fp.write('TEST HOST:  %s\n' % (HOSTNAME))

	def cleanup(self, **kwargs):
		"""Implementation of the cleanup method. 
		
		Flushes and closes the file handle to the logfile.  

		@param kwargs: Variable argument list
				
		"""
		if self.fp: 
			self.fp.write('\n\n\n')
			self.fp.close()
			self.fp = None

			
	def processResult(self, testObj, **kwargs):
		"""Implementation of the processResult method. 
		
		Writes the test id and outcome to the logfile. 
		
		@param testObj: Reference to an instance of a L{pysys.basetest.BaseTest} class
		@param kwargs: Variable argument list
		
		"""
		if "cycle" in kwargs: 
			if self.cycle != kwargs["cycle"]:
				self.cycle = kwargs["cycle"]
				self.fp.write('\n[Cycle %d]:\n'%(self.cycle+1))
		
		self.fp.write("%s: %s\n" % (LOOKUP[testObj.getOutcome()], testObj.descriptor.id))

		
		
class XMLResultsWriter(BaseRecordResultsWriter):
	"""Class to log results to logfile in XML format.
	
	The class creates a DOM document to represent the test output results and writes the DOM to the 
	logfile using toprettyxml(). The outputDir, stylesheet, useFileURL attributes of the class can 
	be over-ridden in the PySys project file using the nested <property> tag on the <writer> tag.
	 
	@ivar outputDir: Path to output directory to write the test summary files
	@type outputDir: string
	@ivar stylesheet: Path to the XSL stylesheet
	@type stylesheet: string
	@ivar useFileURL: Indicates if full file URLs are to be used for local resource references 
	@type useFileURL: string (true | false)
	
	"""
	outputDir = None
	stylesheet = DEFAULT_STYLESHEET
	useFileURL = "false"

	def __init__(self, logfile):
		"""Create an instance of the TextResultsWriter class.
		
		@param logfile: The filename template for the logging of test results
		
		"""
		self.logfile = time.strftime(logfile, time.gmtime(time.time()))
		self.cycle = -1
		self.numResults = 0
		self.fp = None


	def setup(self, **kwargs):
		"""Implementation of the setup method.

		Creates the DOM for the test output summary and writes to logfile. 
						
		@param kwargs: Variable argument list
		
		"""
		self.numTests = kwargs["numTests"] if "numTests" in kwargs else 0 
		self.logfile = os.path.join(self.outputDir, self.logfile) if self.outputDir is not None else self.logfile
		
		try:
			self.fp = flushfile(open(self.logfile, "w"))
		
			impl = getDOMImplementation()
			self.document = impl.createDocument(None, "pysyslog", None)
			stylesheet = self.document.createProcessingInstruction("xml-stylesheet", "href=\"%s\" type=\"text/xsl\"" % (self.stylesheet))
			self.document.insertBefore(stylesheet, self.document.childNodes[0])

			# create the root and add in the status, number of tests and number completed
			self.rootElement = self.document.documentElement
			self.statusAttribute = self.document.createAttribute("status")
			self.statusAttribute.value="running"
			self.rootElement.setAttributeNode(self.statusAttribute)

			self.completedAttribute = self.document.createAttribute("completed")
			self.completedAttribute.value="%s/%s" % (self.numResults, self.numTests)
			self.rootElement.setAttributeNode(self.completedAttribute)
	
			# add the data node
			element = self.document.createElement("timestamp")
			element.appendChild(self.document.createTextNode(time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))))
			self.rootElement.appendChild(element)

			# add the platform node
			element = self.document.createElement("platform")
			element.appendChild(self.document.createTextNode(PLATFORM))
			self.rootElement.appendChild(element)

			# add the test host node
			element = self.document.createElement("host")
			element.appendChild(self.document.createTextNode(HOSTNAME))
			self.rootElement.appendChild(element)

			# add the test host node
			element = self.document.createElement("root")
			element.appendChild(self.document.createTextNode(self.__pathToURL(PROJECT.root)))
			self.rootElement.appendChild(element)

			# add the extra params nodes
			element = self.document.createElement("xargs")
			if "xargs" in kwargs: 
				for key in list(kwargs["xargs"].keys()):
					childelement = self.document.createElement("xarg")
					nameAttribute = self.document.createAttribute("name")
					valueAttribute = self.document.createAttribute("value") 
					nameAttribute.value=key
					valueAttribute.value=kwargs["xargs"][key].__str__()
					childelement.setAttributeNode(nameAttribute)
					childelement.setAttributeNode(valueAttribute)
					element.appendChild(childelement)
			self.rootElement.appendChild(element)
				
			# write the file out
			self.fp.write(self.document.toprettyxml(indent="  "))
		except Exception:
			log.info("caught %s in XMLResultsWriter: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)


	def cleanup(self, **kwargs):
		"""Implementation of the cleanup method. 
		
		Updates the test run status in the DOM, and re-writes to logfile.

		@param kwargs: Variable argument list
				
		"""
		if self.fp: 
			self.fp.seek(0)
			self.statusAttribute.value="complete"
			self.fp.write(self.document.toprettyxml(indent="  "))
			self.fp.close()
			self.fp = None
			
	def processResult(self, testObj, **kwargs):
		"""Implementation of the processResult method. 
		
		Adds the results node to the DOM and re-writes to logfile.
		
		@param testObj: Reference to an instance of a L{pysys.basetest.BaseTest} class
		@param kwargs: Variable argument list
		
		"""	
		self.fp.seek(0)
		
		if "cycle" in kwargs: 
			if self.cycle != kwargs["cycle"]:
				self.cycle = kwargs["cycle"]
				self.__createResultsNode()
		
		# create the results entry
		resultElement = self.document.createElement("result")
		nameAttribute = self.document.createAttribute("id")
		outcomeAttribute = self.document.createAttribute("outcome")  
		nameAttribute.value=testObj.descriptor.id
		outcomeAttribute.value=LOOKUP[testObj.getOutcome()]
		resultElement.setAttributeNode(nameAttribute)
		resultElement.setAttributeNode(outcomeAttribute)

		element = self.document.createElement("outcomeReason")
		element.appendChild(self.document.createTextNode( testObj.getOutcomeReason() ))
		resultElement.appendChild(element)
		
		element = self.document.createElement("timestamp")
		element.appendChild(self.document.createTextNode(time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))))
		resultElement.appendChild(element)

		element = self.document.createElement("descriptor")
		element.appendChild(self.document.createTextNode(self.__pathToURL(testObj.descriptor.file)))
		resultElement.appendChild(element)

		element = self.document.createElement("output")
		element.appendChild(self.document.createTextNode(self.__pathToURL(testObj.output)))
		resultElement.appendChild(element)
		
		self.resultsElement.appendChild(resultElement)
	
		# update the count of completed tests
		self.numResults = self.numResults + 1
		self.completedAttribute.value="%s/%s" % (self.numResults, self.numTests)
				
		# write the file out
		self.fp.write(self.document.toprettyxml(indent="  "))
    	

	def __createResultsNode(self):
		self.resultsElement = self.document.createElement("results")
		cycleAttribute = self.document.createAttribute("cycle")
		cycleAttribute.value="%d"%(self.cycle+1)
		self.resultsElement.setAttributeNode(cycleAttribute)
		self.rootElement.appendChild(self.resultsElement)

    	
	def __pathToURL(self, path):
		try: 
			if self.useFileURL.lower() == "false": return path
		except Exception:
			return path
		else:
			return urlparse.urlunparse(["file", HOSTNAME, path.replace("\\", "/"), "","",""])
	
	
class JUnitXMLResultsWriter(BaseRecordResultsWriter):
	"""Class to log test results in Apache Ant JUnit XML format (one output file per test per cycle). 
	
	@ivar outputDir: Path to output directory to write the test summary files
	@type outputDir: string
	
	"""
	outputDir = None
	
	def __init__(self, logfile):
		"""Create an instance of the TextResultsWriter class.
		
		@param logfile: The (optional) filename template for the logging of test results
		
		"""	
		self.cycle = -1


	def setup(self, **kwargs):	
		"""Implementation of the setup method.

		Creates the output directory for the writing of the test summary files.  
						
		@param kwargs: Variable argument list
		
		"""	
		self.outputDir = os.path.join(PROJECT.root, 'target','pysys-reports') if self.outputDir is None else self.outputDir
		if os.path.exists(self.outputDir): self.purgeDirectory(self.outputDir, True)
		os.makedirs(self.outputDir)
		self.cycles = kwargs.pop('cycles', 0)

		
	def cleanup(self, **kwargs):
		"""Implementation of the cleanup method. 

		@param kwargs: Variable argument list
				
		"""
		pass
			

	def processResult(self, testObj, **kwargs):
		"""Implementation of the processResult method. 
		
		Creates a test summary file in the Apache Ant Junit XML format. 
		
		@param testObj: Reference to an instance of a L{pysys.basetest.BaseTest} class
		@param kwargs: Variable argument list
		
		"""	
		if "cycle" in kwargs: 
			if self.cycle != kwargs["cycle"]:
				self.cycle = kwargs["cycle"]
		
		impl = getDOMImplementation()		
		document = impl.createDocument(None, 'testsuite', None)		
		rootElement = document.documentElement
		attr1 = document.createAttribute('name')
		attr1.value = testObj.descriptor.id
		attr2 = document.createAttribute('tests')
		attr2.value='1'
		attr3 = document.createAttribute('failures')
		attr3.value = '%d'%(int)(testObj.getOutcome() in FAILS)	
		attr4 = document.createAttribute('skipped')	
		attr4.value = '%d'%(int)(testObj.getOutcome() == SKIPPED)		
		rootElement.setAttributeNode(attr1)
		rootElement.setAttributeNode(attr2)
		rootElement.setAttributeNode(attr3)
		rootElement.setAttributeNode(attr4)
		
		# add the testcase information
		testcase = document.createElement('testcase')
		attr1 = document.createAttribute('classname')
		attr1.value = testObj.descriptor.classname
		attr2 = document.createAttribute('name')
		attr2.value = testObj.descriptor.id		   	
		testcase.setAttributeNode(attr1)
		testcase.setAttributeNode(attr2)
		
		# add in failure information if the test has failed
		if (testObj.getOutcome() in FAILS):
			failure = document.createElement('failure')
			attr1 = document.createAttribute('message')
			attr1.value = LOOKUP[testObj.getOutcome()]
			failure.setAttributeNode(attr1)
			failure.appendChild(document.createTextNode( testObj.getOutcomeReason() ))		
						
			stdout = document.createElement('system-out')
			fp = open(os.path.join(testObj.output, 'run.log'))
			stdout.appendChild(document.createTextNode(fp.read()))
			fp.close()
			
			testcase.appendChild(failure)
			testcase.appendChild(stdout)
		rootElement.appendChild(testcase)
		
		# write out the test result
		if self.cycles > 1:
			fp = open(os.path.join(self.outputDir,'TEST-%s.%s.xml'%(testObj.descriptor.id, self.cycle+1)), 'w')
		else:
			fp = open(os.path.join(self.outputDir,'TEST-%s.xml'%(testObj.descriptor.id)), 'w')
		fp.write(document.toprettyxml(indent='	'))
		fp.close()
		

	def purgeDirectory(self, dir, delTop=False):
		for file in os.listdir(dir):
			path = os.path.join(dir, file)
			if PLATFORM in ['sunos', 'linux']:
				mode = os.lstat(path)[stat.ST_MODE]
			else:
				mode = os.stat(path)[stat.ST_MODE]
		
			if stat.S_ISLNK(mode):
				os.unlink(path)
			if stat.S_ISREG(mode):
				os.remove(path)
			elif stat.S_ISDIR(mode):
				self.purgeDirectory(path, delTop=True)

		if delTop: 
			os.rmdir(dir)


class CSVResultsWriter(BaseRecordResultsWriter):
	"""Class to log results to logfile in CSV format.

	Writing of the test summary file defaults to the working directory. This can be be over-ridden in the PySys
	project file using the nested <property> tag on the <writer> tag. The CSV column output is in the form;

	id, title, cycle, startTime, duration, outcome

	@ivar outputDir: Path to output directory to write the test summary files
	@type outputDir: string

	"""
	outputDir = None

	def __init__(self, logfile):
		"""Create an instance of the TextResultsWriter class.

		@param logfile: The filename template for the logging of test results

		"""
		self.logfile = time.strftime(logfile, time.gmtime(time.time()))
		self.fp = None


	def setup(self, **kwargs):
		"""Implementation of the setup method.

		Creates the file handle to the logfile and logs initial details of the date,
		platform and test host.

		@param kwargs: Variable argument list

		"""
		self.logfile = os.path.join(self.outputDir, self.logfile) if self.outputDir is not None else self.logfile

		self.fp = flushfile(open(self.logfile, "w"))
		self.fp.write('id, title, cycle, startTime, duration, outcome\n')


	def cleanup(self, **kwargs):
		"""Implementation of the cleanup method.

		Flushes and closes the file handle to the logfile.

		@param kwargs: Variable argument list

		"""
		if self.fp:
			self.fp.write('\n\n\n')
			self.fp.close()
			self.fp = None


	def processResult(self, testObj, **kwargs):
		"""Implementation of the processResult method.

		Writes the test id and outcome to the logfile.

		@param testObj: Reference to an instance of a L{pysys.basetest.BaseTest} class
		@param kwargs: Variable argument list

		"""
		testStart = kwargs["testStart"] if "testStart" in kwargs else time.time()
		testTime = kwargs["testTime"] if "testTime" in kwargs else 0
		cycle = (kwargs["cycle"]+1) if "cycle" in kwargs else 0

		csv = []
		csv.append(testObj.descriptor.id)
		csv.append('\"%s\"'%testObj.descriptor.title)
		csv.append(str(cycle))
		csv.append((time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(testStart))))
		csv.append(str(testTime))
		csv.append(LOOKUP[testObj.getOutcome()])
		self.fp.write('%s \n' % ','.join(csv))

class ConsoleSummaryResultsWriter(BaseSummaryResultsWriter):
	"""
	Standard 'summary' writer that is used to list a summary of the 
	test results at the end of execution. 
	"""
	def __init__(self, logfile=None):
		self.showOutcomeReason = self.showOutputDir = False # option added in 1.3.0. May soon change the default to True. 
	
	def setup(self, cycles=0, threads=0, **kwargs):
		self.results = {}
		self.startTime = time.time()
		self.duration = 0.0
		for cycle in range(cycles):
			self.results[cycle] = {}
			for outcome in PRECEDENT: self.results[cycle][outcome] = []
		self.threads = threads

	def processResult(self, testObj, cycle=-1, testTime=-1, testStart=-1, **kwargs):
		self.results[cycle][testObj.getOutcome()].append( (testObj.descriptor.id, testObj.getOutcomeReason(), testObj.output ))
		self.duration = self.duration + testTime


	def cleanup(self, **kwargs):
		log = logging.getLogger('pysys.resultssummary')
		log.critical("")
		log.critical(  "Completed test run at:  %s", time.strftime('%A %Y-%m-%d %H:%M:%S %Z', time.localtime(time.time())))
		if self.threads > 1: 
			log.critical("Total test duration (absolute): %.2f secs", time.time() - self.startTime)		
			log.critical("Total test duration (additive): %.2f secs", self.duration)
		else:
			log.critical("Total test duration:    %.2f secs", time.time() - self.startTime)		
		log.critical("")		
		self.printNonPassesSummary(log)
		
	def printNonPassesSummary(self, log):
		showOutcomeReason = str(self.showOutcomeReason).lower() == 'true'
		showOutputDir = str(self.showOutputDir).lower() == 'true'
		
		log.critical("Summary of non passes: ")
		fails = 0
		for cycle in list(self.results.keys()):
			for outcome in list(self.results[cycle].keys()):
				if outcome in FAILS : fails = fails + len(self.results[cycle][outcome])
		if fails == 0:
			log.critical("	THERE WERE NO NON PASSES", extra={DefaultPySysLoggingFormatter.KEY_COLOR_CATEGORY:'passed'})
		else:
			for cycle in list(self.results.keys()):
				cyclestr = ''
				if len(self.results) > 1: cyclestr = '[CYCLE %d] '%(cycle+1)
				for outcome in FAILS:
					for (id, reason, outputdir) in self.results[cycle][outcome]: 
						log.critical("  %s%s: %s ", cyclestr, LOOKUP[outcome], id, extra={DefaultPySysLoggingFormatter.KEY_COLOR_CATEGORY:LOOKUP[outcome].lower()})
						if showOutputDir:
							log.critical("      %s", os.path.normpath(os.path.relpath(outputdir)))
						if showOutcomeReason and reason:
							log.critical("      %s", reason, extra={DefaultPySysLoggingFormatter.KEY_COLOR_CATEGORY:'outcomereason'})


class ConsoleProgressResultsWriter(BaseProgressResultsWriter):
	"""
	Standard 'progress' writer that logs a summary of progress so far to the console, after each test completes. 
	
	"""
	def __init__(self, logfile=None):
		self.recentFailures = 5  # configurable

	def setup(self, cycles=-1, numTests=-1, threads=-1, **kwargs):
		self.cycles = cycles
		self.numTests = numTests
		self.startTime = time.time()

		self.outcomes = {}
		for o in PRECEDENT: self.outcomes[o] = 0
		self._recentFailureReasons = []
		self.threads = threads
		self.inprogress = set() # this is thread-safe for add/remove

	def processTestStarting(self, testObj, cycle=-1, **kwargs):
		self.inprogress.add(self.testToDisplay(testObj, cycle))

	def testToDisplay(self, testObj, cycle):
		id = testObj.descriptor.id
		if self.cycles > 1: id += ' [CYCLE %02d]'%(cycle+1)
		return id

	def processResult(self, testObj, cycle=-1, **kwargs):
		# don't bother if only one test
		if self.numTests == 1: return
		log = logging.getLogger('pysys.resultsprogress')
		
		id = self.testToDisplay(testObj, cycle)
		self.inprogress.remove(id)
		
		outcome = testObj.getOutcome()
		self.outcomes[outcome] += 1
		
		executed = sum(self.outcomes.values())
		
		if outcome in FAILS:
			m = LOOKUP[outcome]+': '+id
			if testObj.getOutcomeReason(): m += ': '+testObj.getOutcomeReason()
			self._recentFailureReasons.append(m)
			self._recentFailureReasons = self._recentFailureReasons[-1*self.recentFailures:] # keep last N
		
		# nb: no need to lock since this always executes on the main thread
		
		timediv = 1
		if time.time()-self.startTime > 60: timediv = 60
		log.info('--- Progress: completed %d/%d = %0.1f%% of tests in %d %s', executed, self.numTests, 100.0*executed/self.numTests, int((time.time()-self.startTime)/timediv), 
			'seconds' if timediv==1 else 'minutes', extra={DefaultPySysLoggingFormatter.KEY_COLOR_CATEGORY:'progress'})
		failednumber = sum([self.outcomes[o] for o in FAILS])
		passed = ', '.join(['%d %s'%(self.outcomes[o], LOOKUP[o]) for o in PRECEDENT if o not in FAILS and self.outcomes[o]>0])
		failed = ', '.join(['%d %s'%(self.outcomes[o], LOOKUP[o]) for o in PRECEDENT if o in FAILS and self.outcomes[o]>0])
		if passed: log.info('      %s (%0.1f%%)', passed, 100.0*(executed-failednumber)/executed, extra={DefaultPySysLoggingFormatter.KEY_COLOR_CATEGORY:'passed'})
		if failed: log.info('      %s', failed, extra={DefaultPySysLoggingFormatter.KEY_COLOR_CATEGORY:'failed'})
		if self._recentFailureReasons:
			log.info('    Recent failures: ', extra={DefaultPySysLoggingFormatter.KEY_COLOR_CATEGORY:'progress'})
			for f in self._recentFailureReasons:
				log.info('      '+f, extra={DefaultPySysLoggingFormatter.KEY_COLOR_CATEGORY:'failed'})
		inprogress = list(self.inprogress)
		if self.threads>1 and inprogress:
			log.info('    Currently executing: %s', ', '.join(sorted(inprogress)), extra={DefaultPySysLoggingFormatter.KEY_COLOR_CATEGORY:'progress'})
		log.info('-'*62, extra={DefaultPySysLoggingFormatter.KEY_COLOR_CATEGORY:'progress'}) 

