#!/usr/bin/python

import shell
import ovs_ofproto

class Flows(object):
	def __init__(self, ovs_path, logfd):
		self.logfd = logfd
		self.ofctl_path = ovs_path + "/ovs-ofctl"
		self.ofproto = ovs_ofproto.OFProto(ovs_path)

	def set_flow_execute(self, hdr, br, flow_str):
		cmd = [ "sudo", self.ofctl_path, "add-flow", br, flow_str ]
		shell.run_cmd(hdr, cmd, self.logfd);

	def reset(self, br):
		hdr = "Deleting all flows in bridge " + br
		cmd = ["sudo", self.ofctl_path, "del-flows", br]
		shell.run_cmd(hdr, cmd, self.logfd)

	def __set_b2b_flow(self, br, port_1, ofp_port_1, port_2, ofp_port_2):
		hdr = "Setting flow between ports " + port_1 + ":" + ofp_port_1 + " -> " + port_2 + ":" + ofp_port_2
		flow_str = "in_port=" + ofp_port_1 + ",idle_timeout=0,action=output:" + ofp_port_2
		self.set_flow_execute(hdr, br, flow_str)

	def __set_arp_flow(self, br, port_1, ofp_port_1, port_2, ofp_port_2):
		hdr = "Setting ARP flow between ports " + port_1 + ":" + ofp_port_1 + " -> " + port_2 + ":" + ofp_port_2
		flow_str = "in_port=" + ofp_port_1 + ",dl_type=0x0806" + ",idle_timeout=0,action=output:" + ofp_port_2
		self.set_flow_execute(hdr, br, flow_str)

	def set_b2b_flows(self, br, port_1, port_2):
		port_1_ofp_port = self.ofproto.ofp_port(br, port_1)
		port_2_ofp_port = self.ofproto.ofp_port(br, port_2)
		self.__set_b2b_flow(br, port_1, port_1_ofp_port, port_2,
				    port_2_ofp_port)
		self.__set_b2b_flow(br, port_2, port_2_ofp_port, port_1,
				    port_1_ofp_port)

	def set_arp_flows(self, br, port_1, port_2):
		port_1_ofp_port = self.ofproto.ofp_port(br, port_1)
		port_2_ofp_port = self.ofproto.ofp_port(br, port_2)
		self.__set_arp_flow(br, port_1, port_1_ofp_port,
				    port_2, port_2_ofp_port)
		self.__set_arp_flow(br, port_2, port_2_ofp_port,
				    port_1, port_1_ofp_port)

	def set_dst_mac_flow(self, br, port_1, mac_2, port_2):
		port_1_ofp_port = self.ofproto.ofp_port(br, port_1)
		port_2_ofp_port = self.ofproto.ofp_port(br, port_2)
		hdr = "Setting dst_mac flow between ports " + port_1 + ":" + ofp_port_1 + " -> " + port_2 + "[" + mac_2 + "]:" + ofp_port_2
		flow_str = "in_port=" + ofp_port_1 + ",dl_dst=" + mac_2 + ",idle_timeout=0,action=output:" + ofp_port_2
		self.set_flow_execute(hdr, br, flow_str)

	def set_flow(self, br, port_1, port_2):
		port_1_ofp_port = self.ofproto.ofp_port(br, port_1)
		port_2_ofp_port = self.ofproto.ofp_port(br, port_2)
		self.__set_b2b_flow(br, port_1, port_1_ofp_port, port_2,
				    port_2_ofp_port)

	def set_loopback_flow(self, br, port, dst_mac, src_mac, dst_ip, src_ip):
		hdr = "Setting loopback flow"
		port_ofp_port = self.ofproto.ofp_port(br, port)
		flow_str = "in_port=" + port_ofp_port + ",idle_timeout=0,action=mod_dl_src:" + dst_mac + ",mod_dl_dst:" + src_mac + ",mod_nw_src:" + dst_ip + ",mod_nw_dst:" + src_ip + ",output:" + port_ofp_port
		self.set_flow_execute(hdr, br, flow_str)
