#!/usr/bin/python

import sys

sys.path.append("/usr/local/openvswitch/pylib/system")
import shell

sys.path.append("/usr/local/openvswitch/pylib/vca")
import vca_flows
import vca_mirror
import vca_vm

class PBM(object):
	mirror = None
	acl_type = None
	acl_dir = None
	def __init__(self, ovs_path, br, logfd, mirror_id, mirror_dst_ip,
		     vm_name):
		self.ovs_path = ovs_path
		self.ofctl_path = self.ovs_path + "/ovs-ofctl"
		self.appctl_path = self.ovs_path + "/ovs-appctl"
		self.br = br
		self.logfd = logfd
		self.mirror_id = mirror_id
		self.mirror_dst_ip = mirror_dst_ip
		self.vm_name = vm_name
		self.__init()

	def __init(self):
		self.vm = vca_vm.VM(self.ovs_path, self.br, None,
				    None, None, None, None, None,
				    None, None, None, self.logfd)
		self.vm.set_vm_name(self.vm_name)
		self.vm_uuid = self.vm.vm_uuid()
		self.port_name = self.vm.port_name()
		self.vm_ofp_port = self.vm.port_ofp_port()
		self.default_flowstr = "priority=0,actions=allow"
		#self.static_flowstr = "priority=0,tcp,in_port=" + self.vm_ofp_port + ",tp_src=100,tp_dst=200,actions=allow"
		self.static_flowstr = "priority=0,ip,in_port=" + self.vm_ofp_port + ",actions=allow"
		self.redirect_flowstr = "priority=0,ip,in_port=" + self.vm_ofp_port + ",actions=9999"
		self.reflexive_flowstr = "stateful=1"
		self.mirror_flowstr = "mirror_id=" + self.mirror_id + ",mirror_dst_ip=" + self.mirror_dst_ip

	def __base_acl_flowstr(self, acl_dir):
		flowstr = "flow_type=acl,flags=" + acl_dir + ",interface=" + self.port_name + ",vm_uuid=" + self.vm_uuid + ",type=vm"
		return flowstr

	def __acl_mirror_flowstr(self, acl_dir):
		flowstr = self.__base_acl_flowstr(acl_dir) + "," + self.mirror_flowstr
		return flowstr

	def __setup_default_acl_mirror_flowstr(self, acl_dir):
		flowstr = self.__acl_mirror_flowstr(acl_dir) + "," + self.default_flowstr
		return flowstr

	def __cleanup_default_acl_mirror_flowstr(self, acl_dir):
		flowstr = self.__base_acl_flowstr(acl_dir) + "," + self.default_flowstr
		return flowstr

	def __setup_static_acl_flowstr(self, acl_dir):
		flowstr = self.__base_acl_flowstr(acl_dir) + "," + self.static_flowstr
		return flowstr

	def __setup_static_acl_mirror_flowstr(self, acl_dir):
		flowstr = self.__acl_mirror_flowstr(acl_dir) + "," + self.static_flowstr
		return flowstr

	def __cleanup_static_acl_mirror_flowstr(self, acl_dir):
		flowstr = self.__base_acl_flowstr(acl_dir) + "," + self.static_flowstr
		return flowstr

	def __setup_redirect_acl_mirror_flowstr(self, acl_dir):
		flowstr = self.__acl_mirror_flowstr(acl_dir) + "," + self.redirect_flowstr
		return flowstr

	def __cleanup_redirect_acl_mirror_flowstr(self, acl_dir):
		flowstr = self.__base_acl_flowstr(acl_dir) + "," + self.static_flowstr
		return flowstr

	def __setup_reflexive_acl_mirror_flowstr(self, acl_dir):
		flowstr = self.__acl_mirror_flowstr(acl_dir) + "," + self.reflexive_flowstr + "," + self.static_flowstr
		return flowstr

	def __cleanup_reflexive_acl_mirror_flowstr(self, acl_dir):
		flowstr = self.__base_acl_flowstr(acl_dir) + "," + self.reflexive_flowstr + "," + self.static_flowstr
		return flowstr

	def __setup_acl_mirror(self, action, acl_type, acl_dir):
		flowstr = None
		table_type = None
		if (acl_type == "redirect") :
			table_type = "redirect"
		elif (acl_dir == "ingress"):
			table_type = "pre"
		elif (acl_dir == "egress"):
			table_type = "post"

		if (table_type == None):
			print "Mirrors for ACL dir " + acl_dir + " not supported yet"
			return

		if (acl_type == "default"):
			if (action == "Set"):
				flowstr = self.__setup_default_acl_mirror_flowstr(table_type)
			else :
				flowstr = self.__cleanup_default_acl_mirror_flowstr(table_type)
		elif (acl_type == "static"):
			if (action == "Set"):
				flowstr = self.__setup_static_acl_mirror_flowstr(table_type)
			else:
				flowstr = self.__cleanup_static_acl_mirror_flowstr(table_type)
		elif (acl_type == "redirect"):
			if (action == "Set"):
				flowstr = self.__setup_static_acl_flowstr("pre")
				cmd = [ self.ofctl_path, "add-flow", self.br, flowstr ]
				hdrstr = action + " " + acl_type + " - " + " Enable ingress ACL"
				shell.run_cmd(hdrstr, cmd, self.logfd)
				flowstr = self.__setup_redirect_acl_mirror_flowstr(table_type)
			else:
				flowstr = self.__cleanup_redirect_acl_mirror_flowstr(table_type)
		elif (acl_type == "reflexive"):
			if (action == "Set"):
				flowstr = self.__setup_reflexive_acl_mirror_flowstr(table_type)
			else:
				flowstr = self.__cleanup_reflexive_acl_mirror_flowstr(table_type)
		if (flowstr == None):
			print "Mirrors for ACL type " + acl_type + " not supported yet"
			return

		cmd = [ self.ofctl_path, "add-flow", self.br, flowstr ]
		if (acl_dir != None):
			hdrstr = action + " " + acl_type + " " + acl_dir + " ACL mirror"
		else:
			hdrstr = action + " " + acl_type + " " + " ACL mirror"
		shell.run_cmd(hdrstr, cmd, self.logfd)

	def local_create(self, acl_type, acl_dir):
		self.acl_type = acl_type
		self.acl_dir = acl_dir
		self.__setup_acl_mirror("Set", acl_type, acl_dir)
		self.mirror = vca_mirror.Mirror(self.ovs_path, self.br,
						self.logfd, "ACL",
						self.mirror_id)

	def local_destroy(self):
		if (self.acl_type != None and self.acl_dir != None):
			self.__setup_acl_mirror("Unset", self.acl_type, self.acl_dir)

	def dump(self, to_stdout):
		if (self.mirror != None):
			self.mirror.dump(to_stdout)

	def show(self, to_stdout):
		if (self.mirror != None):
			self.mirror.show(to_stdout)

	def get_dst_ip(self):
		dst_ip = None
		if (self.mirror != None):
			dst_ip = self.mirror.get_dst_ip()
		return dst_ip

	def get_nrefs(self):
		nrefs = None
		if (self.mirror != None):
			nrefs = self.mirror.get_nrefs()
		return nrefs

	def get_internal_name(self):
		nrefs = None
		if (self.mirror != None):
			nrefs = self.mirror.get_internal_name()
		return nrefs

	def get_mirror_flow_attrs(self):
		flows = vca_flows.Flows(self.ovs_path, self.br, self.logfd)
		flows_out = flows.get_mirror_flows().splitlines()
		mirror_attrs = []
		for flow in flows_out:
			tokens = flow.split()
			if (tokens == None) or (len(tokens) < 19):
				continue
       			mirror = tokens[18].split("=")[1].replace("{", "").replace("}", "")
			if (mirror == None):
				continue
			flow_attr = {}
			flow_attr['table_id'] = tokens[0].split("=")[1].replace(",", "")
			mirror_tokens = mirror.split(",")
			flow_attr['mirror_id'] = mirror_tokens[0].split(":")[1]
			flow_attr['mirror_dst_ip'] = mirror_tokens[1].split(":")[1]
			flow_attr['mirror_n_packets'] = mirror_tokens[2].split(":")[1]
			flow_attr['mirror_n_bytes'] = mirror_tokens[3].split(":")[1]
			mirror_attrs.append(flow_attr)
		return mirror_attrs

	def get_tunnel_port(self):
		tp = None
		if (self.mirror != None):
			tp = self.mirror.get_tunnel_port()
		return tp

	def get_mirror_vport(self, dir):
		mirror_vport = None
		mirror_ofp_port = None
		mirror_odp_port = None
		if (self.mirror != None):
			mirror_vport, mirror_port_nos = self.mirror.get_mirror_vport(dir)
			mirror_ofp_port = mirror_port_nos.replace("(", "").replace(")", "").split("/")[0]
			mirror_odp_port = mirror_port_nos.replace("(", "").replace(")", "").split("/")[1]
		return mirror_vport, mirror_ofp_port, mirror_odp_port

	def __parse_dump_flows_detail(self, acl_type, is_mirror):
		cmd = [ self.appctl_path, "bridge/dump-flows-detail", self.br ]
		out = shell.execute(cmd).splitlines()
		n_packets = 0
		n_bytes = 0
		table_id = -1
		if (acl_type == "ingress"):
			table_id = 9
		elif (acl_type == "egress"):
			table_id = 14
		elif (acl_type == "redirect"):
			table_id = 10
		if (table_id == -1):
			return n_packets, n_bytes, None
		for l in out:
			if (l.find("n_packets=0") >= 0):
				continue
			this_table_id = str(l.split(",")[0]).split("=")[1]
			if (this_table_id != str(table_id)):
				continue
			toks = l.split()
			if (l.find("mirror=") < 0):
				n_packets = -1
				n_bytes = -1
				break
			if (is_mirror == True):
				mirror_tok = toks[18]
				n_packets = mirror_tok.split(",")[2].split(":")[1]
				n_bytes = mirror_tok.split(",")[3].split(":")[1].replace("}", "")
			else :
				n_packets = toks[2].split("=")[1].replace(",", "")
				n_bytes = toks[19].split("=")[1].replace(",", "")
			break
		return n_packets, n_bytes, l

	def get_flow_pkt_counters(self, acl_type):
		return self.__parse_dump_flows_detail(acl_type, False)

	def get_flow_pkt_counters_mirror(self, acl_type):
		return self.__parse_dump_flows_detail(acl_type, True)
