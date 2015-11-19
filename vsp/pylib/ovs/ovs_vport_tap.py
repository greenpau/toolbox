#!/usr/bin/python

import sys
sys.path.append("/usr/local/openvswitch/pylib/system")
sys.path.append("/usr/local/openvswitch/pylib/ovs")
import shell
import net
import ovs_ofproto

class Tap(object):
	def __init__(self, ovs_path, port_type, br, iface, ip, logfd):
		self.ovs_path = ovs_path
		self.port_type = port_type
		self.vsctl_path = ovs_path + "/ovs-vsctl"
		self.br = br
		self.iface = iface
		self.logfd = logfd
		if (ip != "0.0.0.0"):
			self.__create(ip)

	def __init(self, ip):
		self.ip = ip
		self.netmask = "255.255.255.0"
		val = self.ip.split(".")
		self.subnet = val[0] + "." + val[1] + "." + val[2] + "." + "0"
		val = self.ip.split(".")
		self.gw_ip = val[0] + "." + val[1] + "." + val[2] + "." + "1"
		self.mac = net.get_iface_mac(self.iface)

	def __create(self, ip):
		if (self.port_type == "internal"):
			cmd = [ self.vsctl_path, "add-port", self.br,
	       			self.iface, "--", "set", "interface",
				self.iface, "type=internal"]
		else:
			net.add_vlan(self.iface, self.logfd)
			cmd = [ self.vsctl_path, "add-port", self.br,
	       			self.iface ]
		rc = shell.run_cmd("Creating port " + self.iface, cmd,
				   self.logfd);
		self.__init(ip)
		if (rc == 0):
			net.set_iface_ip(self.iface, self.netmask, ip,
					 self.logfd)
			net.route_add(self.iface, ip, self.subnet,
				      self.netmask, self.logfd)

	def reset(self):
		cmd = [ self.vsctl_path, "del-port", self.br,
			self.iface ]
		shell.run_cmd("Deleting port " + self.iface + " on bridge " +
			      self.br, cmd, self.logfd)
		net.del_vlan(self.iface, self.logfd)

	def get_ofp_port(self):
		ofproto = ovs_ofproto.OFProto(self.ovs_path)
		return ofproto.ofp_port(self.br, self.iface)

	def get_subnet(self):
		return self.subnet

	def get_netmask(self):
		return self.netmask

	def get_gw_ip(self):
		return self.gw_ip

	def get_mac(self):
		return self.mac
