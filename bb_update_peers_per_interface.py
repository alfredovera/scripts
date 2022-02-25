#!/usr/bin/env python3
import argparse
import typing

import netaddr

from lib import billboard, general, netbox

Bb_dataclasses = list[billboard.bb_dataclass]
NetIps = list[netaddr.IPNetwork]


def arg_parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
    Enable/disable peers for a server on given interfaces

    examples:
    The following will print the commands but not execute.
        %(prog)s -i mcx1p1 -p -u         # undrain prod_global on all peers on this specific interface
        %(prog)s -i mcx1p1,mcx1p2 -p -u  # undrain prod_global on all peers on these specific interfaces

        %(prog)s -e mcx1p1 -p -u         # undrain prod_global on all peers except on this specific interface
        %(prog)s -e mcx1p1,mcx1p2 -p -u  # undrain prod_global on all peers on these specific interfaces

        %(prog)s -i mcx1p1 -m -u         # undrain monitor on all peers on this specific interface
        %(prog)s -e mcx1p1 -m -u         # undrain monitor on all peers except on this specific interface

        %(prog)s -i mcx1p1 -m -p -d      # drain monitor and prod_global on all peers on this specific interface
        %(prog)s -e mcx1p1 -m -p -d      # drain monitor and prod_global on all peers except on this specific interface

    Add the '-x' flag to any of these to apply it directly.
    """,
    )
    parser.add_argument(
        "server", type=str, help="The server name to apply teh paths for"
    )
    iface_selection = parser.add_mutually_exclusive_group(required=True)
    iface_selection.add_argument(
        "-i",
        metavar="interface name",
        default="",
        type=str,
        help="Only include a specific interface",
    )
    iface_selection.add_argument(
        "-e",
        metavar="interface name",
        default="",
        type=str,
        help="Include all interfaces except a specific interface",
    )
    parser.add_argument(
        "-p",
        action="store_const",
        const="prod_global",
        help="Enabled prod_global path_type",
    )
    parser.add_argument(
        "-m",
        action="store_const",
        const="monitor",
        help="Enabled monitor path_type",
    )
    drain_selection = parser.add_mutually_exclusive_group(required=True)
    drain_selection.add_argument(
        "-d",
        action="store_const",
        const="drain",
        help="Drain",
    )
    drain_selection.add_argument(
        "-u",
        action="store_const",
        const="undrain",
        help="Undrain",
    )
    parser.add_argument(
        "-x",
        action="store_true",
        default=False,
        help="Execute the billboard commands instead of generate only",
    )
    return parser.parse_args()


def single_interface(ifaces: list[str]) -> NetIps:
    ips = get_ips(ifaces)
    net_ips = [netaddr.IPNetwork(ip["ip"]) for ip in ips if ip.get("ip")]
    return net_ips


def multiple_interfaces(except_ifaces: list[str]) -> NetIps:
    ips = get_ips()
    but_ips = [
        ip
        for ip in ips
        if ip.get("interface") and ip["interface"].name not in except_ifaces
    ]
    net_ips = [netaddr.IPNetwork(ip["ip"]) for ip in but_ips if ip.get("ip")]
    return net_ips


def get_ips(
    interface: list[str] = None,
) -> list[dict[str, typing.Any]]:
    # works with list and string
    nb = netbox.Netbox()

    netbox_tag = "circuit-interface-ip"
    ips = nb.query_ips(device=server_name, tag=netbox_tag, interface=interface)
    return ips


def get_net_ips(intfs: str = None, except_intfs: str = None) -> NetIps:
    net_ips = []
    if intfs and isinstance(intfs, str):
        ifaces = list(map(str.strip, intfs.split(",")))
        net_ips = single_interface(ifaces=ifaces)
    elif except_intfs and isinstance(intfs, str):
        except_ifaces = list(map(str.strip, except_intfs.split(",")))
        net_ips = multiple_interfaces(except_ifaces=except_ifaces)
    return net_ips


def get_bb_cmds(
    net_ips: NetIps, drain_action: str, server_name: str, path_types: str
) -> list[str]:
    bb_peer_parsed = billboard.get_parsed_peer_data(server=server_name)

    bb_matched_peers = [
        b for b in bb_peer_parsed for n in net_ips if netaddr.IPAddress(b.peer_ip) in n
    ]
    bb_cmds = []
    for b in bb_matched_peers:
        if netaddr.IPAddress(b.peer_ip).version == 6:
            if "prod_global" in path_types:
                path_types = "prod_global"
            else:
                continue
        bb_cmds.append(
            f"billboard {drain_action} peer {server_name} {b.peer_ip} path_types={path_types}"
        )

    return bb_cmds


def execute_billboard_commands(bb_cmds: list[str], execute: bool = False) -> None:
    # Execute or just print
    if execute:
        for line in bb_cmds:
            _, output, errors = general.shell_cmd(line.split(), communicate_input="y\n")
            print(line)
            if output:
                print(f"\t{output}")
            if errors:
                print(f"\t{errors}", end="")
    else:
        for line in bb_cmds:
            print(line)


def main() -> None:
    net_ips = get_net_ips(intfs=intf, except_intfs=except_intf)
    bb_cmds = get_bb_cmds(
        net_ips=net_ips,
        drain_action=drain_action,
        server_name=server_name,
        path_types=path_types,
    )
    execute_billboard_commands(bb_cmds=bb_cmds, execute=execute)


if __name__ == "__main__":
    args = arg_parse()
    general.preliminary_checks(
        [
            "BILLBOARD_API_TOKEN",
            "NETBOX_TOKEN",
        ]
    )
    server_name = args.server
    intf: str = args.i
    except_intf: str = args.e
    drain_action = args.d or args.u
    execute = args.x
    path_types = ",".join([x for x in [args.p, args.m] if x])
    main()
