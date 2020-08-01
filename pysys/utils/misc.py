#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2020 M.B. Grieve

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

"""
Miscellanous utilities such as `pysys.utils.misc.compareVersions` and `pysys.utils.misc.setInstanceVariablesFromDict`.
"""

from pysys.constants import *
from pysys.utils.pycompat import *

__all__ = [
	'setInstanceVariablesFromDict',
	'compareVersions',
]

def compareVersions(v1, v2):
	""" Compares two alphanumeric dotted version strings to see which is more recent. 
	
	See L{pysys.process.user.ProcessUser.compareVersions} for more details. 
	"""
	
	def normversion(v):
		# convert from bytes to strings if necessary
		if isinstance(v, binary_type): v = v.decode('utf-8')
		
		# normalize versions into a list of components, with integers for the numeric bits
		v = [int(x) if x.isdigit() else x for x in re.split(u'([0-9]+|[.])', v.lower().replace('-','.').replace('_','.')) if (x and x != u'.') ]
		
		return v
	
	v1 = normversion(v1)
	v2 = normversion(v2)
	
	# make them the same length
	while len(v1)<len(v2): v1.append(0)
	while len(v1)>len(v2): v2.append(0)

	for i in range(len(v1)):
		if type(v1[i]) != type(v2[i]): # can't use > on different types
			if type(v2[i])==int: # define string>int
				return +1
			else:
				return -1
		else:
			if v1[i] > v2[i]: return 1
			if v1[i] < v2[i]: return -1
	return 0

def setInstanceVariablesFromDict(obj, d, errorOnMissingVariables=False):
	"""
	Sets an instance variable for each item in the specified dictionary, with automatic conversion of 
	bool/int/float/list[str] values from strings if a default value of that type was provided as a static variable on 
	the object. 
	
	.. versionadded:: 1.6.0

	:param object obj: Any Python object. 
	:param dict[str,str] d: The properties to set
	:param bool errorOnMissingVariables: Set this to True if you want an exception to be raised if the dictionary 
		contains a key for which is there no corresponding variable on obj.
	"""
	for key, val in d.items():
		if errorOnMissingVariables and not hasattr(obj, key):
			raise KeyError('Cannot set unexpected property "%s" on %s'%(key, type(obj).__name__))
		defvalue = getattr(obj, key, None)
		if defvalue is not None and isstring(val):
			# attempt type coersion to keep the type the same
			if defvalue is True or defvalue is False:
				if val.lower()=='true': val = True
				elif val.lower()=='false' or val == '': val = False
				else:
					raise Exception('Unexpected value for boolean %s: %s'%(key, repr(val)))
			elif isinstance(defvalue, int):
				val = int(val)
			elif isinstance(defvalue, float):
				val = float(val)
			elif isinstance(defvalue, list):
				val = [val.strip() for val in val.split(',') if val.strip()]
		setattr(obj, key, val)
	