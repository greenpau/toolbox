#!/usr/bin/python

import os
import sys

home = os.environ['HOME']
sys.path.append(home + "/bin/testbin/pylib")

import shell

class Regress(object):
	def __init__(self, phys_topo, sub_topo, platform, is_iso, eof,
		     pkg_path, rel, suite_name, test_name, repeat):
		self.phys_topo = phys_topo
		self.sub_topo = sub_topo
		self.platform = platform
		self.is_iso = is_iso
		self.eof = eof
		self.pkg_path = pkg_path
		self.useimageStr = "dctor/" + rel + "/latest"
		self.suite_name = suite_name
		self.test_name = test_name
		self.repeat = repeat

	def __get_topoStr(self):
		if (self.sub_topo == "rh7Vxlan") or (self.sub_topo == "ubuntu1404Vxlan") or (self.sub_topo == "ubuntu1404"):
			topoStr = " -physTopology " + self.phys_topo + " -subTopology " + self.sub_topo
		elif (self.sub_topo != "") :
			topoStr = " -subTopology " + self.sub_topo
		else :
			topoStr = " -subTopology dctorOvs"
		return topoStr

	def __get_platformStr(self):
		if (self.platform == "nsg"):
			platformStr = " -physTopology " + self.platform
		else:
			platformStr = " -platform " + self.platform
		return platformStr

	def __get_pkgStr(self):
		if (self.is_iso == True):
			pkgStr = " -useimages " + self.useimageStr + " -vrs " + self.pkg_path + " -checkKernel false"
		else :
			pkgStr = " -useimages " + self.useimageStr + " -altpackages ovs=" + self.pkg_path
		return pkgStr

	def __get_eofStr(self):
		if (self.eof == True):
			eofStr = " -exitOnFailure true "
		else :
			eofStr = ""
		return eofStr

	def __get_suiteStr(self):
		if (self.suite_name == None):
			in_suite = os.environ['in_suite']
		else :
			in_suite = self.suite_name
		if (in_suite != ""):
			suiteStr = " -runSuite " + in_suite
		else:
			suiteStr = ""
		return suiteStr

	def __get_testStr(self):
		if (self.test_name != ""):
			testStr = " -runTest " + self.test_name
		else:
			testStr = ""
		return testStr

	def __get_repeatStr(self):
		if (self.repeat != ""):
			repeatStr = " -repeatList " + self.repeat
		else:
			repeatStr = ""
		return repeatStr

	def getParams(self):
		topoStr = self.__get_topoStr()
		platformStr = self.__get_platformStr()
		pkgStr = self.__get_pkgStr()
		eofStr = self.__get_eofStr()
		suiteStr = self.__get_suiteStr()
		testStr = self.__get_testStr()
		repeatStr = self.__get_repeatStr()
		return topoStr, platformStr, pkgStr, eofStr, suiteStr, testStr, repeatStr

	def exec__(self, cmdstr):
		cmd = cmdstr.split();
		shell.execute_hdr("Running regression cmd", cmd)
