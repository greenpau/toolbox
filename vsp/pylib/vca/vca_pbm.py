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
		self.vport = self.vm.vport()
		self.vm_ofp_port = self.vm.vm_port()
		self.default_flowstr = "priority=0,actions=allow"
		self.static_flowstr = "priority=0,tcp,in_port=" + self.vm_ofp_port + ",tp_src=100,tp_dst=200,actions=allow"
		self.mirror_flowstr = "mirror_id=" + self.mirror_id + ",mirror_dst_ip=" + self.mirror_dst_ip

	def __base_acl_flowstr(self, acl_dir):
		flowstr = "flow_type=acl,flags=" + acl_dir + ",interface=" + self.vport + ",vm_uuid=" + self.vm_uuid + ",type=vm"
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

	def __setup_static_acl_mirror_flowstr(self, acl_dir):
		flowstr = self.__acl_mirror_flowstr(acl_dir) + "," + self.static_flowstr
		return flowstr

	def __cleanup_static_acl_mirror_flowstr(self, acl_dir):
		flowstr = self.__base_acl_flowstr(acl_dir) + "," + self.static_flowstr
		return flowstr

	def __setup_acl_mirror(self, action, acl_type, acl_dir):
		flowstr = None
		table_type = None
		if (acl_dir == "ingress"):
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
		if (flowstr == None):
			print "Mirrors for ACL type " + acl_type + " not supported yet"
			return

		cmd = [ self.ofctl_path, "add-flow", self.br, flowstr ]
		hdrstr = action + " " + acl_type + " " + acl_dir + " ACL mirror"
		shell.run_cmd(hdrstr, cmd, self.logfd)
		if (acl_type == "static"):
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
