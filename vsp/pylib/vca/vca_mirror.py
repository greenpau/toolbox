#!/usr/bin/python

import sys

sys.path.append("/usr/local/openvswitch/pylib/system")
import shell

sys.path.append("/usr/local/openvswitch/pylib/vca")
import ovs_ofproto

class Mirror(object):
	def __init__(self, ovs_path, br, logfd, mirror_type, mirror_id):
		self.ovs_path = ovs_path
		self.appctl_path = ovs_path + "/ovs-appctl"
		self.br = br
		self.logfd = logfd
		self.mirror_type = mirror_type
		self.mirror_id = mirror_id

	def dump(self, to_stdout):
		cmd = [ self.appctl_path, "bridge/dump-mirrors", self.br ]
		if (to_stdout == True):
			shell.execute_hdr("Mirror configuration", cmd)
		else:
			shell.execute_log(self.logfd, cmd)

	def show(self, to_stdout):
		cmd = [ self.appctl_path, "bridge/show-mirror", self.br,
			self.mirror_id ]
		if (to_stdout == True):
			shell.execute_hdr("Mirror info for " + self.mirror_id,
					  cmd)
		else:
			shell.execute_log(self.logfd, cmd)

	def __parse_show_mirror(self, match_pattern, field):
		cmd = [ self.appctl_path, "bridge/show-mirror", self.br,
			self.mirror_id ]
		mirror_show = shell.execute(cmd).splitlines()
		out = None
		process_this_block = False
		for line in mirror_show:
			line_tok = line.split()
			if (line_tok == None) or (line_tok == []):
				continue
			if (line_tok[0] == self.mirror_id):
				mirror_type = line_tok[2]
				if (mirror_type == self.mirror_type):
					process_this_block = True
				else :
					process_this_block = False
			if (process_this_block == True):
				if (line.find(match_pattern) < 0):
					continue
				out = line_tok[field]
				break
		return out

	def get_port_name(self):
		return self.__parse_show_mirror(self.mirror_id, 3)

	def get_destination(self):
		return self.__parse_show_mirror(self.mirror_id, 6)

	def get_nrefs(self):
		return self.__parse_show_mirror(self.mirror_id, 5)

	def get_dyn_agent(self):
		return self.__parse_show_mirror("Mirror Agent:", 2)

	def get_internal_name(self):
		return self.__parse_show_mirror("Mirror Internal Name:", 3)

	def get_tunnel_port(self):
		mirror_iface = self.__parse_show_mirror("Tunnel Port:", 2)
		mirror_ports_entry = self.__parse_show_mirror("Tunnel Port:", 3)
		if (mirror_ports_entry != None):
			mirror_ports = mirror_ports_entry.replace(")", "").replace("(", "")
		else :
			mirror_ports = None
		return mirror_iface, mirror_ports

	def get_mirror_vport(self, type, col):
		port_name = self.__parse_show_mirror(type, col)
		ofproto = ovs_ofproto.OFProto(self.ovs_path)
		ofp_port = ofproto.ofp_port(self.br, port_name)
		odp_port = ofproto.odp_port(port_name)
		port_nums = ofp_port + "/" + odp_port
		return port_name, port_nums

	def get_mirror_traffic_stats(self):
		n_packets = self.__parse_show_mirror("Mirror Port Cumulative Statistics:", 5).replace(",", "")
		n_bytes = self.__parse_show_mirror("Mirror Port Cumulative Statistics:", 7)
		return n_packets, n_bytes
