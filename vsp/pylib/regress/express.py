#!/usr/bin/python

import sys
import subprocess
import os
import getopt

home = os.environ['HOME']
sys.path.append(home + "/bin/testbin/pylib")

import regress

class Express(object):
	regress_path = "/usr/global/bin/regress"
	run_level = "express"
	phys_topo = ""
	forcePause = '@@@ Forced paused by sabyasse @@@'
	platform = ""
	test_name = ""
	repeat = ""

	def __init__(self, testbed, pkg_path, phys_topo, sub_topo, rel,
		     platform, is_iso, eof):
		self.testbed = testbed
		self.pkg_path = pkg_path
		self.phys_topo = phys_topo
		self.sub_topo = sub_topo
		self.rel = rel
		if (platform != None):
			self.platform = platform
		self.is_iso = is_iso
		self.eof = eof

	def set_suite(self, suite_name):
		self.suite_name = suite_name;

	def set_test(self, test_name):
		self.test_name = test_name;

	def set_repeat(self, repeat):
		self.repeat = repeat;

	def run_private(self):
		r = regress.Regress(self.phys_topo, self.sub_topo,
				    self.platform, self.is_iso,
				    self.eof, self.pkg_path, self.rel,
				    self.suite_name, self.test_name,
				    self.repeat)
		topoStr, platformStr, pkgStr, eofStr, suiteStr, testStr, repeatStr = r.getParams()
		cmdstr = self.regress_path + " -testbed " + self.testbed + topoStr + platformStr + " -priority P0 -runLevel " + self.run_level + " -forcePause " + self.forcePause + eofStr + pkgStr + suiteStr + testStr + repeatStr
		r.exec__(cmdstr)
