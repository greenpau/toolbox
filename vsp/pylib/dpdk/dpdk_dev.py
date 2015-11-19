#!/usr/bin/python

import os

# generic utility classes
import sys
sys.path.append("/usr/local/openvswitch/pylib/system")
import logger
from cd import cd
import shell

# DPDK classes
import dpdk_helper

class DPDK_Device:
	def __init__(self, home, progname, dpdk_sb, logfd, device):
		self.home = home
		self.progname = progname
		self.dpdk_sb = dpdk_sb
		self.device = device
		self.logfd = logfd
		self.dpdk_path = home + "/Linux/src/sandbox/" + dpdk_sb + "/dpdk"
		if (os.path.exists(self.dpdk_path + "/tools/pci_unbind.py") == True):
			self.pci_bind_tool = self.dpdk_path + "/tools/pci_unbind.py"
		else:
			self.pci_bind_tool = self.dpdk_path + "/tools/igb_uio_bind.py"
	def cleanup(self):
		cmd = [ self.pci_bind_tool, "-u", self.device ]
		shell.run_cmd("Removing " + self.device, cmd, self.logfd)

	def setup(self):
		output = shell.grep("lspci -k", self.device)
		if (output != ""):
			output = shell.grep("echo " + output, "vmxnet")
			if (output == ""):
				driver = "igb_uio"
			else:
				driver = "vmxnet3-usermap"
		cmd = [ "sudo", self.pci_bind_tool, "--bind=" + driver,
	       		self.device ]
		shell.run_cmd("Setting up " + self.device + " as DPDK device to " + driver, cmd, self.logfd)
