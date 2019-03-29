import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re, shutil

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		shutil.copytree(self.input, os.path.join(self.output,'test'))

		subtest = 'enabled-defaults'
		runPySys(self, subtest, ['run', '--record', '--threads', '1', '-o', subtest], 
			workingDir='test', ignoreExitStatus=True, environs={'TRAVIS':'true'})

		subtest = 'enabled-printLogsOverride' 
		runPySys(self, subtest, ['run', '--record', '--printLogs', 'all', '--threads', '2', '-o', subtest], 
			workingDir='test', ignoreExitStatus=True, environs={'TRAVIS':'true'})

		subtest = 'default-project' 
		runPySys(self, subtest, ['run', '--record', '--printLogs', 'all', '--threads', '2', '-o', subtest], 
			workingDir='test', ignoreExitStatus=True, environs={'TRAVIS':'true', 
				'PYSYS_PROJECTFILE':PROJECT.testRootDir+'/pysysproject.xml'})

			
	def validate(self):

		for subtest in ['enabled-defaults', 'default-project']:
			self.assertOrderedGrep('%s.out'%subtest, exprList=[
				# first folding, using the test outdir name
				# avoid using the actual literal here else travis will try to fold it!
				'[@t]ravis_fold:[@s]tart:PySys-%s'%subtest,
				'INFO .*Id.*:.*NestedFail',
				'INFO .*Id.*:.*NestedTimedout',
				# end folding before summary
				'[@t]ravis_fold:[@e]nd:PySys-%s'%subtest,
				'Summary of non passes:',
				])

		# this CI provider disables printing of non-failure logs by default
		self.assertGrep('enabled-defaults.out', expr='Id.*:.*NestedPass', contains=False)

		# but can override it explicitly if user wants to
		self.assertGrep('enabled-printLogsOverride.out', expr='Id.*:.*NestedPass', contains=True)

