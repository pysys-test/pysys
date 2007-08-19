from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.process.helper import ProcessWrapper

class PySysTest(BaseTest):

	def execute(self):
		script = "%s/internal/utilities/scripts/counter.py" % self.project.root
	
		self.hprocess = self.startProcess(command=sys.executable,
						  arguments = [script, "2", "-101"],
						  environs = os.environ,
						  workingDir = self.input,
						  stdout = "%s/counter.out" % self.output,
						  stderr = "%s/counter.err" % self.output,
						  state=FOREGROUND)
		
		# do a couple of wait for files
		self.waitForFile('counter.out', timeout=4)
		self.waitForFile('counter.err', timeout=4)
						  
		# do a couple of wait for signals in the files
		self.waitForSignal('counter.out', expr='Count is 1', timeout=4)
		self.waitForSignal('counter.err', expr='Process id of test executable', timeout=4)	

		
	def validate(self):
		# check the sdtout of the process
		self.assertDiff('counter.out', 'ref_counter.out')
		
		# check the stderr of the process
		self.assertGrep('counter.err', expr='Process id of test executable is %d' % self.hprocess.pid)
		
		# check the return status of the process
		self.assertTrue(self.hprocess.exitStatus == -101)
		