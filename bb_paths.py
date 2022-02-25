#!/usr/bin/env python3
import argparse
import copy
import subprocess

import netaddr

from lib import general, netbox


def get_args():
    """
    Parse arguments passed through the run command.
    """
    parser = argparse.ArgumentParser(
        description="This python script queries Netbox API and Billboard Cloud to announce "
        "or withdraw paths via Billboard CLI. To run against your local Billboard environment, add the '-local' flag. "
        "To run in production, add the '-prod' flag. To only print out the CLI commands, do not pass any flags. "
        "Example command: python bb-paths.py announce mad01-data01 -type prod_global,monitor -prod"
    )
    parser.add_argument(
        "action", action="store", help="[announce|withdraw] Indicate action."
    )
    parser.add_argument(
        "device_name",
        action="store",
        help="Indicate valid POP device. Example: mad01-data01",
    )
    parser.add_argument(
        "-type",
        action="store",
        dest="path_filter",
        required=True,
        help="[prod_global|monitor|site_local|int_local|all] Indicate which Path Type(s) you want"
        " to generate Billboard path commands for. Comma separate for"
        " multiple Path Types. Example: -type prod_global,site_local",
    )
    parser.add_argument(
        "-local",
        default=False,
        action="store_true",
        dest="local_mode",
        help="Indicates local environment mode. Billboard CLI commands will be executed against local Billboard "
        "environment using '--host localhost --port 55010' flags.",
    )
    parser.add_argument(
        "-prod",
        default=False,
        action="store_true",
        dest="prod_mode",
        help="Indicates production mode. WARNING: Billboard CLI commands will be executed.",
    )

    args = parser.parse_args()

    if args.action.lower() not in ["announce", "withdraw"]:
        raise parser.error("Action must be withdraw or announce!")

    path_filters = args.path_filter.lower()
    supported_paths = ["prod_global", "monitor", "site_local", "int_local", "all"]
    if not all(i in supported_paths for i in path_filters.split(",")):
        raise parser.error("All filtered paths must be valid: %s" % supported_paths)

    if args.prod_mode and args.local_mode:
        raise parser.error("You cannot pass both -prod and -local flags at once!")

    return args


def find_device_int(device, peer_list):
    """
    For each peer in peer_list find a matching Netbox device circuit-ip that resides in the same subnet,
    then save the device interface for that peer
    """
    # Query Netbox for ips on device with 'circuit-interface-ip' tag for a specific device
    netbox_tag = "circuit-interface-ip"
    nb_circuit_ips = nb.query_ips(device=device, tag=netbox_tag)

    for peer in peer_list:
        for circuit_ip in nb_circuit_ips:
            ip = netaddr.IPNetwork(circuit_ip["ip"])
            network = ip.cidr
            if netaddr.IPAddress(peer["peer_ip"]) in network:
                peer["interface"] = circuit_ip["interface"]
    return None


def find_int_local_paths(device, peer_list):
    """
    For each peer in peer_list find the Netbox interface-local-ip by matching interface and ipv4/ipv6 type
    """
    # Query Netbox for ips on device with 'interface-local-ip' tag for a specific device
    netbox_tag = "interface-local-ip"
    nb_int_local_ips = nb.query_ips(device=device, tag=netbox_tag)

    for peer in peer_list:
        for int_local_ip in nb_int_local_ips:
            if (
                int_local_ip["interface"] == peer["interface"]
                and int_local_ip["ip_type"] == peer["ip_type"]
            ):
                ip = netaddr.IPNetwork(int_local_ip["ip"])
                cidr = str(ip.cidr)
                peer["paths"].append({"cidr": cidr, "path_type": "int_local"})
    return None


def find_other_paths(site_name, peer_list):
    """
    Query Netbox for PROD_GLOBAL, MONITOR, and SITE_LOCAL ranges and populate
    """

    nb_prod_global_ipv4 = [
        {"cidr": str(i), "path_type": "prod_global"}
        for i in nb.query_prefixes(family=4, role="production-anycast-range")
    ]
    nb_prod_global_ipv6 = [
        {"cidr": str(i), "path_type": "prod_global"}
        for i in nb.query_prefixes(family=6, role="production-anycast-range")
    ]
    nb_monitor_ipv4 = [
        {"cidr": str(i), "path_type": "monitor"}
        for i in nb.query_prefixes(family=4, role="qos-anycast-range")
    ]
    nb_site_local_ipv4 = [
        {"cidr": str(i), "path_type": "site_local"}
        for i in nb.query_prefixes(
            site=site_name, family=4, role="ipv4-site-local-range"
        )
    ]
    nb_site_local_ipv6 = [
        {"cidr": str(i), "path_type": "site_local"}
        for i in nb.query_prefixes(
            site=site_name, family=6, role="ipv6-site-local-range"
        )
    ]
    nb_site_ipv6 = [
        {"cidr": str(i), "path_type": "site_local"}
        for i in nb.query_prefixes(site=site_name, family=6, role="ipv6-site-range")
    ]

    # Loop through each peer, attach rangs to paths list for matching address type
    for peer in peer_list:
        if peer["ip_type"] == "4":
            peer["paths"].extend(nb_prod_global_ipv4)
            peer["paths"].extend(nb_monitor_ipv4)
            peer["paths"].extend(nb_site_local_ipv4)
        elif peer["ip_type"] == "6":
            peer["paths"].extend(nb_prod_global_ipv6)
            peer["paths"].extend(nb_site_local_ipv6)
            peer["paths"].extend(nb_site_ipv6)

    return None


def bb_query_peers(site_name, device):
    """
    Query device peer info using  Billboard CLI tool
    """
    command = ["billboard", "get", "peer", "hostname=%s" % device]
    PEER_IP_OFFSET = 3
    TYPE_OFFSET = 4

    peer_info_dict = {
        "device": "",
        "site": "",
        "peer_ip": "",
        "ip_type": "",
        "peer_type": "",
        "interface": "",
        "paths": [],
    }

    output = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
    )

    # Parse through output and grab device, peer-ip, peer_type info, figure out if each is ipv4 or ipv6
    # Using range [1:-1] to ignore first line containing column names and last line containing empty line
    peer_list = []
    for line in output.stdout.split("\n")[1:-1]:
        peer_ip = line.split()[PEER_IP_OFFSET]
        ip_type = netaddr.IPNetwork(peer_ip).version
        peer_type = line.split()[TYPE_OFFSET]

        peer_info = copy.deepcopy(peer_info_dict)
        peer_info["device"] = device
        peer_info["site"] = site_name
        peer_info["peer_ip"] = str(peer_ip)
        peer_info["ip_type"] = str(ip_type)
        peer_info["peer_type"] = str(peer_type)
        peer_list.append(peer_info)

    return peer_list


def bb_query_paths(device):
    """
    Query path info using Billboard CLI tool
    """
    command = ["billboard", "get", "path", "hostname=%s" % device]

    output = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
    )
    path_list = []
    for line in output.stdout.split("\n")[1:-1]:
        device, _, _, peer_ip, prefix, prefix_len, path_type, _, _, *_ = line.split()

        path_info = {
            "device": str(device),
            "peer_ip": str(peer_ip),
            "prefix": str(prefix),
            "prefix_len": str(prefix_len),
            "path_type": str(path_type),
        }
        path_list.append(path_info)

    return path_list


def bb_announce_command(device, peer_ip, path_info):
    """
    Craft Billboard Cloud CLI command to announce paths/advertisements for a particular peer
    ex. billboard announce {device_name} {peer_ip} prefix={prefix} prefix_len={prefix_len} type={path_type}
    """
    path_type = path_info["path_type"]
    prefix = path_info["cidr"].split("/")[0]
    prefix_len = path_info["cidr"].split("/")[1]
    path_command = [
        "billboard",
        "announce",
        device,
        peer_ip,
        "prefix=%s" % prefix,
        "prefix_len=%s" % prefix_len,
        "type=%s" % path_type,
    ]

    return path_command


def bb_withdraw_command(path_info):
    """
    Craft Billboard Cloud CLI command to withdraw paths/advertisements for a particular device
    ex. billboard withraw {device_name} {peer_ip} prefix={prefix} prefix_len={prefix_len} type={path_type}
    """
    path_command = [
        "billboard",
        "withdraw",
        path_info["device"],
        path_info["peer_ip"],
        "prefix=%s" % path_info["prefix"],
        "prefix_len=%s" % path_info["prefix_len"],
    ]
    return path_command


def announce(site_name, device, path_filters):
    """
    For announcing paths using Netbox data. Returns list with Billboard CLI commands
    """
    # Find all peers configured in Billboard for device
    peer_list = bb_query_peers(site_name=site_name, device=device)

    # Update peer info with matching interface
    find_device_int(device=device, peer_list=peer_list)

    # Find INT_LOCAL paths and update peer paths
    find_int_local_paths(device=device, peer_list=peer_list)

    # Find PROD_GLOBAL, MONITOR, SITE_LOCAL paths and update peer
    find_other_paths(site_name=site_name, peer_list=peer_list)

    # Craft Billboard path commands
    path_command_list = []
    for peer in peer_list:
        for path in peer["paths"]:
            # Check that path_type is present in user defined path type list before creating Billboard CLI command
            if path["path_type"] in path_filters:
                path_command = bb_announce_command(
                    device=peer["device"], peer_ip=peer["peer_ip"], path_info=path
                )
                path_command_list.append(path_command)

    return path_command_list


def withdraw(device, path_filters):
    """
    For withdrawing paths matching to a particular device and path type. Returns list with Billboard CLI commands
    """
    path_list = bb_query_paths(device)

    # Craft Billboard path commands
    path_command_list = []
    for path in path_list:
        path_type = path["path_type"].lower()
        if path_type in path_filters and path["device"] == device:
            path_command = bb_withdraw_command(path_info=path)
            path_command_list.append(path_command)

    return path_command_list


def main():
    args = get_args()
    general.preliminary_checks(
        [
            "BILLBOARD_API_TOKEN",
            "NETBOX_TOKEN",
        ]
    )
    # device_name = args.device_name.lower()
    action = args.action.lower()
    path_filters = args.path_filter.split(",")
    all_path_types = ["prod_global", "monitor", "site_local", "int_local"]
    # Check path filter
    if path_filters == ["all"]:
        path_filters = all_path_types
    local_mode = args.local_mode
    prod_mode = args.prod_mode

    device_name, site_name = general.get_server_site(args.device_name)

    # Perform withdraw or announce action
    if action == "announce":
        command_list = announce(
            site_name=site_name, device=device_name, path_filters=path_filters
        )
    elif action == "withdraw":
        command_list = withdraw(device=device_name, path_filters=path_filters)

    # Check for prod_mode before processing commands
    for i in command_list:

        if local_mode:
            local_flags = ["--host", "localhost", "--port", "55010"]
            i.extend(local_flags)
            print(" ".join(i))
            p = subprocess.Popen(
                i,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            p.communicate(input="y\n")
        elif prod_mode:
            print(" ".join(i))
            print("WE'LL DO IT LIVE!")
            p = subprocess.Popen(
                i,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            p.communicate(input="y\n")

        else:
            print(" ".join(i))


if __name__ == "__main__":
    nb = netbox.Netbox()
    main()
