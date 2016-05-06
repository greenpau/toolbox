#!/usr/bin/python

import sys
import time

sys.path.append("/usr/local/openvswitch/pylib/system")
import shell

sys.path.append("/usr/local/openvswitch/pylib/vca")
import vca_mirror
import vca_vm

class DYN(object):
	mirror = None
	def __init__(self, ovs_path, br, logfd, mirror_id, mirror_dst_port,
		     vm_name, agent):
		self.ovs_path = ovs_path
		self.ofctl_path = self.ovs_path + "/ovs-ofctl"
		self.vsctl_path = self.ovs_path + "/ovs-vsctl"
		self.appctl_path = self.ovs_path + "/ovs-appctl"
		self.br = br
		self.logfd = logfd
		self.mirror_id = mirror_id
		self.mirror_dst_port = mirror_dst_port
		self.vm_name = vm_name
		self.agent = agent
		self.__init()
		self.__setup_mirror_dst("Set")

	def __init(self):
		self.vm = vca_vm.VM(self.ovs_path, self.br, None,
				    None, None, None, None, None,
				    None, None, None, self.logfd)
		self.vm.set_vm_name(self.vm_name)
		self.vm_uuid = self.vm.vm_uuid()
		self.port_name = self.vm.port_name()

	def __del__(self):
		self.__setup_mirror_dst("Unset")

	def __setup_mirror_dst(self, action):
		if (action == "Set"):
			cmd = [ self.vsctl_path, "--no-wait", "add-port",
				self.br, self.mirror_dst_port, "--",
				"set", "interface", self.mirror_dst_port,
				"type=internal",
			      ]
			hdrstr = "create mirror destination " + self.mirror_dst_port
		else:
			cmd = [ self.vsctl_path, "--no-wait", "del-port",
				self.br, self.mirror_dst_port
			      ]
			hdrstr = "destroy mirror destination " + self.mirror_dst_port
		shell.run_cmd(hdrstr, cmd, self.logfd)
		time.sleep(1)

	def __setup_vport_mirror(self, action):
		if (action == "Set"):
			if (self.agent == "dpi"):
				cmd = [ self.vsctl_path, "set", "interface",
					self.port_name,
					"other_config:dpi=enable",
					"other_config:dpi-id=" + self.mirror_id,
				      ]
			else:
				cmd = [ self.vsctl_path, "set", "interface",
					self.port_name,
					"other_config:dyn-mirror=enable",
					"other_config:mirror-dst-port=" +
					 self.mirror_dst_port,
					"other_config:mirror-dir=both",
					"other_config:mirror-id=" + self.mirror_id,
				      ]
			hdrstr = "create mirror on vport " + self.port_name + " agent: " + self.agent
		else :
			if (self.agent == "dpi"):
				cmd = [ self.vsctl_path, "set", "interface",
					self.port_name,
					"other_config:dpi=disable",
				      ]
			else:
				cmd = [ self.vsctl_path, "set", "interface",
					self.port_name,
					"other_config:dyn-mirror=disable",
					"other_config:mirror-dst-port=" +
					 self.mirror_dst_port,
					"other_config:mirror-dir=both",
					"other_config:mirror-id=" + self.mirror_id,
				      ]
			hdrstr = "destroy mirror on vport " + self.port_name + " agent: " + self.agent
		shell.run_cmd(hdrstr, cmd, self.logfd)
		time.sleep(1)

	def local_create(self):
		self.__setup_vport_mirror("Set")
		self.mirror = vca_mirror.Mirror(self.ovs_path, self.br,
						self.logfd, "Dyn",
						self.mirror_id)

	def local_destroy(self):
		self.__setup_vport_mirror("Unset")

	def dump(self, to_stdout):
		if (self.mirror != None):
			self.mirror.dump(to_stdout)

	def show(self, to_stdout):
		if (self.mirror != None):
			self.mirror.show(to_stdout)

	def get_destination(self):
		dst_port = None
		if (self.mirror != None):
			dst_port = self.mirror.get_destination()
		return dst_port

	def get_nrefs(self):
		nrefs = None
		if (self.mirror != None):
			nrefs = self.mirror.get_nrefs()
		return nrefs

	def get_port_name(self):
		port_name = None
		if (self.mirror != None):
			port_name = self.mirror.get_port_name()
		return port_name

	def get_internal_name(self):
		int_name = None
		if (self.mirror != None):
			int_name = self.mirror.get_internal_name()
		return int_name

	def get_tunnel_port(self):
		return None, None

	def get_dyn_agent(self):
		agent = None
		if (self.mirror != None):
			agent = self.mirror.get_dyn_agent()
		return agent

	def __parse_dump_flows(self, type, ofp_port, field):
		cmd = [ self.appctl_path, "bridge/dump-flows", self.br ]
		out = shell.execute(cmd).splitlines()
		table_id = -1
		if (type == "Ingress"):
			table_id = 5
		elif (type == "Egress"):
			table_id = 6
		if (table_id == -1):
			return n_packets, n_bytes, None
		val = None
		for l in out:
			this_table_id = str(l.split(",")[0]).split("=")[1]
			if (this_table_id != str(table_id)):
				continue
			if (l.find("create_dyn_mirror") >= 0):
				continue
			toks = l.split()
			rule = toks[5]
			prio = rule.split(",")[0].split("=")[1]
			if (prio != "16384"):
				continue
			in_port = rule.split(",")[2].split("=")[1]
			if (in_port != str(ofp_port)):
				continue
			val = toks[field]
			break
		return val, l

	def get_flow_pkt_counters(self, type, ofp_port):
		n_pkts_str, flow = self.__parse_dump_flows(type, ofp_port, 2)
		if (n_pkts_str == None):
			n_pkts = 0
		else:
			n_pkts = n_pkts_str.replace(",", "").split("=")[1]
		n_bytes_str, flow = self.__parse_dump_flows(type, ofp_port, 4)
		if (n_bytes_str == None):
			n_bytes = 0
		else:
			n_bytes = n_bytes_str.replace(",", "").split("=")[1]
		return int(n_pkts), int(n_bytes), flow

	def get_flow_mirror_actions(self, type, ofp_port):
		rule, flow = self.__parse_dump_flows(type, ofp_port, 5)
		if (rule == None):
			actions = None
		else:
			actions = rule.split("actions=")[1]
		return actions, flow

	def get_flow_mirror_actions_output(self, type, ofp_port):
		actions, flow = self.get_flow_mirror_actions(type, ofp_port)
		output_ofp_port = None
		if (actions != None):
			output_ofp_port = actions.split("output:")[1].split(",")[0]
		return output_ofp_port

	def get_flow_mirror_actions_resub_table(self, type, ofp_port):
		actions, flow = self.get_flow_mirror_actions(type, ofp_port)
		resub_table = None
		if (actions != None):
			resub_table = actions.split("resubmit(,")[1].replace(")", "")
		return resub_table


	def __parse_dpi_show(self, match_pattern, field):
		cmd = [ self.appctl_path, "dpi/show", self.br ]
		out = shell.execute(cmd).splitlines()
		for l in out:
			line_tok = l.split()
			if (line_tok == None) or (line_tok == []):
				continue
			if (l.find(match_pattern) < 0):
				continue
			out = line_tok[field]
			break
		return out

	def get_dpi_port_by_mirror_id(self, mirror_id):
		if (mirror_id == "-"):
			match_pattern = "DPI Engine"
		else:
			match_pattern = "DPI Port"
		return self.__parse_dpi_show(match_pattern, 0)

	def get_dpi_stats_by_mirror_id(self, mirror_id):
		if (mirror_id == "-"):
			match_pattern = "DPI Engine"
		else:
			match_pattern = "DPI Port"
		n_pkts = self.__parse_dpi_show(match_pattern, 4)
		n_bytes = self.__parse_dpi_show(match_pattern, 5)
		return n_pkts, n_bytes
