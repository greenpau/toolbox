#!/usr/bin/pytho

import os
import sys

# generic utility classes
sys.path.append("/usr/local/openvswitch/pylib/system")
import logger
from cd import cd
import shell

# DPDK classes
import dpdk_helper
import dpdk_dev

class DPDK_System:
	def __init__(self, home, progname, dpdk_sb):
		self.home = home
		self.progname = progname
		self.dpdk_sb = dpdk_sb
		self.hugetlbfs_mount = "/mnt/huge"
		self.sys_nr_hugepages_file = "/sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages"
		self.proc_nr_hugepages_file = "/proc/sys/vm/nr_hugepages"
		self.dpdk_path = home + "/Linux/src/sandbox/" + dpdk_sb + "/dpdk"
		self.vmxnet3_path =  home + "/Linux/src/sandbox/" + dpdk_sb + "/vmxnet3-usermap-1.1"
		if (os.path.exists(self.dpdk_path + "/tools/pci_unbind.py") == True):
			self.pci_bind_tool = self.dpdk_path + "/tools/pci_unbind.py"
		else:
			self.pci_bind_tool = self.dpdk_path + "/tools/igb_uio_bind.py"

	def __build_dpdk(self, c_flag):
		with cd(self.dpdk_path):
			cmd = [ "make", "uninstall" ]
			shell.run_cmd("Uninstalling DPDK", cmd, self.logfd)
			if c_flag == 1:
				cmd = [ "make",  "config", "T=" + self.tgt]
				shell.run_cmd("Configuring DPDK", cmd,
					      self.logfd)
			cmd = [ "make", "install", "T=" + self.tgt ]
			shell.run_cmd("Building and installing DPDK", cmd,
				      self.logfd)

	def __build_vmxnet3(self):
		with cd(self.vmxnet3_path):
			cmd = [ "make", "clean" ]
			shell.run_cmd("Cleaning up vmxnet3", cmd, self.logfd)
			cmd = [ "make", "all", "T=" + self.tgt,
				"RTE_INCLUDE=" + self.dpdk_path + "/" + self.tgt + "/include" ]
			shell.run_cmd("Building vmxnet3", cmd, self.logfd)

	def build(self, tgt_config, c_flag):
	       	if (tgt_config != "default") and (tgt_config != "ivshmem"):
			print self.progname + ": unknown target configuration"
			return 1
		if (self.dpdk_sb == ""):
			print self.progname + ": missing DPDK sandbox"
			return 1
		logfile, self.tgt = dpdk_helper.set_defaults(self.home,
							     self.progname,
							     tgt_config,
							     "build")
		dpdk_helper.print_defaults(self.tgt, c_flag, self.dpdk_path,
			       		   logfile)
		self.logfd = logger.open_log(logfile)
		self.__build_dpdk(c_flag)
		self.__build_vmxnet3()
		return 0
	
	def status(self):
		if (self.dpdk_sb == ""):
			print self.progname + ": missing DPDK sandbox"
			return 1
		logfile, self.tgt = dpdk_helper.set_defaults(self.home,
							     self.progname, "",
							     "status")
		print "DPDK Environment:"
		dpdk_helper.print_defaults(self.tgt, 0, self.dpdk_path, logfile)

		output = shell.execute_raw("cat " + self.sys_nr_hugepages_file)
		print ""
		print "No of 2MB huge pages reserved for DPDK: " + output

		output = shell.grep("cat /proc/meminfo", "Huge")
		print "Huge Page Memory Map:"
		print output

		output = shell.grep("mount", "hugetlbfs")
		print "Huge TLB Filesystem mount point information:"
		if (output != ""):
			print output
		else:
			print "n/a"

		print "IGB kernel module configuration:"
		output = shell.grep("lsmod", "igb")
		if (output != ""):
			print output
		else:
			print "n/a"

		print "KNI kernel module configuration:"
		output = shell.grep("lsmod", "kni")
		if (output != ""):
			print output
		else:
			print "n/a"

		output = shell.execute_raw(self.pci_bind_tool + " --status")
		print ""
		print "PCI Bind tool status:"
		print output
		return 0

	def __get_device_list(self):
		output = shell.grep(self.pci_bind_tool + " --status",
			       	    "drv=igb_uio").splitlines()
		devices = ""
		n_devices = 0
		for line in output:
			line_tok = line.split(" ")
			devices += line_tok[0]
			devices += "\n"
			n_devices += 1
		return n_devices, devices

	def print_device_list(self):
		n_devices, devices = self.__get_device_list()
		if (n_devices == 0):
			return 0
		print ""
		for device in devices.splitlines():
			output = shell.execute_raw("lspci -nn -s " + device)
			print "lspci of DPDK device " + device + ":"
			print output
		return 0

	def __cleanup_device_list(self):
		n_devices, devices = self.__get_device_list()
		if (n_devices > 0):
			for device in devices.splitlines():
				dpdk_device = dpdk_dev.DPDK_Device(self.home,
							self.progname,
							self.dpdk_sb,
						       	self.logfd, device)
				dpdk_device.cleanup()
		return 0

	def __cleanup_drivers(self):
		cmd = [ "rmmod", "vmxnet3-usermap" ]
		shell.run_cmd("Removing vmxnet3-usermap driver", cmd,
			      self.logfd)
		cmd = [ "rmmod", "igb_uio" ]
		shell.run_cmd("Removing igb_uio driver", cmd, self.logfd)
		cmd = [ "rmmod", "rte_kni" ]
		shell.run_cmd("Removing rte_kni driver", cmd, self.logfd)
		cmd = [ "rmmod", "uio" ]
		shell.run_cmd("Removing uio driver", cmd, self.logfd)

	def __cleanup_processes(self):
		cmd = [ "killall", "-9", "ovs-vswitchd" ]
		shell.run_cmd("Killing ovs-vswitchd", cmd, self.logfd)

	def __cleanup_hugetlbfs(self):
		cmd = [ "umount", "-f", self.hugetlbfs_mount ]
		shell.run_cmd("Unmounting " + self.hugetlbfs_mount, cmd,
			      self.logfd)

	def __modify_huge_pages_procfile(self, n_pages, caption):
		scriptfile = "/tmp/scriptfile"
		scriptfile_fd = open(scriptfile, "w")
		print >> scriptfile_fd, "echo " + str(n_pages) + " > " + self.proc_nr_hugepages_file
		scriptfile_fd.close()
		cmd = [ "sh", scriptfile ]
		shell.run_cmd(caption + " " + self.proc_nr_hugepages_file,
			      cmd, self.logfd)
		os.unlink(scriptfile)

	def __cleanup_huge_pages(self):
		self.__modify_huge_pages_procfile(0, "Cleanup")

	def __cleanup(self):
		print "Cleaning up DPDK Environment:"
		self.__cleanup_device_list()
		self.__cleanup_drivers()
		self.__cleanup_processes()
		self.__cleanup_hugetlbfs()
		self.__cleanup_huge_pages()

	def __setup_drivers(self):
		cmd = [ "modprobe", "uio" ]
		shell.run_cmd("Adding uio driver", cmd, self.logfd)
		cmd = [ "insmod",
	       		self.dpdk_path + "/" + self.tgt + "/kmod/igb_uio.ko" ]
		shell.run_cmd("Adding igb_uio driver", cmd, self.logfd)
		cmd = [ "insmod",
	       		self.dpdk_path + "/" + self.tgt + "/kmod/rte_kni.ko" ]
		shell.run_cmd("Adding rte_kni driver", cmd, self.logfd)
		cmd = [ "insmod",
	       		self.vmxnet3_path + "/vmxnet3-usermap.ko",
	       		"enable_shm=2", "num_rqs=1", "num_tqs=1,1" ]
		shell.run_cmd("Adding vmxnet3-usermap driver", cmd, self.logfd)

	def __setup_devices(self, device_list):
		devices = device_list.split(",")
		for device in devices:
			dpdk_device = dpdk_dev.DPDK_Device(self.home,
							   self.progname,
							   self.dpdk_sb,
							   self.logfd, device)
			dpdk_device.setup()

	def __setup_hugetlbfs(self):
		cmd = [ "mkdir", "-p", self.hugetlbfs_mount ]
		shell.run_cmd("Creating " + self.hugetlbfs_mount, cmd,
			      self.logfd)
		cmd = [ "mount", "-t", "hugetlbfs", "nodev",
	       		self.hugetlbfs_mount ]
		shell.run_cmd("Mounting " + self.hugetlbfs_mount, cmd,
			      self.logfd)

	def __setup_huge_pages(self, n_pages):
		self.__modify_huge_pages_procfile(n_pages, "Setup")

	def __setup(self, n_pages, device_list):
		print "Setting up DPDK Environment:"
		self.__setup_drivers()
		self.__setup_devices(device_list)
		self.__setup_hugetlbfs()
		self.__setup_huge_pages(n_pages)

	def reset(self, tgt_config, n_pages, device_list):
		logfile, self.tgt = dpdk_helper.set_defaults(self.home,
							     self.progname,
							     tgt_config,
							     "init")
		dpdk_helper.print_defaults(self.tgt, 0, self.dpdk_path, logfile)
		self.logfd = logger.open_log(logfile)
		print
		self.__cleanup()
		print
		self.__setup(n_pages, device_list)
		return 0

	def cleanup(self, tgt_config):
		logfile, self.tgt = dpdk_helper.set_defaults(self.home,
							     self.progname,
							     tgt_config,
							     "cleanup")
		dpdk_helper.print_defaults(self.tgt, 0, self.dpdk_path, logfile)
		self.logfd = logger.open_log(logfile)
		self.__cleanup()
		return 0
