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
		('print-noargs', ['print'], 'Test_WithModes~mode1,Test_WithNoModes'),
		('print-primary', ['print', '--mode', 'PRIMARY'], 'Test_WithModes~mode1,Test_WithNoModes'),
		('print-all', ['print', '--mode', 'ALL'], 'Test_WithModes~mode1,Test_WithModes~mode2,Test_WithModes~mode3,Test_WithNoModes'),
		('print-not-primary', ['print', '--mode', '!PRIMARY'], 'Test_WithModes~mode2,Test_WithModes~mode3'),
		('print-not-mode1', ['print', '--mode', '!mode1,!mode3'], 'Test_WithModes~mode2,Test_WithNoModes'),
		('print-modes-1-3', ['print', '--modeinclude', 'mode1,mode3'], 'Test_WithModes~mode1,Test_WithModes~mode3'),
		('print-primary-and-mode', ['print', '--mode', 'PRIMARY,mode2'], 'Test_WithModes~mode1,Test_WithModes~mode2,Test_WithNoModes'),
		('print-positive-and-negative', ['print', '--mode', 'PRIMARY,mode2,!mode1'], 'Test_WithModes~mode2,Test_WithNoModes'),
		('print-no-modes', ['print', '--mode', ''], 'Test_WithNoModes'),
		('print-not-no-modes', ['print', '--mode', '!'], 'Test_WithModes~mode1,Test_WithModes~mode2,Test_WithModes~mode3'),
		
		# test --modeexcludes
		('print-positive-and-negative-modeexclude', ['print', '--mode', 'PRIMARY', '--mode', 'mode2', '--modeexclude','mode1'], 
			'Test_WithModes~mode2,Test_WithNoModes'),
		('print-not-no-modes-modeexclude', ['print', '--modeexclude', ''], 
			'Test_WithModes~mode1,Test_WithModes~mode2,Test_WithModes~mode3'),
		
		# testid~mode test specs
		('print-standard-spec', ['print', '--mode', 'PRIMARY', '--mode', 'mode2', '--modeexclude','mode1', 'Test_WithNoModes', 'Test_WithModes'], 
			'Test_WithModes~mode2,Test_WithNoModes'),

		('print-mode-spec', ['print', 'Test_WithModes~mode2', 'Test_WithModes~mode3'], 
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
		
		# use "pysys print"	to deeply test mode selection and expansion logic
		for subid, args, _ in reversed(self.SUBTESTS):
			runPySys(self, subid, args, workingDir='test')
		
		# finally use "pysys run" to touch-test the above for test execution, 
		# and check correct output dir selection (both relative and absolute) 
		# and multi-cyle behaviour
		
		# TODO; check code coverage
		
	def validate(self):
		for subid, args, expectedids in self.SUBTESTS:
			self.log.info('%s:', subid)
			actualids = []
			with io.open(self.output+'/'+subid+'.out', encoding='ascii') as f:
				for l in f:
					if ':' in l: l = l.split(':')[0].strip()
					if l.strip(): actualids.append(l.strip())
			self.assertThat('%r == %r', expectedids, ','.join(actualids))
