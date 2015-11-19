#!/usr/bin/python

import sys
sys.path.append("/usr/local/openvswitch/pylib/system")
import shell

class OFProto(object):
	def __init__(self, ovs_path):
		self.ofctl_path = ovs_path + "/ovs-ofctl"
		self.appctl_path = ovs_path + "/ovs-appctl"
		self.ovs_db_path = "/usr/local/var/run/openvswitch"

	def ofp_port(self, br, port):
		ofp_port_num = 0
		port_info = shell.execute(["sudo", self.ofctl_path,
					   "dump-ports-desc",
					   br]).splitlines()
		for line in port_info:
			if line.find("addr") < 0:
				continue
			lineparts = line.split()
			port_name = lineparts[0]
			if port_name.find(port) < 0:
				continue
			port_tok = port_name.split('(', 1)
			ofp_port_num = port_tok[0]
			break
		return str(ofp_port_num)

	def odp_port(self, port):
		odp_port_num = 0
		cmd = [ "sudo", self.appctl_path, "dpif/show" ]
		dpif_port_show = shell.execute(cmd).splitlines()
		for line in dpif_port_show:
			if (line.find(port) < 0):
				continue
			line_tok = line.split()
			port_str = line_tok[1]
			port_tok = port_str.split('/')
			odp_port_num = port_tok[1]
			break
		return odp_port_num

	def get_bridge(self):
		ovs_vswitchd_pid = shell.get_pid("ovs-vswitchd")
		ovs_vswitchd_target = self.ovs_db_path + "/ovs-vswitchd." + ovs_vswitchd_pid + ".ctl"
		br = shell.execute(["sudo", self.appctl_path, "-t",
				    ovs_vswitchd_target,
				    "ofproto/list"]).splitlines()
		return br[0]
