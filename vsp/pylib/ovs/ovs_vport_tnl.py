#!/usr/bin/python

import shell
import ovs_ofproto

class Tunnel(object):
	def __init__(self, ovs_path, br, tnl_type, tnl_key, tnl_ip, tep_type,
		     logfd):
		self.ovs_path = ovs_path
		self.vsctl_path = ovs_path + "/ovs-vsctl"
		self.appctl_path = ovs_path + "/ovs-appctl"
		self.br = br
		self.tnl_type = tnl_type
		self.tnl_key = tnl_key
		self.tnl_ip = tnl_ip
		self.tep_type = tep_type
		self.logfd = logfd
		if (tnl_key != None):
			self.__set_tnl_iface()
			self.__create()

	def __set_tnl_iface(self):
		if (self.tep_type == "rtep"):
			val = self.tnl_ip.split(".")
			tnl_ip_hex = ("%x" % int(val[0])) + \
				     ("%x" % int(val[1])) + \
				     ("%x" % int(val[2])) + \
				     ("%x" % int(val[3]))
			self.iface = "t" + tnl_ip_hex + self.tnl_key
		else:
			self.iface = self.tep_type + "-" + self.tnl_key

	def __set_tnl_ipstr(self):
		if (self.tep_type == "rtep"):
			return "options:remote_ip=" + self.tnl_ip
		elif (self.tep_type == "ltep"):
			return "options:local_ip=" + self.tnl_ip
		else:
			return ""

	def __set_tnl_keystr(self):
		if (self.tep_type == "rtep"):
			return "options:key=" + self.tnl_key
		elif (self.tep_type == "ltep"):
			return "options:key=" + self.tnl_key
		else:
			return ""

	def __create(self):
		ipstr = self.__set_tnl_ipstr()
		keystr = self.__set_tnl_keystr()
		cmd = [ "sudo", self.vsctl_path, "add-port", self.br,
	       		self.iface, "--", "set", "interface", self.iface,
		       	"type=" + self.tnl_type, ipstr, keystr ]
		rc = shell.run_cmd("Creating tunnel port " + self.iface, cmd,
				   self.logfd);

	def __get_ifaces(self):
		cmd = [ "sudo", self.appctl_path, "dpif/show" ]
		appctl_out = shell.execute(cmd).splitlines()
		ifaces = []
		for line in appctl_out:
			if ((line.find("(vxlan:") < 0) and
			    (line.find("(gre:") < 0) and
			    (line.find("(mpls-gre:") < 0)):
				continue
			line_tok = line.split()
			ifaces.append(line_tok[0])
		return ifaces

	def get_ofp_port(self):
		ofproto = ovs_ofproto.OFProto(self.ovs_path)
		return ofproto.ofp_port(self.br, self.iface)

	def get_tnl_name(self):
		return self.iface

	def destroy(self):
		iface_list = self.__get_ifaces()
		for iface in iface_list:
			if (self.iface != iface):
				continue
			cmd = [ "sudo", self.vsctl_path, "del-port", self.br,
		       		iface ]
			shell.run_cmd("Deleting tunnel port " + iface +
				      " on bridge " + self.br, cmd, self.logfd)

	def reset(self):
		iface_list = self.__get_ifaces()
		for iface in iface_list:
			cmd = [ "sudo", self.vsctl_path, "del-port", self.br,
		       		iface ]
			shell.run_cmd("Deleting tunnel port " + iface +
				      " on bridge " + self.br, cmd, self.logfd)
