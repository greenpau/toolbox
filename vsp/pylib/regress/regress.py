#!/usr/bin/python

import os
import sys

sys.path.append("/usr/local/openvswitch/pylib/regress")
sys.path.append("/usr/local/openvswitch/pylib/system")

import shell

class Regress(object):
	usr_global_machine = "strato.us.alcatel-lucent.com"
	def __init__(self, phys_topo, sub_topo, platform, is_iso, eof,
		     pkg_path, vrs_image_path, rel, suite_name, test_name,
		     repeat, custom_gash, vsd_image_path, vsc_image_path,
		     vrs_local_path):
		self.phys_topo = phys_topo
		self.sub_topo = sub_topo
		self.platform = platform
		self.is_iso = is_iso
		self.eof = eof
		self.pkg_path = pkg_path
		self.rel = rel
		self.vrs_image_path = vrs_image_path
		self.vrs_local_path = vrs_local_path
		self.ncpe_files = [ "ncpe_centos7.qcow2",
				    "ncpeimg_" + self.rel + ".0priv.md5",
				    "ncpeimg_" + self.rel + ".0priv.tar",
				    "ncpeimg_" + "USE..md5",
				    "ncpeimg_" + "USE..tar",
		]
		if (vsc_image_path == ""):
			self.vsc_image_path = " -useimages dctor/" + rel + "/current"
		else:
			self.vsc_image_path = " -useimages dctor/" + vsc_image_path
		if (vsd_image_path == ""):
			self.vsd_image_path = " -vsd " + rel + "/current"
		else:
			self.vsd_image_path = " -vsd " + vsd_image_path
		self.suite_name = suite_name
		self.test_name = test_name
		self.repeat = repeat
		self.custom_gash = custom_gash

	def __get_topoStr(self):
		if (self.sub_topo == "rh7Vxlan") or (self.sub_topo == "ubuntu1404Vxlan") or (self.sub_topo == "ubuntu1404"):
			topoStr = " -physTopology " + self.phys_topo + " -subTopology " + self.sub_topo
		elif (self.sub_topo == None):
			# NSG express
			topoStr = " -platform dctor"
		elif (self.sub_topo != "") :
			topoStr = " -subTopology " + self.sub_topo
		else :
			#topoStr = " -subTopology dctorOvsVxlan"
			topoStr = " -subTopology dctorOvs"
		return topoStr

	def __get_platformStr(self):
		if (self.platform == "nsg") or (self.platform == "nsgDpdk"):
			platformStr = " -physTopology " + self.platform
		else:
			#platformStr = " -physTopology stdSixDut -platform " + self.platform
			platformStr = " -platform " + self.platform
		return platformStr

	def __get_pkgStr(self):
		if (self.vrs_image_path != ""):
			pkgStr = self.vsc_image_path + self.vsd_image_path + " -vrs " + self.vrs_image_path
		elif (self.is_iso == True):
			pkgStr = self.vsc_image_path + self.vsd_image_path + " -vrs " + self.pkg_path + " -checkKernel false"
		else :
			#pkgStr = self.vsc_image_path + self.vsd_image_path + " -altpackages ovs=" + self.pkg_path
			pkgStr = self.vsc_image_path + self.vsd_image_path + " -vrs " + self.pkg_path
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

	def __get_customGashStr(self):
		if (self.custom_gash != ""):
			custom_gash_str = " -customRepo " + self.custom_gash
		else:
			custom_gash_str = ""
		return custom_gash_str

	def getParams(self):
		topoStr = self.__get_topoStr()
		platformStr = self.__get_platformStr()
		pkgStr = self.__get_pkgStr()
		eofStr = self.__get_eofStr()
		suiteStr = self.__get_suiteStr()
		testStr = self.__get_testStr()
		repeatStr = self.__get_repeatStr()
		custom_gash_str = self.__get_customGashStr()
		return topoStr, platformStr, pkgStr, eofStr, suiteStr, testStr, repeatStr, custom_gash_str

	def __sync_usr_global(self):
		if (self.vrs_local_path == "") or (self.pkg_path == ""):
			return
		elif ((self.platform != "nsg") and (self.platform != "nsgDpdk")):
			if self.sub_topo == "rh7Vxlan":
				self.__sync_usr_global_el7()
		else:
			self.__sync_usr_global_nsg()
		return

	def __sync_usr_global_el7(self):
		pkg_path_el7 = self.pkg_path + "/el7"
		cmdstr = 'mkdir -p ' + pkg_path_el7
		cmd = cmdstr.split()
		shell.execute_hdr("Creating directory " + pkg_path_el7, cmd)
		for path,dirs,files in os.walk(self.vrs_local_path):
			for f in files:
				src_path = os.path.join(path,f)
				if os.path.exists(src_path) == False:
					continue
		 		dst_path = pkg_path_el7
				cmdstr = 'scp ' + src_path + ' ' + self.usr_global_machine + ':' + dst_path
				cmd = cmdstr.split()
				shell.execute_hdr("Sync " + src_path + " to " + dst_path, cmd)

	def __sync_usr_global_nsg(self):
		pkg_path_ncpe = self.pkg_path + '/ncpe'
		cmdstr = 'mkdir -p ' + pkg_path_ncpe
		cmd = cmdstr.split()
		shell.execute_hdr("Creating directory " + pkg_path_ncpe, cmd)
		pkg_path_ncpe_i = self.pkg_path + '/ncpe-i'
		cmdstr = 'mkdir -p ' + pkg_path_ncpe_i
		cmd = cmdstr.split()
		shell.execute_hdr("Creating directory " + pkg_path_ncpe_i, cmd)
		for file in self.ncpe_files:
		 	src_path = self.vrs_local_path + '/' + file
			if os.path.exists(src_path) == False:
				continue
			if (file.find("qcow2") != -1):
		 		dst_path = pkg_path_ncpe
				cmdstr = 'scp ' + src_path + ' ' + self.usr_global_machine + ':' + dst_path
				cmd = cmdstr.split()
				shell.execute_hdr("Sync " + src_path + " to " + dst_path, cmd)
		 		dst_path = pkg_path_ncpe_i
				cmdstr = 'scp ' + src_path + ' ' + self.usr_global_machine + ':' + dst_path
				cmd = cmdstr.split()
				shell.execute_hdr("Sync " + src_path + " to " + dst_path, cmd)
				continue
			if (file.find("USE") != -1):
		 		dst_path = pkg_path_ncpe_i
			else:
				dst_path = pkg_path_ncpe
			cmdstr = 'scp ' + src_path + ' ' + self.usr_global_machine + ':' + dst_path
			cmd = cmdstr.split()
			shell.execute_hdr("Sync " + src_path + " to " + dst_path, cmd)

	def exec__(self, cmdstr):
		self.__sync_usr_global()
		cmd = cmdstr.split();
		shell.execute_hdr("Running regression cmd", cmd)
