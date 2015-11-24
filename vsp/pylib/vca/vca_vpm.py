#!/usr/bin/python

import sys

sys.path.append("/usr/local/openvswitch/pylib/system")
import shell

sys.path.append("/usr/local/openvswitch/pylib/vca")
import vca_mirror
import vca_vm

class VPM(object):
	mirror = None
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
		self.mirror_flowstr = "flow_type=mirror, interface=" + self.vport + ", vm_uuid=" + self.vm_uuid + "," + "mirror-id=" + self.mirror_id + ", remote_ip=" + self.mirror_dst_ip

	def __setup_vport_mirror(self, action):
		flowstr = self.mirror_flowstr + ", mirror_direction=" + self.mirror_dir
		if (action == "Set"):
			ofctl_cmd = "add-flow"
		else :
			ofctl_cmd = "del-flows"
		cmd = [ self.ofctl_path, ofctl_cmd, self.br, flowstr ]
		hdrstr = action + " " + self.mirror_dir + " Port mirror"
		shell.run_cmd(hdrstr, cmd, self.logfd)

	def local_create(self, mirror_dir):
		self.mirror_dir = mirror_dir
		self.__setup_vport_mirror("Set")
		self.mirror = vca_mirror.Mirror(self.ovs_path, self.br,
						self.logfd, "Port",
						self.mirror_id)

	def local_destroy(self):
		if (self.mirror_dir != None):
			self.__setup_vport_mirror("Unset")

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

	def get_tunnel_port(self):
		tp = None
		if (self.mirror != None):
			tp = self.mirror.get_tunnel_port()
		return tp
