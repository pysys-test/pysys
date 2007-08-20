from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.process.helper import ProcessWrapper

class PySysTest(BaseTest):

	def execute(self):
		script = "%s/internal/utilities/scripts/counter.py" % self.project.root
	
		self.hprocess = self.startProcess(command=sys.executable,
						  arguments = [script, "10", "-201"],
						  environs = os.environ,
						  workingDir = self.input,
						  stdout = "%s/counter.out" % self.output,
						  stderr = "%s/counter.err" % self.output,
						  state=BACKGROUND)
						  
		# check the process status
		self.initialstatus = self.hprocess.running()
		
		# wait for the process to complete (after 10 loops)
		self.waitProcess(self.hprocess, timeout=10)
		
		# check the process status
		self.finalstatus = self.hprocess.running()
		
		
	def validate(self):
		# process running status should have been true to start
		self.assertTrue(self.initialstatus)
		
		# process running status should have been false on completion
		self.assertFalse(self.finalstatus)
	
		# check the sdtout of the process
		self.assertDiff('counter.out', 'ref_counter.out')
		
		# check the return status of the process
		self.assertTrue(self.hprocess.exitStatus == -201)