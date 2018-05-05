from pysys.utils.logutils import ColorLogFormatter
import logging

class CustomFormatter(ColorLogFormatter):
	def __init__(self, optionsDict, isStdOut):
		self.customprefix = optionsDict.pop('customopt')
		super(CustomFormatter, self).__init__(optionsDict, isStdOut)
		
	def format(self, record):
		result = super(CustomFormatter, self).format(record)
		result = self.customprefix+' isStdOut=%s %s'%(self.isStdOut, result)
		return result