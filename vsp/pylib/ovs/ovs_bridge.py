#!/usr/bin/python

import shell
import vca_flows
import vca_evpn
import vca_vrf
import ovs_vport_tap
import ovs_vport_tnl

class Bridge(object):
	def __init__(self, ovs_path, br, logfd):
		self.ovs_path = ovs_path
		self.ofctl_path = ovs_path + "/ovs-ofctl"
		self.appctl_path = ovs_path + "/ovs-appctl"
		self.vsctl_path = ovs_path + "/ovs-vsctl"
		self.br = br
		self.logfd = logfd

	def reset(self, iface):
		tap = ovs_vport_tap.Tap(self.ovs_path, "internal",
					self.br, iface, "0.0.0.0", self.logfd);
		tap.reset()

		tnl = ovs_vport_tnl.Tunnel(self.ovs_path, self.br,
					   None, None, "0.0.0.0",
					   None, self.logfd)
		tnl.reset()

		flows = vca_flows.Flows(self.ovs_path, self.br, self.logfd)
		flows.reset()

		evpn = vca_evpn.EVPN(self.ovs_path, self.br, 0, 0, 0, 0, 0, 0,
				     0, self.logfd)
		evpn.reset()

		vrf = vca_vrf.VRF(self.ovs_path, self.br, 0, 0, 0, 0,
				  self.logfd)
		vrf.reset()

	def show(self):
		cmd = [ "sudo", self.appctl_path, "dpif/show", ]
		shell.execute_hdr("DPIF configuration", cmd)

		cmd = [ "sudo", self.ofctl_path, "dump-ports-desc", self.br ]
		shell.execute_hdr("OFProto configuration", cmd)

		cmd = [ "sudo", self.appctl_path, "bridge/port-show" ]
		shell.execute_hdr("Bridge Port configuration", cmd)

	def dump_flows(self):
		flows = vca_flows.Flows(self.ovs_path, self.br, self.logfd)
		flows.dump_flows()
