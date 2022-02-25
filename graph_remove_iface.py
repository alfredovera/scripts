#!/usr/bin/env python3
"""Removes an interface from Graph"""
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


parser = argparse.ArgumentParser(description="Remove an interface from Graph")
parser.add_argument("iface", type=str, help="Mac address of the interface")
parser.add_argument("-d", action="store_true", help="Delete the interface")
args = parser.parse_args()

g = graph.Graph("api.subspace.com:443")

# lookup interface
iface = g.get_interface(args.iface)
exit_if_none(iface, f"Could not find interface {args.iface}")


print(
    f"if  {iface.name} {iface.guid} {iface.mac.content} {iface.state=} {iface.type=} {iface.use_ipv4=}"
)

if args.d:
    print("Removing ^^ from graph")
    g.delete_interface(iface.mac.content)
