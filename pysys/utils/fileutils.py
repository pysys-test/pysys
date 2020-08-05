# -*- coding: latin-1 -*-
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
File and directory handling utility functions such as mkdir and deletedir, with enhanced error handling and 
support for long paths on Windows. Also some simple utilities for loading properties and JSON files. 
"""

import os, shutil, time, locale
import collections
import json

from pysys.constants import IS_WINDOWS
from pysys.utils.pycompat import PY2, openfile

def toLongPathSafe(path, onlyIfNeeded=False):
	"""
	Converts the specified path string to a form suitable for passing to API 
	calls if it exceeds the maximum path length on this OS. 
	
	Currently, this is necessary only on Windows, where a unicode string 
	starting with \\?\ must be used to get correct behaviour for long paths. 
	On Windows this function also normalizes the capitalization of drive 
	letters so they are always upper case regardless of OS version and current 
	working directory. 
	
	:param path: A path. Must not be a relative path. Can be None/empty. Can 
		contain ".." sequences. If possible, use a unicode character string. 
		On Python 2, byte strings are permitted and converted using 
		``locale.getpreferredencoding()``.
	
	:param onlyIfNeeded: Set to True to only adds the long path support if this 
		path exceeds the maximum length on this OS (e.g. 256 chars). You must keep 
		this at False if you will be adding extra characters on to the end of the 
		returned string. 
	
	:return: The passed-in path, possibly with a ``\\?\`` prefix added, 
		forward slashes converted to backslashes on Windows, and converted to 
		a unicode string. Trailing slashes may be removed. 
		Note that the conversion to unicode requires a lot of care on Python 2 
		where byte strings are more common, since it is not possible to combine 
		unicode and byte strings (if they have non-ascii characters), for example 
		for a log statement. 
	
	"""
	if (not IS_WINDOWS) or (not path): return path
	if path[0] != path[0].upper(): path = path[0].upper()+path[1:]
	if onlyIfNeeded and len(path)<255: return path
	if path.startswith(u'\\\\?\\'): 
		if u'/' in path: return path.replace(u'/',u'\\')
		return path
	inputpath = path
	# ".." is not permitted in \\?\ paths; normpath is expensive so don't do this unless we have to
	if '.' in path: 
		path = os.path.normpath(path)
	else:
		# path is most likely to contain / so more efficient to conditionalize this 
		path = path.replace('/','\\')
		if '\\\\' in path:
		# consecutive \ separators are not permitted in \\?\ paths
			path = path.replace('\\\\','\\')

	if PY2 and isinstance(path, str):
		path = path.decode(locale.getpreferredencoding())
	
	if path.startswith(u'\\\\'): 
		path = u'\\\\?\\UNC\\'+path.lstrip('\\') # \\?\UNC\server\share
	else:
		path = u'\\\\?\\'+path
	return path

def fromLongPathSafe(path):
	"""
	Strip off ``\\?\`` prefixes added by L{toLongPathSafe}. 
	
	Note that this function does not convert unicode strings back to byte 
	strings, so if you want a complete reversal of toLongPathSafe you will 
	additionally have to call C{result.encode(locale.getpreferredencoding())}.
	"""
	if not path: return path
	if not path.startswith('\\\\?\\'): return path
	if path.startswith('\\\\?\\UNC\\'):
		result = '\\'+path[7:]
	else:
		result = path[4:]
	return result

def pathexists(path):
	""" Returns True if the specified path is an existing file or directory, 
	as returned by C{os.path.exists}. 
	
	This method is safe to call on paths that may be over the Windows 256 
	character limit. 
	
	:param path: If None or empty, returns True. Only Python 2, can be a 
		unicode or byte string. 
	"""
	return path and os.path.exists(toLongPathSafe(path))

def mkdir(path):
	"""
	Create a directory, with recursive creation of any parent directories.
	
	This function is a no-op (does not throw) if the directory already exists. 

	:return: Returns the path passed in. 
	"""
	origpath = path
	path = toLongPathSafe(path, onlyIfNeeded=True)
	try:
		os.makedirs(path)
	except Exception as e:
		if not os.path.isdir(path):
			# occasionally fails on windows for no reason, so add retry
			time.sleep(0.1)
			os.makedirs(path)
	return origpath

def deletedir(path, retries=1, ignore_errors=False, onerror=None):
	"""
	Recursively delete the specified directory, with optional retries. 
	
	Does nothing if it does not exist. Raises an exception if the deletion fails (unless ``onerror=`` is specified), 
	but deletes as many files as possible before doing so. 
	
	:param retries: The number of retries to attempt. This can be useful to 
		work around temporary failures causes by Windows file locking. 
	
	:param ignore_errors: If True, an exception is raised if the path exists but cannot be deleted. 
	
	:param onerror: A callable that with arguments (function, path, excinfo), called when an error occurs while 
		deleting. See the documentation for ``shutil.rmtree`` for more information. 
	"""
	if ignore_errors: assert onerror==None, 'cannot set onerror and also ignore_errors'
	
	path = toLongPathSafe(path)
	try:
		# delete as many files as we can first, so if there's an error deleting some files (e.g. due to windows file 
		# locking) we don't use any more disk space than we need to
		shutil.rmtree(path, ignore_errors=True)
		
		# then try again, being more careful
		if os.path.exists(path) and not ignore_errors:
			shutil.rmtree(path, onerror=onerror)
	except Exception: # pragma: no cover
		if not os.path.exists(path): return # nothing to do
		if retries <= 0:
			raise
		time.sleep(0.5) # work around windows file-locking issues
		deletedir(path, retries = retries-1, onerror=onerror)

def loadProperties(path, encoding='utf-8-sig'):
	"""
	Reads keys and values from the specified ``.properties`` file. 
	
	Support ``#`` and ``!`` comments but does not perform any special handling of backslash ``\\`` characters 
	(either for escaping or for line continuation). Leading and trailing whitespace around keys and values 
	is stripped. If you need handling of ``\\`` escapes and/or expansion of ``${...}`` placeholders this should be 
	performed manually on the returned values. 
	
	:param str path: The absolute path to the properties file. 
	:param str encoding: The encoding to use (unless running under Python 2 in which case byte strings are always returned). 
		The default is UTF-8 (with optional Byte Order Mark). 
	:return dict[str:str]: An ordered dictionary containing the keys and values from the file. 
	"""
	assert os.path.isabs(path), 'Cannot use relative path: "%s"'%path
	result = collections.OrderedDict()
	with openfile(path, mode='r', encoding=None if PY2 else encoding, errors='strict') as fp:
		for line in fp:
			line = line.lstrip()
			if len(line)==0 or line.startswith(('#','!')): continue
			line = line.split('=', 1)
			if len(line) != 2: continue
			result[line[0].strip()] = line[1].strip()

	return result


def loadJSON(path, **kwargs):
	"""
	Reads JSON from the specified path. 
	
	This is a small wrapper around Python's ``json.load()`` function. 
	
	:param str path: The absolute path to the JSON file, which must be encoded using UTF-8 (with optional Byte Order Mark). 
	:param kwargs: Keyword arguments will be passed to ``json.load()``.
	:return obj: A dict, list, or other Python object representing the contents of the JSON file. 
	"""
	assert os.path.isabs(path), 'Cannot use relative path: "%s"'%path
	with openfile(path, mode='r', encoding='utf-8-sig', errors='strict') as fp:
		return json.load(fp, **kwargs)
		