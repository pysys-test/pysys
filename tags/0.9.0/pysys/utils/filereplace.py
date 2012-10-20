#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2012  M.B.Grieve

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

import os.path, sys, string

from pysys.exceptions import *

def replace(input, output, dict={}, marker=''):
	"""Read an input file, and write to output tailoring the file to replace set keywords with values.

	The replace method reads in the contents of the input file line by line, checks for matches in 
	each line to the keys in the dictionary dict parameter, and replaces each match with the value
	of the dictionary for that key, writing the line to the output file. The marker parameter is a
	character which can be used to denoted keywords in the file to be replaced. For instance, with 
	dict of the form C{{'CATSEAT':'mat', 'DOGSEAT':'hat'}}, marker set to '$', and an input file::
	
	  The cat sat on the $CATSEAT$
	  The dog sat on the $DOGSEAT$
	  
	the ouptut file produced would have the contents::
	  
	  The cat sat on the mat
	  The dog sat on the hat

	@param input: The full path to the input file
	@param output: The full path to the output file with the keywords replaced
	@param dict: A dictionary of key/value pairs to use in the replacement
	@param marker: The character used to mark key words to be replaced (may be the empty string
	               if no characters are used)
	@raises FileNotFoundException: Raised if the input file does not exist
	
	"""
	if not os.path.exists(input):
		raise FileNotFoundException, "unable to find file %s" % (os.path.basename(input))
	else:
		fi = open(input, 'r')
		fo = open(output, 'w')
		for line in fi.readlines():
			for key in dict.keys():
				line = line.replace('%s%s%s'%(marker, key, marker), "%s" % (dict[key]))
			fo.write(line)
		fi.close()
		fo.close()

	
