#!/usr/bin/env python3
import argparse
import sys

from graph import graph

# from graph.pop_pb2 import Pop
# from graph.server_pb2 import Server
# from graph.interface_pb2 import Interface, InterfaceState, InterfaceType
from graph.interface_pb2 import InterfaceType
from icmplib import ping
from tcolorpy import tcolor


def exit_if_none(obj, msg):
    if obj is None:
        print(msg)
        sys.exit(0)


parser = argparse.ArgumentParser(description="Ping test midgress address reachability")
parser.add_argument("server", type=str, help="The server name to query for")
args = parser.parse_args()

g = graph.Graph("api.subspace.com:443")

# lookup server
s = g.get_server(args.server)
exit_if_none(s, f"Could not find server {args.server}")

p = g.get_pop(s.pop_id)
ifaces = g.list_interfaces_by_field(field="pop_bpf_id", value=str(s.pop_bpf_id))

print("\nTesting midgress reachability for:\n")
print(f"pop {p.name} {p.graph_id}")
print(f"svr {s.name} {s.guid} {s.pop_id} {s.pop_bpf_id}")

for iface in ifaces:

    if not iface.type == InterfaceType.TRANSIT:
        continue

    print(tcolor(f"\n{iface.name}:", color="blue"))
    if iface.v4_midgress_cidr.address:
        host = ping(
            iface.v4_midgress_cidr.address, count=10, interval=0.2, privileged=False
        )
        msg = f"  {host.packets_received} of {host.packets_sent} pkts ({host.min_rtt}/{host.avg_rtt}/{host.max_rtt})"
        color = "green" if host.is_alive else "red"
        print(f"  {iface.v4_midgress_cidr.address:36}{tcolor(msg, color=color)}")

    if iface.v6_midgress_cidr.address:
        host = ping(
            iface.v6_midgress_cidr.address, count=10, interval=0.2, privileged=False
        )
        msg = f"  {host.packets_received} of {host.packets_sent} pkts ({host.min_rtt}/{host.avg_rtt}/{host.max_rtt})"
        color = "green" if host.is_alive else "red"
        print(f"  {iface.v6_midgress_cidr.address:36}{tcolor(msg, color=color)}")
