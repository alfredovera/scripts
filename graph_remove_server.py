#!/usr/bin/env python3
"""Remove a Server and interfaces from Graph"""
import argparse
import sys

from graph import graph

# from graph.pop_pb2 import Pop
# from graph.server_pb2 import Server
# from graph.interface_pb2 import Interface, InterfaceState


def exit_if_none(obj, msg):
    if obj is None:
        print(msg)
        sys.exit(0)


parser = argparse.ArgumentParser(description="Remove a server from Graph")
parser.add_argument("server", type=str, help="The server name to query for")
parser.add_argument(
    "-d", action="store_true", help="Delete the server, pop and interfaces"
)
args = parser.parse_args()

g = graph.Graph("api.subspace.com:443")

# lookup server
s = g.get_server(args.server)
exit_if_none(s, f"Could not find server {args.server}")

p = g.get_pop(s.pop_id)
ifaces = g.list_interfaces_by_field(field="pop_bpf_id", value=str(s.pop_bpf_id))

print(f"pop {p.name} {p.graph_id}")
print(f"svr {s.name} {s.guid} {s.pop_id} {s.pop_bpf_id}")
for iface in ifaces:
    print(
        f"if  {iface.name} {iface.guid} {iface.mac.content} {iface.state=} {iface.type=} {iface.use_ipv4=}"
    )

if args.d:
    print("Removing ^^ from graph")
    for iface in ifaces:
        g.delete_interface(iface.mac.content)
    g.delete_server(s.name)
