#!/usr/bin/python

import sys
sys.path.append("/usr/local/openvswitch/pylib/system")
sys.path.append("/usr/local/openvswitch/pylib/ovs")
import shell
import ovs_ofproto

class Flows(object):
	def __init__(self, ovs_path, logfd):
		self.logfd = logfd
		self.ofctl_path = ovs_path + "/ovs-ofctl"
		self.appctl_path = ovs_path + "/ovs-appctl"
		self.ofproto = ovs_ofproto.OFProto(ovs_path)

	def set_flow_execute(self, hdr, br, flow_str):
		cmd = [ self.ofctl_path, "add-flow", br, flow_str ]
		shell.run_cmd(hdr, cmd, self.logfd);

	def reset(self, br):
		hdr = "Deleting all flows in bridge " + br
		cmd = [ self.ofctl_path, "del-flows", br ]
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

	def __parse_dump_flows(self, br, table_id, col):
		cmd = [ self.appctl_path, "bridge/dump-flows", br ]
		out = shell.execute(cmd).splitlines()
		n_flows = 0
		out_flows = []
		for l in out:
			toks = l.split()
			if (toks[0].find("table_id") < 0):
				continue
			this_table_id = toks[0].split("=")[1].replace(",", "")
			if (this_table_id == str(254) or
			    this_table_id == str(0)):
				continue
			if (table_id != None):
				if (this_table_id != str(table_id)):
					continue
			n_flows = n_flows + 1
			if (col != None):
				out_flows.append([this_table_id, toks[int(col)]])
			else:
				out_flows.append([this_table_id, l])
		return n_flows, out_flows

	def get_n_pkts_by_table(self, br, table_id):
		n_flows, flows = self.__parse_dump_flows(br, table_id, "2")
		out_flows = []
		n_flows_pkt = 0
		for f in flows:
			n_pkts = int(f[1].split("=")[1].replace(",", ""))
			out_flows.append([int(f[0]), n_pkts])
			n_flows_pkt = n_flows_pkt + 1
		return n_flows_pkt, out_flows

	def get_n_pkts_hit_by_table(self, br, table_id):
		n_flows, flows = self.__parse_dump_flows(br, table_id, "2")
		out_flows = []
		n_flows_pkt_hits = 0
		for f in flows:
			n_pkts = int(f[1].split("=")[1].replace(",", ""))
			if (n_pkts == 0):
				continue
			out_flows.append([int(f[0]), n_pkts])
			n_flows_pkt_hits = n_flows_pkt_hits + 1
		return n_flows_pkt_hits, out_flows
