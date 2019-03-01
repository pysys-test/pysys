What is PySys?
==============
PySys is an easy-to-use tool for running and orchestrating all your system, integration, manual and unit tests. 

It provides a comprehensive package of utility methods to make all the common operations a breeze, as well as the flexibility to add whatever test execution and validation logic you need using the full power of the Python language, and without the compilation time and slower development of static/non-scripting languages such as Java/JUnit.

Key features include:

- A comprehensive library of assertion methods appropriate for system-level testing, such as checking for error/success messages in log files and comparing the contents of output files
- A comprehensive library of methods to automate platform-independent process starting, orchestration, and cleanup, for both Windows and Unix-based systems. Includes common operations such as:

  * dynamic port allocation, 
  * waiting until a server is running on a specified port
  * waiting until a file contains a specified message, 
  * aborting early if an error message is detected

- Support for executing tests in parallel to significantly speed up execution time
- A process memory monitoring framework to check for memory leaks
- A performance monitoring framework for recording and aggregating latency, throughput and other performance metrics
- A pluggable "writers" framework for recording test outcomes in any format, including a standard JUnit-compatible XML results writer in the box
- Integrated support for running PyUnit tests
- Integrated support for executing manual interactively driven test cases
- Test categorization and selective include/exclude execution, using per-test classification groups


Download
========
The PySys source package can be downloaded from https://pypi.org. There is also a Windows binary installer available for download on the project page at https://sourceforge.net/projects/pysys/ .

API documentation is available at http://pysys.sourceforge.net/

Installation
============

PySys can be used with Python 2.7 or Python 3.5 and later. 

Dependencies
------------
Running on windows requires installation of the pywin32 extensions written 
by Mark Hammond (http://sourceforge.net/projects/pywin32). 

Those wishing to use the manual tester on unix systems also require the tcl/tk libraries to be installed 
on the host machine and the Python version to be compiled with tcl/tk 
support.


Windows Binary Installation
---------------------------
Installation on windows via the binary distribution bundle is performed by 
downloading the PySys-X.Y.Z.win32.exe installer executable and running. 
Note that a common error on windows is in the execution of the post-install 
script, where an error of the form below is reported::

  close failed in file object destructor:
  sys.excepthook is missing
  lost sys.stderr

If obtained, right click the installer executable in an explorer window, 
and select "Troubleshoot Compatability". Select "Try recommended settings", 
and then "Start the program ...".  


Windows/Unix Source Installation
--------------------------------
To install from source on unix or windows systems you should download the 
source archive and perform the following (use winrar or winzip to unpack 
on windows)::

 $ tar zxvpf PySys-X.Y.Z.tar.gz
 $ cd PySys-X.Y.Z
 $ python setup.py build
 $ python setup.py install
 
To install on both windows and unix systems you may need to have root 
privileges on the machine. 


The 'pysys.py' launcher 
-----------------------
PySys installs a launcher script 'pysys.py' as part of the installation 
process to facilitate the management and execution of testcases. On unix 
systems the script is installed into the Python binary directory, e.g. 
/usr/local/bin, and is hence on the default user's path. On windows systems 
the script is installed into the Scripts directory of the Python 
installation, e.g. c:\Python\Scripts\pysys.py, which is not by default on 
the user's path. To run on windows systems the Scripts directory of the 
Python installation should be added to the user's path to allow direct 
execution of the script. 

After installation, to see the available options to the pysys.py script use::

  $ pysys.py --help
  
The script takes four main top level command line options to it, namely 
'run', 'print', 'make' and 'clean', which are used to run a set of testcases, 
print the meta data for a set of testcases, make a new testcase directory 
structure, or clean all testcase output. For more information on the further 
options available to each add --help after the top level option, e.g.::

  $ pysys.py run --help


Getting Started
===============
PySys comes with a set of simple example testcases to demonstrate its use for running 
automated and manual testcases. 

The samples are distributed in a unix line ending friendly tar.gz archive, and a windows line ending friendly zip file. 
To unpack the tests on unix systems use::

 $ tar zxvpf PySys-examples.X.Y.Z.tar.gz
 $ cd pysys-examples

To run the testcases, after changing directory to the testcases location, 
simply execute::

 $ pysys.py run  


License
=======
PySys is licensed under the GNU LESSER GENERAL PUBLIC LICENSE Version 2.1. 

See pysys-license.txt for details. 
