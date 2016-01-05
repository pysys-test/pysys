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

import sys, os, os.path, glob, getopt, sets, re, string, logging

from pysys import rootLogger
from pysys import __version__
from pysys.constants import *
from pysys.exceptions import *
from pysys.launcher import createDescriptors
from pysys.xml.descriptor import DESCRIPTOR_TEMPLATE
from pysys.basetest import TEST_TEMPLATE

EXPR1 = re.compile("^[\w\.]*=.*$")
EXPR2 = re.compile("^[\w\.]*$")
EXPR3 = re.compile("^[\w]*_([0-9]+)$")

consoleLogger = logging.StreamHandler(sys.stdout)
consoleFormatter = logging.Formatter('%(asctime)s %(levelname)-5s %(message)s')
consoleLogger.setFormatter(consoleFormatter)
consoleLogger.setLevel(logging.NOTSET)
rootLogger.addHandler(consoleLogger)

log = logging.getLogger('pysys.launcher.console')
log.setLevel(logging.NOTSET)


class ConsolePrintHelper:
	def __init__(self):
		self.arguments = []
		self.full = FALSE
		self.suites = FALSE
		self.requirements = FALSE
		self.mode = None
		self.type = None
		self.trace = None
		self.includes = []
		self.excludes = []
		self.tests = None
		self.optionString = 'hfsrm:a:t:i:e:'
		self.optionList = ["help","full","suites","requirements","mode=","type=","trace=","include=","exclude="] 
		

	def printUsage(self):
		print "PySys System Test Framework (version %s)" % __version__ 
		print "\nUsage: %s [option]* [tests]*" % os.path.basename(sys.argv[0])
		print "    where options include;"
		print "       -h | --help                 print this message"
		print "       -f | --full                 print full information"
		print "       -s | --suites               print test suites defined"
		print "       -r | --requirements         print test requirements covered"
		print "       -m | --mode      STRING     print tests that run in user defined mode "
		print "       -a | --type      STRING     print tests of supplied type (auto or manual, default all)"
		print "       -t | --trace     STRING     print tests which cover requirement id " 
		print "       -i | --include   STRING     print tests in included suite (can be specified multiple times)"
		print "       -e | --exclude   STRING     do not print tests in excluded suite (can be specified multiple times)"
		print ""
		print "   and where [tests] describes a set of tests to be printed to the console. Note that multiple test "
		print "   sets can be specified, and where none are given all available tests will be run. If an include "
		print "   suite is given, only tests that belong to that suite will be printed. If an exclude suite is given, "
		print "   tests in the suite will not be run. The following syntax is used to select a test set;"
		print ""
		print "       test1    - a single testcase with id test1"
		print "       :test2   - upto testcase with id test2"
		print "       test1:   - from testcase with id test1 onwards"
		print "       id1:id2  - all tests between tests with ids test1 and test2"
		print ""
		print "   e.g. "
		print "       %s -i suite1 -e suite2 --full test1:test3" % os.path.basename(sys.argv[0])
		print ""
		sys.exit()


	def parseArgs(self, args):
		try:
			optlist, self.arguments = getopt.getopt(args, self.optionString, self.optionList)
		except:
			log.warn("Error parsing command line arguments: %s" % (sys.exc_info()[1]))
			sys.exit(1)
			
		for option, value in optlist:
			if option in ("-h", "--help"):
				self.printUsage()

			elif option in ("-f", "--full"):
				self.full = TRUE
				
			if option in ("-s", "--suites"):
				self.suites = TRUE
			
			if option in ("-r", "--requirements"):
				self.requirements = TRUE
				
			elif option in ("-m", "--mode"):
				self.mode = value

			elif option in ("-a", "--type"):
				self.type = value
				if self.type not in ["auto", "manual"]:
					log.warn("Unsupported test type - valid types are auto and manual")
					sys.exit(1)

			elif option in ("-t", "--trace"):
				self.trace = value
				
			elif option in ("-i", "--include"):
				self.includes.append(value)

			elif option in ("-e", "--exclude"):
				self.excludes.append(value)


	def printTests(self):
		descriptors = createDescriptors(self.arguments, self.type, self.includes, self.excludes, self.trace)		

		exit = 0
		if self.suites == TRUE:
			suites = []
			for descriptor in descriptors:
				for suite in descriptor.suites:
					if suite not in suites:
						suites.append(suite)
			print "\nSuites defined: "
			for suite in suites:
				print "                 %s" % (suite)
			exit = 1

		if self.requirements == TRUE:
			requirements = []
			for descriptor in descriptors:
				for requirement in descriptor.traceability:
					if requirement not in requirements:
						requirements.append(requirement)
			print "\nRequirements covered: "
			for requirement in requirements:
				print "                 %s" % (requirement)
			exit = 1
		
		if exit: return
			
		maxsize = 0
		for descriptor in descriptors:
			if len(descriptor.id) > maxsize: maxsize = len(descriptor.id)
		maxsize = maxsize + 2
		
		for descriptor in descriptors:
			padding = " " * (maxsize - len(descriptor.id))
			if not self.full:
				print "%s:%s%s" % (descriptor.id, padding, descriptor.title)
			else:
				print "=========================================="
				print "		" + descriptor.id
				print "=========================================="
				descriptor.toString()



class ConsoleMakeTestHelper:
	def __init__(self, workingDir):
		self.workingDir = workingDir
		self.testId = None
		self.type = "auto"

	def printUsage(self):
		print "PySys System Test Framework (version %s)" % __version__ 
		print "\nUsage: %s [option]+" % os.path.basename(sys.argv[0])
		print "   where the [option] includes;"
		print "       -h | --help                 print this message"
		print "       -n | --nextid               use the next available test id"
		print "       -t | --testid   STRING      the test id to create"
		print "       -a | --type     STRING      set the test type (auto or manual, default is auto)"
		print ""
		print "You must either select the -n flag to create a test with the next availabe id"
		print "or specify the testcase id manually using -t STRING"
		sys.exit()


	def parseArgs(self, args):
		try:
			optlist, arguments = getopt.getopt(args, 'hnt:a:', ["help","nextid","testid=","type="] )
		except:
			print "Error parsing command line arguments: %s" % (sys.exc_info()[1])
			self.printUsage()

		if optlist == []:
			print "Error - you must supply either the -n or -t option to %s ..." % os.path.basename(sys.argv[0])
			self.printUsage()
			sys.exit()
			
		for option, value in optlist:
			if option in ("-h", "--help"):
				self.printUsage()

			elif option in ("-n", "--nextid"):
				self.testId = self.getNextId()				  
				
			elif option in ("-t", "--testid"):
				try:
					self.testId = value
				except:
					print "A valid string must be supplied"
					self.printUsage()

			elif option in ("-a", "--type"):
				self.type = value
				if self.type not in ["auto", "manual"]:
					log.warn("Unsupported test type - valid types are auto and manual")
					sys.exit(1)					

		return self.testId


	def getNextId(self):
		testids = glob.glob(r'%s/[a-zA-Z0-9_]*_[0-9]*' % (self.workingDir))
		testids.sort()
		
		if not testids: return None
		match = re.match('(?P<base>[a-zA-Z0-9_]*_)(?P<number>[0-9]*)', os.path.basename(testids.pop()))
		base = match.group('base')
		number = int(match.group('number')) + 1
		return base + str(number).rjust(3, "0")


	def makeTest(self, input=None, output=None, reference=None, descriptor=None, testclass=None, module=None,
				 suite="", constantsImport=None, basetestImport=None, basetest=None, teststring=None):
		if input==None: input = DEFAULT_INPUT
		if output==None: output = DEFAULT_OUTPUT
		if reference==None: reference = DEFAULT_REFERENCE
		if descriptor==None: descriptor = DEFAULT_DESCRIPTOR
		if testclass==None: testclass = DEFAULT_TESTCLASS
		if module==None: module = DEFAULT_MODULE
		if constantsImport ==None: constantsImport = "from pysys.constants import *"
		if basetestImport == None: basetestImport = "from pysys.basetest import BaseTest"
		if basetest == None: basetest = "BaseTest"
		
		log.info("Creating directory %s ..." % self.testId)
		os.makedirs(self.testId)
		log.info("Creating directory %s ..." % os.path.join(self.testId, input))
		os.makedirs(os.path.join(self.testId, input))
		log.info("Creating directory %s ..." % os.path.join(self.testId, output))
		os.makedirs(os.path.join(self.testId, output))
		log.info("Creating directory %s ..." % os.path.join(self.testId, reference))
		os.makedirs(os.path.join(self.testId, reference))
		
		log.info("Creating descriptor %s ..." % os.path.join(self.testId, descriptor))
		descriptor_fp = open(os.path.join(self.testId, descriptor), "w")
		descriptor_fp.write(DESCRIPTOR_TEMPLATE %(self.type, suite, testclass, module))
		descriptor_fp.close()
		
		log.info("Creating test class module %s ..." % os.path.join(self.testId, "%s.py" % module))	
		testclass_fp = open(os.path.join(self.testId, "%s.py" % module), "w")
		if teststring == None:
			testclass_fp.write(TEST_TEMPLATE % (constantsImport, basetestImport, testclass, basetest))
		else:
			testclass_fp.write(teststring)
		testclass_fp.close()



class ConsoleLaunchHelper:
	def __init__(self):
		self.arguments = []
		self.record = FALSE
		self.purge = FALSE
		self.verbosity = INFO
		self.type = None
		self.trace = None
		self.includes = []
		self.excludes = []
		self.cycle = 1
		self.outsubdir = PLATFORM
		self.mode = None
		self.userOptions = {}
		self.descriptors = []
		self.optionString = 'hrpv:a:t:i:e:c:o:m:X:'
		self.optionList = ["help","record","purge","verbosity=","type=","trace=","include=","exclude=","cycle=","outdir=","mode="]


	def printUsage(self, printXOptions):
		print "PySys System Test Framework (version %s)" % __version__ 
		print "\nUsage: %s [option]* [tests]*" % os.path.basename(sys.argv[0])
		print "   where the [option] includes;"
		print "       -h | --help                 print this message"
		print "       -r | --record               record the test results in the working directory"
		print "       -p | --purge                purge the output subdirectory on test pass"
		print "       -v | --verbosity STRING     set the verbosity level (CRIT, WARN, INFO, DEBUG)"
		print "       -a | --type      STRING     set the test type to run (auto or manual, default is both)" 
		print "       -t | --trace     STRING     set the requirement id for the test run"
		print "       -i | --include   STRING     set the test suites to include (can be specified multiple times)"
		print "       -e | --exclude   STRING     set the test suites to exclude (can be specified multiple times)"
		print "       -c | --cycle     INT        set the the number of cycles to run the tests"
		print "       -o | --outdir    STRING     set the name of the test output subdirectory"
		print "       -m | --mode      STRING     set the user defined mode to run the tests"
		print "       -X               KEY=VALUE  set user defined options to be passed through to the test and "
		print "                                   runner classes. The left hand side string is the data attribute "
		print "                                   to set, the right hand side string the value (TRUE of not specified) "
		if printXOptions: printXOptions()
		print ""
		print "   and where [tests] describes a set of tests to be run. Note that multiple test sets can be specified, "
		print "   where none are given all available tests will be run. If an include suite is given, only tests that "
		print "   belong to that suite will be run. If an exclude suite is given, tests in the suite will not be run. "
		print "   The following syntax is used to select a test set;"
		print ""
		print "       test1    - a single testcase with id test1"
		print "       :test2   - upto testcase with id test2"
		print "       test1:   - from testcase with id test1 onwards"
		print "       id1:id2  - all tests between tests with ids test1 and test2"
		print ""
		print "   e.g. "
		print "       %s -vDEBUG --include MYTESTS test1:test4 test7" % os.path.basename(sys.argv[0])
		print "       %s -c2 -Xhost=localhost test1:" % os.path.basename(sys.argv[0])
		print ""
		sys.exit()


	def parseArgs(self, args, printXOptions=None):
		try:
			optlist, self.arguments = getopt.getopt(args, self.optionString, self.optionList)
		except:
			log.warn("Error parsing command line arguments: %s" % (sys.exc_info()[1]))
			sys.exit(1)

		for option, value in optlist:
			if option in ("-h", "--help"):
				self.printUsage(printXOptions)	  

			elif option in ("-r", "--record"):
				self.record = TRUE

			elif option in ("-p", "--purge"):
				self.purge = TRUE		  

			elif option in ("-v", "--verbosity"):
				self.verbosity = value
				if self.verbosity == "DEBUG":
					rootLogger.setLevel(logging.DEBUG)
				elif self.verbosity == "INFO":
					rootLogger.setLevel(logging.INFO)
				elif self.verbosity == "WARN":
					rootLogger.setLevel(logging.WARN)	
				elif self.verbosity == "CRIT":
					rootLogger.setLevel(logging.CRITICAL)	

			elif option in ("-a", "--type"):
				self.type = value
				if self.type not in ["auto", "manual"]:
					log.warn("Unsupported test type - valid types are auto and manual")
					sys.exit(1)

			elif option in ("-t", "--trace"):
				self.trace = value
									
			elif option in ("-i", "--include"):
				self.includes.append(value)

			elif option in ("-e", "--exclude"):
				self.excludes.append(value)			
						
			elif option in ("-c", "--cycle"):
				try:
					self.cycle = int(value)
				except:
					print "Error parsing command line arguments: A valid integer for the number of cycles must be supplied"
					self.printUsage(printXOptions)

			elif option in ("-o", "--outdir"):
				self.outsubdir = value
					
			elif option in ("-m", "--mode"):
				self.mode = value

			elif option in ("-X"):
				if EXPR1.search(value) != None:
				  exec("self.userOptions['%s'] = '%s'" % (value.split('=')[0], value.split('=')[1]) )
				if EXPR2.search(value) != None:
					exec("self.userOptions['%s'] = %d" % (value, TRUE))


	def runTests(self, runner, printSummary=TRUE, writers=[]):
		descriptors = createDescriptors(self.arguments, self.type, self.includes, self.excludes, self.trace)
		r = runner(self.record, self.purge, self.cycle, self.mode, self.outsubdir, descriptors, self.userOptions)
		r.start(printSummary, writers)
		r.cleanup()
		


