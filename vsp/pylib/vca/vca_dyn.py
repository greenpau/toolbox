#!/usr/bin/python

import sys

sys.path.append("/usr/local/openvswitch/pylib/system")
import shell

sys.path.append("/usr/local/openvswitch/pylib/vca")
import vca_mirror
import vca_vm

class DYN(object):
	mirror = None
	def __init__(self, ovs_path, br, logfd, mirror_id, mirror_dst_port,
		     vm_name, dyn_type):
		self.ovs_path = ovs_path
		self.ofctl_path = self.ovs_path + "/ovs-ofctl"
		self.vsctl_path = self.ovs_path + "/ovs-vsctl"
		self.br = br
		self.logfd = logfd
		self.mirror_id = mirror_id
		self.mirror_dst_port = mirror_dst_port
		self.vm_name = vm_name
		self.dyn_type = dyn_type
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

	def __setup_vport_mirror(self, action):
		if (action == "Set"):
			cmd = [ self.vsctl_path, "set", "interface",
				self.port_name,
				"other_config:dyn-mirror=enable",
				"other_config:mirror-dst-port=" +
				 self.mirror_dst_port,
				"other_config:mirror-dir=both",
				"other_config:mirror-id=" + self.mirror_id,
			      ]
			hdrstr = "create mirror on vport " + self.port_name
		else :
			cmd = [ self.vsctl_path, "set", "interface",
				self.port_name,
				"other_config:dyn-mirror=disable",
				"other_config:mirror-dst-port=" +
				 self.mirror_dst_port,
				"other_config:mirror-dir=both",
				"other_config:mirror-id=" + self.mirror_id,
			      ]
			hdrstr = "destroy mirror on vport " + self.port_name
		shell.run_cmd(hdrstr, cmd, self.logfd)

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

	def get_internal_name(self):
		int_name = None
		if (self.mirror != None):
			int_name = self.mirror.get_internal_name()
		return int_name

	def get_tunnel_port(self):
		return None, None
