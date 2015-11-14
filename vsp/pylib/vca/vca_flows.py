#!/usr/bin/python

import shell

import ovs_flows
import ovs_ofproto

class Flows(object):
	def __init__(self, ovs_path, br, logfd):
		self.appctl_path = ovs_path + "/ovs-appctl"
		self.br = br
		self.logfd = logfd
		self.flow = ovs_flows.Flows(ovs_path, self.logfd)
		self.ofproto = ovs_ofproto.OFProto(ovs_path)

	def dump_flows(self):
		cmd = [ "sudo", self.appctl_path, "bridge/dump-flows", self.br ]
		shell.execute_hdr("Displaying flows in " + self.br, cmd)

	def reset(self):
		self.flow.reset(self.br)

	def set_flow_evpn_membership(self, vrf_id, evpn_id, vm_iface, vm_uuid,
				     vm_type):
		hdr = "Add flow for EVPN-membership"
		flow_str = "flow_type=route,flags=membership" + \
			   ",vrf_id=" + vrf_id + \
			   ",evpn_id=" + evpn_id + \
			   ",interface=" + vm_iface + \
			   ",vm_uuid=" + vm_uuid + \
			   ",type=" + vm_type
		self.flow.set_flow_execute(hdr, self.br, flow_str)


	def set_flow_evpn_route(self, vrf_id, evpn_id, vm_iface, vm_ip_local,
				vm_netmask, vm_subnet, vm_mac, vm_uuid,
				vm_gw_ip, vm_type, evpn_gw_ip):
		hdr = "Add flow for EVPN-VM route"
		flow_str = "flow_type=route,flags=evpn" + \
			   ",vrf_id=" + vrf_id + \
			   ",evpn_id=" + evpn_id + \
			   ",interface=" + vm_iface + \
			   ",vm_uuid=" + vm_uuid + \
			   ",dl_dst=" + vm_mac + \
			   ",nw_dst=" + vm_ip_local + \
			   ",subnet=" + vm_subnet + \
			   ",type=" + vm_type + \
			   ",gateway=" + evpn_gw_ip
		self.flow.set_flow_execute(hdr, self.br, flow_str)

	def set_flow_evpn_redirect(self, vrf_id, evpn_id, vm_iface, vm_ip_local,
				   vm_netmask, vm_mac, vm_uuid, vm_gw_ip,
				   evpn_gw_ip, evpn_subnet):
		hdr = "Add flow for EVPN redirect route"
		flow_str = "flow_type=route,flags=evpn-redirect" + \
			   ",vrf_id=" + vrf_id + \
			   ",evpn_id=" + evpn_id + \
			   ",interface=" + vm_iface + \
			   ",vm_uuid=" + vm_uuid + \
			   ",dl_dst=" + vm_mac + \
			   ",nw_dst=" + vm_ip_local + \
			   ",subnet=" + evpn_subnet + \
			   ",gateway=" + evpn_gw_ip
		self.flow.set_flow_execute(hdr, self.br, flow_str)

	def set_flow_table_4_table_7(self):
		hdr = "Add flow for Anti-spoof (Table 4 -> Table 7)"
		flow_str = "table=4,action=resubmit(,7)"
		self.flow.set_flow_execute(hdr, self.br, flow_str)

	def set_flow_acl_ingress(self, vm_iface, vm_uuid, vm_type):
		hdr = "Add flow for ACL ingress (pre)"
		flow_str = "flow_type=acl,flags=pre" + \
			   ",interface=" + vm_iface + \
			   ",vm_uuid=" + vm_uuid + \
			   ",type=" + vm_type + \
			   ",priority=0" + \
			   ",actions=allow"
		self.flow.set_flow_execute(hdr, self.br, flow_str)

	def set_flow_acl_redirect(self, vm_iface, vm_uuid):
		hdr = "Add flow for ACL redirect (advanced routing table)"
		flow_str = "flow_type=acl,flags=redirect," + \
			   ",interface=" + vm_iface + \
			   ",vm_uuid=" + vm_uuid + \
			   ",priority=0" + \
			   ",action=allow"
		self.flow.set_flow_execute(hdr, self.br, flow_str)

	def set_flow_qos(self, vm_iface, vm_uuid):
		hdr = "Add flow for QOS"
		flow_str = "flow_type=qos" + \
			   ",interface=" + vm_iface + \
			   ",vm_uuid=" + vm_uuid + \
			   ",rewrite" + \
			   ",engress_rate=10000,ingress_burst=1000" + \
			   ",egress_class=3,n_entries=1,in_dscp=0,out_dscp=18"
		self.flow.set_flow_execute(hdr, self.br, flow_str)

	def set_flow_arp_route(self, vrf_id, evpn_id, vm_iface, vm_ip_local,
			       vm_mac, vm_uuid, vm_gw_ip, evpn_gw_ip,
			       evpn_subnet):
		hdr = "Add flow for ARP route"
		flow_str = "flow_type=route,flags=arp-route" + \
			   ",vrf_id=" + vrf_id + \
			   ",evpn_id=" + evpn_id + \
			   ",interface=" + vm_iface + \
			   ",vm_uuid=" + vm_uuid + \
			   ",dl_dst=" + vm_mac + \
			   ",nw_dst=" + vm_ip_local + \
			   ",subnet=" + evpn_subnet + \
			   ",gateway=" + evpn_gw_ip
		self.flow.set_flow_execute(hdr, self.br, flow_str)

	def set_flow_dhcp_request(self, iface, evpn_id, vm_uuid, vm_ip_local):
		hdr = "Add flow for DHCP request for VM iface " + iface
		flow_str = "flow_type=dhcp" + \
			   ",interface=" + iface + \
			   ",evpn_id=" + evpn_id + \
			   ",vm_uuid=" + vm_uuid + \
			   ",ip=" + vm_ip_local
		self.flow.set_flow_execute(hdr, self.br, flow_str)

	def set_flow_remote_route(self, vrf_id, vrf_tnl_key, evpn_id,
				  vm_iface, vm_ip_remote, vm_mac_remote,
				  vm_type, rtep_ip, evpn_gw_ip, evpn_subnet):
		hdr = "Add flow for remote route (" + rtep_ip + ")"
		flow_str = "flow_type=route,flags=evpn" + \
			   ",vrf_id=" + vrf_id + \
			   ",evpn_id=" + evpn_id + \
			   ",vni_id=" + vrf_tnl_key + \
			   ",interface=" + vm_iface + \
			   ",dl_dst=" + vm_mac_remote + \
			   ",nw_dst=" + vm_ip_remote + \
			   ",type=" + vm_type + \
			   ",subnet=" + evpn_subnet + \
			   ",gateway=" + evpn_gw_ip + \
			   ",is_remote=true" + \
			   ",remote_ip=" + rtep_ip
		self.flow.set_flow_execute(hdr, self.br, flow_str)

	def set_l2_flow(self, port_1, port_2):
		ofp_port_1 = self.ofproto.ofp_port(self.br, port_1)
		ofp_port_2 = self.ofproto.ofp_port(self.br, port_2)
		hdr = "Setting flow between ports " + port_1 + ":" + ofp_port_1 + " -> " + port_2 + ":" + ofp_port_2
		flow_str = "table=0,in_port=" + ofp_port_1 + \
			   ",idle_timeout=0," + \
			   "action=output:" + ofp_port_2
		self.flow.set_flow_execute(hdr, self.br, flow_str)
