#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2013  M.B.Grieve

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

try:
	import tkMessageBox
	from Tkinter import *
except:
	pass

from pysys.constants import *
from pysys.exceptions import *
from pysys.xml.manual import *


class ManualTester:
	def __init__(self, owner, filename, logname=None):
		self.owner = owner
		self.isRunning = 1
		self.intToRes = ["FAILED", "PASSED", "N/A"]
		self.logicMap = {"false" : 0, "true" : 1, "" : 1, 0 : "false", 1 : "true"}
		self.filename = filename
		self.steps = self.parseInputXML(self.filename)
		self.currentStep = -1
		self.results = {}
		self.defect = ""

	def build(self):
		self.parentContainer = Tk()
		self.parentContainer.protocol('WM_DELETE_WINDOW', self.quitPressed)
		self.parentContainer.wm_geometry("500x400")
		self.parentContainer.title("PySys Manual Tester - [%s]" % self.owner.descriptor.id)
		self.parentContainer.resizable(True, True)
		self.container = Frame(self.parentContainer)
		self.containerDetails = Frame(self.container)			
		self.titleBox = Label(self.containerDetails, text="Test Title Here", font=("Verdana 10 "), anchor=W, wraplength=480)
		self.titleBox.pack(fill=X)
		self.messageBoxDetails = Text(self.containerDetails, wrap=WORD, width=1, height=1, padx=10, pady=10)
		self.messageBoxDetails.insert(INSERT, "Test Body Here")
		self.messageBoxDetails.pack(fill=BOTH, expand=YES, side=LEFT)
		self.yscrollbarDetails = Scrollbar(self.containerDetails, orient=VERTICAL)
		self.yscrollbarDetails.pack(fill=Y, side=LEFT)
		self.yscrollbarDetails.config(command=self.messageBoxDetails.yview)
		self.containerDetails.pack(fill=BOTH, expand=YES, padx=5, pady=5)
		self.messageBoxDetails.config(yscrollcommand=self.yscrollbarDetails.set, font=("Helvetica 10"))
		self.containerExpected = Frame(self.container)
		self.labelExpected = Label(self.containerExpected, text="Expected Result", font=("Verdana 10"), anchor=W)
		self.labelExpected.pack(fill=X)
		self.messageBoxExpected = Text(self.containerExpected, wrap=WORD, width=1, height=1, padx=10, pady=10)
		self.messageBoxExpected.insert(INSERT, "Test Body Here")
		self.messageBoxExpected.pack(fill=BOTH, expand=YES, side=LEFT)
		self.yscrollbarExpected = Scrollbar(self.containerExpected, orient=VERTICAL)
		self.yscrollbarExpected.pack(fill=Y, side=LEFT)
		self.yscrollbarExpected.config(command=self.messageBoxExpected.yview)
		self.containerExpected.pack(fill=BOTH, expand=YES, padx=5, pady=5)
		self.messageBoxExpected.config(yscrollcommand=self.yscrollbarExpected.set, font=("Helvetica 10"))
		self.container.pack(fill=BOTH, expand=YES, padx=5, pady=5)			
		self.separator = Frame(height=2, bd=1, relief=SUNKEN)
		self.separator.pack(fill=X, pady=2)
		self.inputContainer = Frame(self.parentContainer, relief=GROOVE)
		self.quitButton = Button(self.inputContainer, text="Quit", command=self.quitPressed, pady=5, padx=5, font=("Verdana 9 bold"))
		self.quitButton.pack(side=LEFT, padx=5, pady=5)
		self.backButton = Button(self.inputContainer, text="< Back", command=self.backPressed, state=DISABLED, pady=5, padx=5, font=("Verdana 9 bold"))
		self.backButton.pack(side=LEFT, padx=5, pady=5)
		self.multiButton = Button(self.inputContainer, text="Start", command=self.multiPressed, default=ACTIVE, pady=5, padx=5, font=("Verdana 9 bold"))
		self.multiButton.pack(side=RIGHT, padx=5, pady=5)
		self.failButton = Button(self.inputContainer, text="Fail", command=self.failPressed, pady=5, padx=5, font=("Verdana 9 bold"))
		self.failButton.pack(side=RIGHT, padx=5, pady=5)
		self.inputContainer.pack(fill=X, padx=5, pady=5)
		self.doStep()

	def quitPressed(self):
		self.owner.log.critical("Application terminated by user (BLOCKED)")
		self.owner.outcome.append(BLOCKED)
		self.stop()

	def backPressed(self):
		if self.currentStep >= 0:
			self.currentStep = self.currentStep - 1
			self.doStep()

	def failPressed(self):
		if self.currentStep >= 0:
			self.results[self.currentStep] = 0
			self.currentStep = self.currentStep + 1
			self.doStep()

	def multiPressed(self):
		if self.currentStep == len(self.steps):
			self.stop()
			return
		elif self.currentStep >= 0:
			if self.steps[self.currentStep].validate == 'true':
				self.results[self.currentStep] = 1
			else: self.results[self.currentStep] = 2
		self.currentStep = self.currentStep + 1
		self.doStep()
	
	def doStep(self):
		self.messageBoxDetails.config(state=NORMAL)
		self.messageBoxDetails.delete(1.0, END)
		self.messageBoxExpected.config(state=NORMAL)
		self.messageBoxExpected.delete(1.0, END)
		if self.currentStep < 0:
			self.multiButton.config(text="Start")
			self.backButton.config(state=DISABLED)
			self.failButton.forget()
			self.containerExpected.forget()
			self.messageBoxDetails.insert(INSERT, self.owner.descriptor.purpose)
			self.titleBox.config(text="Title - %s" % self.owner.descriptor.title)
		elif self.currentStep == len(self.steps):
			self.multiButton.config(text="Finish")		
			self.containerExpected.forget()
			self.messageBoxDetails.insert(INSERT, self.reportToString())
			self.titleBox.config(text="Test Complete - Summary Report")
		elif self.currentStep >= 0:
			self.backButton.config(state=NORMAL)
			self.failButton.pack(side=RIGHT, padx=5, pady=5)
			self.multiButton.config(text="Pass")
			self.failButton.config(text="Fail")
			self.messageBoxDetails.insert(INSERT, self.steps[self.currentStep].description)
			expectedResult = self.steps[self.currentStep].expectedResult
			if expectedResult != "":
				self.messageBoxExpected.insert(INSERT, expectedResult)
				self.containerExpected.pack(side=TOP, fill=BOTH, expand=YES, padx=5, pady=5)
			else:
				self.containerExpected.forget()
			self.titleBox.config(text="Step %s of %s - %s" % (self.currentStep + 1, len(self.steps), self.steps[self.currentStep].title))
			if self.steps[self.currentStep].validate == 'false':
				self.multiButton.config(text="Next >")
				self.failButton.forget()
		self.messageBoxDetails.config(state=DISABLED)
		self.messageBoxExpected.config(state=DISABLED)

	def dlgSavePressed(self):
		self.defect = self.dlgTextField.get()
		self.dlg.destroy()

	def dlgNoPressed(self):
		self.dlg.destroy()
		
	def reportToString(self):
		result = ""
		for r in range(len(self.steps)):
			try: 
				result += "\nStep %s - %s: %s" % (r + 1, self.steps[r].title, self.intToRes[self.results[r]])		
			except: pass
		if self.defect != "": result += "\n\nDefect - %s recorded with test failure" % self.defect
		return result

	def logResults(self):
		for r in range(len(self.results)):
			if r < self.currentStep:
				try:
					self.owner.log.info("Step %s - %s: %s" % (r + 1, self.steps[r].title, self.intToRes[self.results[r]]))
					if self.results[r] == 0: self.owner.outcome.append(FAILED)
					elif self.results[r] == 1: self.owner.outcome.append(PASSED)
				except: pass
		if self.defect != "": self.owner.log.info("Defect - %s recorded with test failure" % self.defect)

	def start(self):
		self.build()
		self.parentContainer.mainloop()

	def stop(self):
		self.logResults()
		self.isRunning = 0
		self.parentContainer.quit()
		self.parentContainer.destroy()

	def running(self):
		return self.isRunning

	def parseInputXML(self, input):
		parser = XMLManualTestParser(input)
		steps = parser.getSteps()
		parser.unlink()
		return steps

