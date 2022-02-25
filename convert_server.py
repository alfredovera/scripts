#!/usr/bin/env python3
"""Convert a R6515 server to a R7525 in Netbox

Changes hardware type, adds additional interfaces
"""
import argparse
import os

import netbox_exporter
from lib import general, hardware_types, netbox

nb = netbox.Netbox()


def ensure_server_model(nb_server, model):
    """Update the model of the server"""
    if nb_server.device_type.model != model:
        if not nb_server.update({"device_type": {"model": model}}):
            raise Exception("Failed to update server model")
        print(f"Updated server model to {model}")


def ifaces_require_update(nb_server, expected_ifaces):
    """Check if a Netbox device has all of the expected interfaces configured"""
    cur_ifaces = [i.name for i in nb.get_server_ifaces(nb_server)]
    exp_ifaces = [i["name"] for i in expected_ifaces]
    return cur_ifaces != exp_ifaces


def migrate_iface_config(nb_server, mig_state, mig_map):
    """Migrate the IP addresses and circuit connections to new interfaces"""
    for iface in mig_state["ifaces"]:
        new_name = mig_map[iface["name"]]
        print(f"Migrating old {iface['name']} as {new_name}:")
        nb_iface = nb.get_server_iface_by_name(nb_server, new_name)
        if not nb_iface:
            raise ValueError("No iface {new_name} found on {nb_server}")
        nb.configure_iface(nb_iface, iface)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Convert Netbox server between models")
    parser.add_argument("server", help="server name")
    parser.add_argument("target_model", help="target model", choices=["R7525"])
    args = parser.parse_args()

    general.preliminary_checks(["NETBOX_TOKEN"])
    # backup pre-migration state
    nbe = netbox_exporter.NetboxExporter()
    mig_dir = f"{os.path.dirname(__file__)}/.convert_server_data"
    mig_filename = f"{mig_dir}/{args.server}.json"
    if not os.path.exists(mig_filename):
        if not os.path.exists(mig_dir):
            os.mkdir(mig_dir)
        nbe.save_server_data(args.server, mig_filename)
    mig_state = nbe.load_server_data(mig_filename)

    # lookup target interface layouts and migration mapping
    src_model = mig_state["model"]
    dst_model = args.target_model
    iface_layout = hardware_types.get_iface_layout_for_model(dst_model)
    iface_mig_map = hardware_types.get_iface_migration_map(src_model, dst_model)

    nb_server = nb.get_server(args.server)
    ensure_server_model(nb_server, dst_model)

    if ifaces_require_update(nb_server, iface_layout):
        print("Interface layout is inconsistent and will be recreated!")
        print("\nRemoving existing interfaces:")
        nb.remove_all_ifaces(nb_server)
        print("\nAdding new interface layout:")
        nb.ensure_iface_layout(nb_server, iface_layout)
        print()
        migrate_iface_config(nb_server, mig_state, iface_mig_map)

#    - rename server ?
