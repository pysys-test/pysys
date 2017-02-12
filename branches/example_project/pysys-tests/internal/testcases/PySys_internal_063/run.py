from pysys.exceptions import *
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.filecopy import filecopy 

class PySysTest(BaseTest):
	def execute(self):
		with open(self.output+'/f1.txt', 'w') as f:
			for i in range(100):
				print >>f, 'f1 line %03d'%(i+1)
		with open(self.output+'/f2.txt', 'w') as f:
			for i in range(5):
				print >>f, 'f2 line %03d'%(i+1)
		
		result = self.logFileContents('does not exist.txt')#
		assert not result
		
		result = self.logFileContents('f1.txt', includes=['.*2\d.*', '.*3\d.*'], excludes=['\d1'])
		assert result
		self.logFileContents(self.output+'/f2.txt', maxLines=2, tail=True, excludes=['\d5'])
		
	def validate(self):
		self.assertGrep('run.log', expr='Contents of f1.txt')
		self.assertGrep('run.log', expr='f1 line 020')
		self.assertGrep('run.log', expr='f1 line 021', contains=False)
		self.assertGrep('run.log', expr='f1 line 039')

		self.assertGrep('run.log', expr='f2 line 003')
		self.assertGrep('run.log', expr='f2 line 001', contains=False)
		self.assertGrep('run.log', expr='f2 line 005', contains=False)
