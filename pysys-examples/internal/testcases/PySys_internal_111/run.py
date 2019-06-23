import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil, io

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	SUBTESTS = [ # name, args, expectedoutput tests (comma-separated)
	
		# test the --mode/modeincludes options (including the ! syntax for excludes)
		('run-noargs', ['run'], 'Test_WithModes~mode1,Test_WithNoModes'),
		('run-primary', ['run', '--mode', 'PRIMARY'], 'Test_WithModes~mode1,Test_WithNoModes'),
		('run-all', ['run', '--mode', 'ALL'], 'Test_WithModes~mode1,Test_WithModes~mode2,Test_WithModes~mode3,Test_WithNoModes'),
		('run-not-primary', ['run', '--mode', '!PRIMARY'], 'Test_WithModes~mode2,Test_WithModes~mode3'),
		('run-not-mode1', ['run', '--mode', '!mode1,!mode3'], 'Test_WithModes~mode2,Test_WithNoModes'),
		('run-modes-1-3', ['run', '--modeinclude', 'mode1,mode3'], 'Test_WithModes~mode1,Test_WithModes~mode3'),
		('run-primary-and-mode', ['run', '--mode', 'PRIMARY,mode2'], 'Test_WithModes~mode1,Test_WithModes~mode2,Test_WithNoModes'),
		('run-positive-and-negative', ['run', '--mode', 'PRIMARY,mode2,!mode1'], 'Test_WithModes~mode2,Test_WithNoModes'),
		('run-no-modes', ['run', '--mode', ''], 'Test_WithNoModes'),
		('run-not-no-modes', ['run', '--mode', '!'], 'Test_WithModes~mode1,Test_WithModes~mode2,Test_WithModes~mode3'),
		
		# test --modeexcludes
		('run-positive-and-negative-modeexclude', ['run', '--mode', 'PRIMARY', '--mode', 'mode2', '--modeexclude','mode1'], 
			'Test_WithModes~mode2,Test_WithNoModes'),
		('run-not-no-modes-modeexclude', ['run', '--modeexclude', ''], 
			'Test_WithModes~mode1,Test_WithModes~mode2,Test_WithModes~mode3'),
		
		# testid~mode test specs
		('run-standard-spec', ['run', '--mode', 'PRIMARY', '--mode', 'mode2', '--modeexclude','mode1', 'Test_WithNoModes', 'Test_WithModes'], 
			'Test_WithModes~mode2,Test_WithNoModes'),

		('run-mode-spec', ['run', 'Test_WithModes~mode2', 'Test_WithModes~mode3'], 
			'Test_WithModes~mode2,Test_WithModes~mode3'),
		
		# TODO: check for no duplication
		
		# todo: no modes
		# interaction with test ids, and regexes, and suffix matching
		# ensure error handling if someone tries a range spec or similar with a ~
		# todo: decide about case sensitivity
		# check hyphens, dots and other chars in mode strings
	]

	def execute(self):
		shutil.copytree(self.input, self.output+'/test')
		
		# use "pysys run"	to deeply test mode selection and expansion logic
		for subid, args, _ in reversed(self.SUBTESTS):
			runPySys(self, subid, args, workingDir='test')
		
		# finally use "pysys run" to touch-test the above for test execution, 
		# and check correct output dir selection (both relative and absolute) 
		# and multi-cyle behaviour
		
		# TODO; check code coverage
		
	def validate(self):
		for subid, args, expectedids in self.SUBTESTS:
			self.log.info('%s:', subid)
			actualids = self.getExprFromFile(subid+'.out', expr='Id   *: *([^ \n]+)', returnAll=True)
			self.assertThat('%r == %r', expectedids, ','.join(actualids))
			self.assertLineCount(subid+'.out', expr='Test final outcome: *PASSED', condition='==%d'%len(actualids))
			self.log.info('')
		
		#self.assertGrep('run-primary.out', expr=