#!/usr/bin/python

import sys
sys.path.append("/usr/local/openvswitch/pylib/system")

import shell

class VRF(object):
	def __init__(self, ovs_path, br, vrf_id, tnl_type, tnl_key,
		     local_ip, logfd):
		self.ovs_path = ovs_path
		self.ofctl_path = ovs_path + "/ovs-ofctl"
		self.appctl_path = ovs_path + "/ovs-appctl"
		self.br = br
		self.vrf_id = str(vrf_id)
		self.vrf_tnl_type = tnl_type
		self.vrf_tnl_key = str(tnl_key)
		self.local_ip = local_ip
		self.logfd = logfd
		if (vrf_id != 0):
			self.__add_vrf()

	def __add_vrf(self):
		cmd = [ "sudo", self.ofctl_path, "add-vrf", self.br,
	       		self.vrf_id, self.vrf_tnl_key,
		       	"type=" + self.vrf_tnl_type + \
			",local_ip=" + self.local_ip ]
		shell.run_cmd("Creating VRF ID " + self.vrf_id, cmd, self.logfd)

	def show(self):
		cmd = [ "sudo", self.appctl_path, "vrf/show", self.br ]
		shell.execute_hdr("VRF configuration", cmd)

	def list_vrfs(self):
		cmd = [ "sudo", self.appctl_path, "vrf/show", self.br ]
		vrf_show_out = shell.execute(cmd).splitlines()
		vrf_list = []
		for line in vrf_show_out:
			if (line.find("vrf_id") < 0):
				continue
			line_tok = line.split()
			vrf_id = line_tok[1]
			vrf_list.append(vrf_id)
		return vrf_list

	def reset(self):
		vrf_list = self.list_vrfs()
		for vrf_id in vrf_list:
			cmd = [ "sudo", self.ofctl_path, "del-vrf", self.br,
				str(int(str(vrf_id), 16)) ]
			shell.run_cmd("Deleting VRF " + vrf_id,
				      cmd, self.logfd)
