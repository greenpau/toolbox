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
		self.ofctl_path = ovs_path + "/ovs-ofctl"
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

	def __parse_dump_ports(self, match_pattern, field):
		cmd = [ self.ofctl_path, "dump-ports", self.br ]
		dump_ports = shell.execute(cmd).splitlines()
		out = None
		process_this_block = False
		ofp_port = self.get_ofp_port()
		if (ofp_port < 10):
			portstr = "port  " + ofp_port + ":"
		else:
			portstr = "port " + ofp_port + ":"
		for line in dump_ports:
			line_tok = line.split()
			if (line_tok == None) or (line_tok == []):
				continue
			if (line.find("port") >= 0):
				this_portnum = line_tok[1].replace(":", "")
				if (this_portnum < 10):
					this_portstr = "port  " + line_tok[1]
				else:
					this_portstr = "port " + line_tok[1]
				if (portstr == this_portstr):
					process_this_block = True
				else:
					process_this_block = False
			if (process_this_block == False):
				continue
			if (line.find(match_pattern) < 0):
				continue
			out = line_tok[field]
			break
		return out

	def get_pkt_stats(self):
		tx_n_packets = int(self.__parse_dump_ports("tx", 1).split("=")[1].replace(",", ""))
		tx_n_bytes = int(self.__parse_dump_ports("tx", 2).split("=")[1].replace(",", ""))
		return tx_n_packets, tx_n_bytes
