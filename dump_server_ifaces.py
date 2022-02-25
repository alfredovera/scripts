#!/usr/bin/env python3
"""Print out a data server's interface configuration"""

import argparse

from lib import general, netbox

COLORS = {
    "no-tag": "\x01\x1b[48;2;255;0;0m\x02\x01\x1b[38;2;255;255;255m\x02",
    "reset": "\x01\x1b[0m\x02",
    "oob-ip": "\x01\x1b[48;2;103;58;183m\x02",
    "anycast-ip": "\x01\x1b[48;2;76;175;80m\x02",
    "site-local-ip": "\x01\x1b[48;2;255;235;59m\x02\x01\x1b[38;2;0;0;0m\x02",
    "interface-local-ip": "\x01\x1b[48;2;255;152;0m\x02\x01\x1b[38;2;0;0;0m\x02",
    "circuit-interface-ip": "\x01\x1b[48;2;63;81;181m\x02",
}


def get_ip_str(nb_ip):
    """Get a colorized string to represent the IP"""
    tag = next(t.slug for t in nb_ip.tags) if nb_ip.tags else "no-tag"
    color = COLORS[tag] if tag is not None else ""
    return f"{color}{nb_ip.address}{COLORS['reset']}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Print out a data server's interface configuration according to "
        "Netbox. Includes the type and status of connected circuits."
    )
    parser.add_argument("server", help="Server name")
    args = parser.parse_args()
    srv_name = args.server.lower()

    general.preliminary_checks(["NETBOX_TOKEN"])

    nb = netbox.Netbox()
    nb_server = nb.get_server(srv_name)
    if nb_server is None:
        raise ValueError(f"No server {srv_name} in Netbox")

    print(
        f"\nNETBOX data for: {COLORS['site-local-ip']}{nb_server.name}{COLORS['reset']}"
        f" ({nb_server.device_type.display_name})\n"
    )
    print(
        f"{'Name':16}"
        f"{'Type':6}"
        f"{'Lacp':6}"
        f"{'Status':14}"
        f"{'Provider':15}"
        f"{'CID':40}"
        f"{'Description':30}"
        f"{'IPs: '}"
        f" {COLORS['no-tag']}no tag{COLORS['reset']}"
        f" {COLORS['oob-ip']}oob-ip{COLORS['reset']}"
        f" {COLORS['anycast-ip']}anycast-ip{COLORS['reset']}"
        f" {COLORS['site-local-ip']}site-local-ip{COLORS['reset']}"
        f" {COLORS['interface-local-ip']}interface-local-ip{COLORS['reset']}"
        f" {COLORS['circuit-interface-ip']}circuit-interface-ip{COLORS['reset']}"
        "\n"
    )
    for nb_iface in nb.get_server_ifaces(nb_server):
        nb_circuit = nb.get_iface_circuit(nb_iface)
        nb_ips = nb.get_iface_ips(nb_iface)

        circuit_cid = ""
        circuit_provider = ""
        circuit_type = ""
        circuit_status = ""
        circuit_desc = ""
        circuit_lacp = ""
        if nb_circuit is not None:
            circuit_cid = nb_circuit.cid
            circuit_provider = nb_circuit.provider.name
            circuit_type = nb_circuit.type.slug
            circuit_status = nb_circuit.status.value
            circuit_desc = nb_circuit.description
            circuit_lacp = "Yes" if nb_circuit.custom_fields["lacp-required"] else ""

        print(
            f"{(nb_iface.name):16}"
            f"{circuit_type:6}"
            f"{circuit_lacp:6}"
            f"{circuit_status:14}"
            f"{circuit_provider:15}"
            f"{circuit_cid:40}"
            f"{circuit_desc:30}"
            f"{(' '.join([get_ip_str(i) for i in nb_ips]))}"
        )

    print("")
