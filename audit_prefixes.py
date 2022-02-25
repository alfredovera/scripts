#!/usr/bin/env python3
"""Audit advertisement prefixes """
import os
import pynetbox

NETBOX_TOKEN = os.environ["NETBOX_TOKEN"]
NETBOX_URL = "https://netbox.global.ftlprod.net"
netbox = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)

prefixes = netbox.ipam.prefixes.filter(role="ipv4-advertisement-range")
for pfx in prefixes:
    pfx_ips = netbox.ipam.ip_addresses.filter(parent=pfx.prefix)

    num_ips = len(pfx_ips)

    if num_ips == 0:
        print(f"{pfx} has no child ip addresses")
    elif num_ips > 1:
        print(f"{pfx} {pfx.site.name} has multiple child ip addresses:")
        for ip in pfx_ips:
            if ip.assigned_object is not None:
                print(f"  {ip} {ip.assigned_object.name} {ip.assigned_object.device.name}")
            else:
                print(f"  {ip}")
