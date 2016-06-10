#!/usr/bin/python

import sys
import subprocess
import os
import getopt

sys.path.append("/usr/local/openvswitch/pylib/regress")

import regress

class Express(object):
	regress_path = "/usr/global/bin/regress"
	run_level = "express"
	phys_topo = ""
	forcePause = '@@@ Forced paused by sabyasse @@@'
	platform = ""
	test_name = ""
	repeat = ""
	custom_gash = ""
	addl_params = ""

	def __init__(self, testbed, pkg_path, vrs_image_path,
		     phys_topo, sub_topo, rel, platform, is_iso, eof,
		     vsd_image_path, vsc_image_path):
		self.testbed = testbed
		self.pkg_path = pkg_path
		self.vrs_image_path = vrs_image_path
		self.vsd_image_path = vsd_image_path
		self.vsc_image_path = vsc_image_path
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

	def set_custom_gash(self, custom_gash):
		self.custom_gash = custom_gash;

	def set_addl_params(self, addl_params):
		self.addl_params = addl_params

	def run_private(self):
		if (self.suite_name == "Sanity"):
			priorityStr = " -priority P1"
		else:
			priorityStr = " -priority P0"
		r = regress.Regress(self.phys_topo, self.sub_topo,
				    self.platform, self.is_iso, self.eof,
				    self.pkg_path, self.vrs_image_path,
				    self.rel, self.suite_name, self.test_name,
				    self.repeat, self.custom_gash,
				    self.vsd_image_path, self.vsc_image_path)
		topoStr, platformStr, pkgStr, eofStr, suiteStr, testStr, repeatStr, custom_gashStr = r.getParams()
		cmdstr = self.regress_path + " -testbed " + self.testbed + topoStr + platformStr + priorityStr + " -runLevel " + self.run_level + " -forcePause " + self.forcePause + eofStr + pkgStr + suiteStr + testStr + repeatStr + custom_gashStr + self.addl_params
		r.exec__(cmdstr)
