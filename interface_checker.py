#!/usr/bin/env python3

"""
This tool is used to check an interface for RX, TX, CRC Errors, Light Levels, and Packet Loss
"""


import argparse
import re
import sys
import threading
import time
from dataclasses import dataclass
from subprocess import PIPE, Popen

from bullet import Bullet, Check, colors
from netaddr import IPNetwork
from tcolorpy import tcolor

from lib import netbox

animate_timer = 0
interfaces = {}


@dataclass
class Interface:
    name: str = ""
    mac: str = ""
    circuit_id: str = ""
    provider: str = ""
    status: str = ""
    itype: str = ""
    ip: str = ""
    light_level: str = ""
    speed: str = ""
    before_rx_errors: str = ""
    after_rx_errors: str = ""
    before_tx_errors: str = ""
    after_tx_errors: str = ""
    before_crc_errors: str = ""
    after_crc_errors: str = ""
    packet_loss: str = ""
    state: str = ""
    raw_packet_loss: str = ""
    raw_light_level: str = ""
    problem: str = ""


def arg_parse() -> object:
    parser = argparse.ArgumentParser(
        description="""This tool tests an interface or group of interfaces for a given server (e.g. sub-iad01-data01)"""
    )
    group = parser.add_argument_group("Interface checker")
    group.add_argument("-s", "--server", metavar="", required=False, help="Server Name")
    group.add_argument(
        "-i",
        "--interface",
        metavar="",
        required=False,
        help="Interface of the server to test",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="© Version 2.1.1",
        help="Version Number",
    )
    return parser.parse_args()


def print_complete(msg: str):
    msg += "....................."
    print(tcolor("{:<44}".format(msg[:44]) + "[", color="white"), end="")
    print(tcolor("Completed", color="green"), end="")
    print(tcolor("]", color="white"))


def send_command_to_server(cmd: str, server="", itype="server") -> str:
    """Sending out the hopper command over SSH to retrieve the path_info data"""
    trailer = ".pop.ftlprod.net "
    ssh_parameters = "ssh -q -o StrictHostKeyChecking=no"
    access_command = f"{ssh_parameters} {server}{trailer}"
    if itype == "server":
        server_command = access_command + cmd
    else:
        server_command = cmd
    return (
        Popen(server_command.split(), stdout=PIPE)
        .communicate()[0]
        .decode("utf-8")
        .rstrip("\n")
    )


def is_interface_up(server: str, interface: str) -> int:
    """Checks to see if an interface is UP or DOWN"""
    global animate_timer
    cmd = "sudo ip -s link show " + interface
    result = send_command_to_server(cmd, server)
    match = re.search(r"(\w+) mode", result)
    if match is not None:
        if "UP" == match.group(0).replace(" mode", ""):
            interfaces[interface].state = "UP"
        else:
            interfaces[interface].state = "DOWN"
    else:
        print(f"Could not verify {interface} on {server}")
        return
    animate_timer += 1


def check_int_speed(server: str, interface: str) -> str:
    cmd = f"sudo ethtool {interface} | grep Speed"
    result = send_command_to_server(cmd, server)
    if re.search("10000Mb/s", result):
        return "10G"
    else:
        return "100G"


def check_light_levels(server: str, interface: list):
    """Updates Interface Class with light level of interface"""
    global animate_timer
    interfaces[interface].speed = check_int_speed(server, interface)
    if interfaces[interface].speed == "10G":
        receiver = '| grep "Receiver signal average optical power  "'
    else:
        receiver = '| grep "Rcvr signal avg optical power"'
    cmd = "sudo ethtool -m " + interface.lower() + receiver
    result = send_command_to_server(cmd, server)
    interfaces[interface].raw_light_level = result
    match = re.search(r"(\d+.\d\d) dBm", result)
    if match is not None:
        if interfaces[interface].speed == "10G":
            interfaces[interface].light_level = float(
                match.group(0).replace(" dBm", "")
            )
        else:
            interfaces[interface].light_level = [
                x.replace("/ ", "")
                for x in re.findall(
                    r"(/ (?:.|\s|\d+)(?:.|\s|\d+)(?:.|\s|\d+)\d+)", result, re.MULTILINE
                )
            ]
    else:
        interfaces[interface].light_level = -99
    animate_timer += 1


def get_interface_ip(server: str, interface: list) -> str:
    """returns the ipv4 on a given interface"""
    cmd = "ip -br a | grep " + interface.lower()
    result = send_command_to_server(cmd, server)
    match = re.search(r"(\d+).(\d+).(\d+).(\d+)/", result)
    if match is not None:
        return match.group(0).replace("/", "")


def get_circuit_peer_ip(ip: str, server: str) -> str:
    if "/31" in ip:
        for ip_addr in IPNetwork(ip):
            if ip.strip("/31") != ip_addr:
                return ip_addr
    else:
        result = send_command_to_server(
            f"billboard get peer hostname={server}",
            server,
            "local",
        )
        if result is not None:
            return [
                string
                for string in result.split()
                if ".".join(ip.split(".")[0:3]) in string
            ][0]


def check_packet_loss(server: str, interface: str):
    """Updates Interface Class with the level of packet loss on an interface"""
    global animate_timer
    t = interfaces[interface].itype
    if t == "PNI" or t == "Wave" or t == "IXP":
        ping_ip = get_circuit_peer_ip(interfaces[interface].ip, server)
    else:
        ping_ip = "4.2.2.2"
    source_ip = get_interface_ip(server, interface)
    cmd = f"sudo ping -f {ping_ip} -c 5000 -I " + source_ip
    result = send_command_to_server(cmd, server)
    interfaces[interface].raw_packet_loss = result
    match = re.search(r"(\d+).(\d+)%", result)
    if match is None:
        match = re.search(r"(\d+)%", result)
    if match is not None:
        interfaces[interface].packet_loss = float(match.group(0).replace("%", ""))
    animate_timer += 1


def check_incrementing_crc_errors(server: str, interface: str):
    """Updates Interface Class with the amount of incrementing CRC Errors"""
    global animate_timer
    cmd = "sudo ethtool -S " + interface.lower() + " | grep rx_crc_errors"
    result = send_command_to_server(cmd, server)
    match = re.search(r"(\d+)", result)
    if match is not None:
        interfaces[interface].before_crc_errors = match.group(0)
    time.sleep(30)
    result = send_command_to_server(cmd, server)
    match = re.search(r"(\d+)", result)
    if match is not None:
        interfaces[interface].after_crc_errors = match.group(0)
    animate_timer += 1


def check_rx_and_tx_incrementing_errors(server: str, interface: str):
    """Updates Interface Class with amount of RX and TX errors for an interface"""
    global animate_timer
    if __name__ == "__main__":
        print(
            tcolor("Gathering Incrementing RX and TX Errors...", color="white"),
            end="\r",
        )
    cmd = "sudo ip -s link show " + interface.lower() + r' | grep "RX\|TX" -A 1'
    result = send_command_to_server(cmd, server)
    parsed_data = result.split()
    if len(parsed_data) > 25:
        interfaces[interface].before_rx_errors = parsed_data[9]
        interfaces[interface].before_tx_errors = parsed_data[22]
    time.sleep(30)
    cmd = "sudo ip -s link show " + interface.lower() + r' | grep "RX\|TX" -A 1'
    result = send_command_to_server(cmd, server)
    parsed_data = result.split()
    if len(parsed_data) > 25:
        interfaces[interface].after_rx_errors = parsed_data[9]
        interfaces[interface].after_tx_errors = parsed_data[22]
    animate_timer += 1


def top_border(interface: str, provider: str):
    print(f"\n  {interface}: ", end="")
    print(tcolor(f"({provider[:10]})", color="white"), end="")
    print(tcolor("\n  -----------------------", color="white"))


def print_report(interface: str, mode=""):
    """Takes the Interface Class and calculates if there is a problem with the interface"""
    if mode == "Diagnostic":
        top_border(interface, interfaces[interface].provider)
        print(f"  Light_Level: {interfaces[interface].light_level} dBm")
        print(tcolor("  -----------------------", color="white"))
        return
    RX_Errors = int(interfaces[interface].after_rx_errors) - int(
        interfaces[interface].before_rx_errors
    )
    TX_Errors = int(interfaces[interface].after_tx_errors) - int(
        interfaces[interface].before_tx_errors
    )
    CRC_Errors = int(interfaces[interface].after_crc_errors) - int(
        interfaces[interface].before_crc_errors
    )
    Light_Level = interfaces[interface].light_level
    Packet_Loss = interfaces[interface].packet_loss
    top_border(interface, interfaces[interface].provider)
    print_metric(
        interface, "RX_Errors:", RX_Errors, validate_metric(float(RX_Errors), 0.0, 1.0)
    )
    print_metric(
        interface, "TX Errors:", TX_Errors, validate_metric(float(TX_Errors), 0.0, 1.0)
    )
    print_metric(
        interface,
        "CRC_Errors:",
        CRC_Errors,
        validate_metric(float(CRC_Errors), 0.0, 1.0),
    )
    if interfaces[interface].speed == "100G":
        print_light_level_array(interface, Light_Level)
    else:
        print_metric(
            interface,
            "Light_Level:",
            Light_Level,
            validate_metric(float(Light_Level), -9.0, -11.0, "light"),
        )
    print_metric(
        interface, "Packet_Loss:", Packet_Loss, validate_metric(Packet_Loss, 0.4, 0.1)
    )
    print(tcolor("  -----------------------", color="white"), end="")


def print_metric(interface: str, label: str, value: int, color_c: str):
    if label == "Packet_Loss:":
        value = str(value) + "%"
    if color_c == "red":
        interfaces[interface].problem = True
    print(tcolor(f"  {label} "), end="")
    print(tcolor(f"{value}", color=color_c))


def print_light_level_array(interface: str, light_level: list):
    print("  Light_Level:")
    for light in light_level:
        value = "     "
        color = validate_metric(float(light), -9.0, -11.0, "light")
        if "-" not in light:
            value = "      "
        print_metric(interface, value, light, color)


def no_light_check(light: list, interface: str) -> bool:
    if type(light) == list:
        for level in light:
            if level == -99:
                interfaces[interface].problem = True
                return True
    elif light == -99:
        interfaces[interface].problem = True
        return True
    return False


def validate_metric(metric: float, l_limit: float, u_limit: float, itype="") -> str:
    """For a given metric, assigns a color to the value based on lower and upper limits"""
    if itype == "light":
        if metric < u_limit or metric == -99:
            return "red"
        elif metric < l_limit:
            return "yellow"
    elif itype == "":
        if metric > u_limit or metric == -99:
            return "red"
        elif metric > l_limit:
            return "yellow"
    else:
        return "white"


def print_splash_screen():
    """ASCII Art for when the script starts"""
    print("       _________")
    print("      / ======= \\")
    print("     / __________\\")
    print("    | ___________ |")
    print("    | | -       | |")
    print("    | |         | |  Interface Checker")
    print("  __| |_________| |______________________")
    print("    \\=____________/")
    print('    / """"""""""" \\')
    print("   / ::::::::::::: \\")
    print("  (_________________)\n")


def make_mode_choice() -> str:
    n_mode = "{:<20}".format("Normal")
    d_mode = "{:<20}".format("Diagnostic")
    cli = Bullet(
        prompt="  Choose which mode: ",
        choices=[n_mode, d_mode],
        word_on_switch=colors.foreground["green"],
        bullet_color=colors.foreground["green"],
        word_color=colors.foreground["white"],
        bullet="→",
        shift=1,
        margin=1,
    )
    result = cli.launch()
    print("")
    return result


def make_diagnostic_choice() -> list:
    int_list = []
    for _, value in interfaces.items():
        int_string = "{:<10}".format(value.name[:8]) + " "
        int_list.append(int_string)
    cli = Bullet(
        prompt="  Choose from the interfaces below: ",
        choices=int_list,
        word_on_switch=colors.foreground["green"],
        bullet_color=colors.foreground["green"],
        word_color=colors.foreground["white"],
        bullet="→",
        shift=1,
        margin=1,
    )
    result = cli.launch()
    print("")
    return [result.split()[0]]


def make_interface_choice() -> list:
    int_list = []
    for _, value in interfaces.items():
        int_string = "{:<10}".format(value.name[:8]) + " "
        int_string += "{:<10}".format(value.provider[:8]) + " "
        int_string += "{:<10}".format(value.itype[:8]) + " "
        int_string += "{:<19}".format(value.mac) + " "
        int_string += "{:<15}".format(value.status[:15]) + " "
        int_list.append(int_string)
    cli = Check(
        prompt="  Select from the interfaces below: (Using Spacebar)",
        choices=int_list,
        check_on_switch=colors.foreground["green"],
        word_on_switch=colors.foreground["green"],
        check_color=colors.foreground["green"],
        word_color=colors.foreground["white"],
        check="√",
        shift=1,
        margin=1,
    )
    temp_list = []
    for result in cli.launch():
        temp_list.append(result.split()[0])
    print("")
    return temp_list


def netbox_collect_interfaces(server: str, mode="Normal"):
    print("  Collecting Netbox Data...", end="\r")
    nb = netbox.Netbox()
    nb_server = nb.get_server(server)
    if not nb_server:
        print("  Sorry, you did not enter a valid server name\n")
    for nb_iface in nb.get_server_ifaces(nb_server):
        nb_circuit = nb.get_iface_circuit(nb_iface)
        if nb_circuit is not None and mode == "Normal":
            key = str(nb_iface)[:]
            interfaces[key] = Interface()
            interfaces[key].name = key[:]
            interfaces[key].mac = nb_iface.mac_address[:]
            interfaces[key].circuit_id = nb_circuit.cid[:]
            interfaces[key].provider = nb_circuit.provider.name[:]
            interfaces[key].status = nb_circuit.status.label[:]
            interfaces[key].itype = convert_circuit_type_names(nb_circuit.type.name[:])
            interfaces[key].ip = find_circuit_ip(nb, nb_iface)
        elif nb_circuit is None and mode == "Diagnostic":
            key = str(nb_iface)[:]
            interfaces[key] = Interface()
            interfaces[key].name = key[:]
            interfaces[key].status = "Unconfigured"


def find_circuit_ip(nb: object, interface: object):
    nb_ips = nb.get_iface_ips(interface, family=4)
    for ip in nb_ips:
        ip_tags = [t.slug for t in ip.tags]
        if "circuit-interface-ip" in ip_tags:
            return ip.address[:]


def convert_circuit_type_names(circuit: str) -> str:
    if "IP Trans" in circuit:
        circuit = "Transit"
    if "IXP" in circuit:
        circuit = "IXP"
    if "Private" in circuit:
        circuit = "PNI"
    if "Backbone" in circuit:
        circuit = "Wave"
    return circuit


def animate(count: int, msg: str):
    global animate_timer
    msg += "........................"
    while animate_timer < count:
        print("{:<44}".format(msg[:44]) + "[", end="")
        print(tcolor("Loading " + "\b |", color="yellow"), end="")
        print("]", end="\r")
        time.sleep(0.1)
        print("{:<44}".format(msg[:44]) + "[", end="")
        print(tcolor("Loading " + "\b /", color="yellow"), end="")
        print("]", end="\r")
        time.sleep(0.1)
        print("{:<44}".format(msg[:44]) + "[", end="")
        print(tcolor("Loading " + "\b -", color="yellow"), end="")
        print("]", end="\r")
        time.sleep(0.1)
        print("{:<44}".format(msg[:44]) + "[", end="")
        print(tcolor("Loading " + "\b \\", color="yellow"), end="")
        print("]", end="\r")
        time.sleep(0.1)


def loop_threaded_function(server: str, interface: str, func: str, msg=""):
    global animate_timer
    threading.Thread(target=func, args=(server, interface)).start()
    animate(1, msg)
    animate_timer = 0
    print_complete(msg)


def loop_threaded_functions(server: str, interface_list: list, func: str, msg=""):
    global animate_timer
    for interface in interface_list:
        threading.Thread(target=func, args=(server, interface)).start()
    animate(len(interface_list), msg)
    animate_timer = 0
    print_complete(msg)


def pipeline_mode(server: str, interface: str = ""):
    print("")
    netbox_collect_interfaces(server, "Normal")
    loop_threaded_function(
        server, interface, is_interface_up, "  Validating Interfaces are UP"
    )
    loop_threaded_function(
        server, interface, check_light_levels, "  Gathering Light Levels"
    )
    loop_threaded_function(
        server, interface, check_packet_loss, "  Gathering Packet Loss"
    )
    loop_threaded_function(
        server,
        interface,
        check_incrementing_crc_errors,
        "  Gathering Incrementing CRC Errors",
    )
    loop_threaded_function(
        server,
        interface,
        check_rx_and_tx_incrementing_errors,
        "  Gathering Incrementing RX and TX Errors",
    )
    print("\n  Report Printout:")
    print_report(interface)
    print("")
    if interfaces[interface].problem is True:
        print(f"  {interface} has an issue")


def return_interfaces(server: str, mode="") -> list:
    if mode == "Diagnostic":
        interface_list = make_diagnostic_choice()
    else:
        interface_list = make_interface_choice()
    if interface_list is None:
        print("  You must make an interface selection to proceed")
        sys.exit(1)
    return interface_list


def diagnostic_mode(server: str, mode: str):
    netbox_collect_interfaces(server, mode)
    interface_list = return_interfaces(server, mode)
    loop_threaded_functions(
        server, interface_list, check_light_levels, "  Gathering Light Levels"
    )
    for interface in interface_list:
        print_report(interface, "Diagnostic")
    sys.exit(1)


def normal_mode(server: str, mode: str):
    problem_ints = []
    interface_list = []
    netbox_collect_interfaces(server)
    if mode == "Entire_Server":
        for key in interfaces:
            interface_list.append(key)
    else:
        interface_list = return_interfaces(server, mode)
        if not interface_list:
            print("You must make an interface selection")
            sys.exit(1)
    loop_threaded_functions(
        server, interface_list, is_interface_up, "  Validating Interfaces are UP"
    )
    loop_threaded_functions(
        server, interface_list, check_light_levels, "  Gathering Light Levels"
    )
    loop_threaded_functions(
        server, interface_list, check_packet_loss, "  Gathering Packet Loss"
    )
    loop_threaded_functions(
        server,
        interface_list,
        check_incrementing_crc_errors,
        "  Gathering Incrementing CRC Errors",
    )
    loop_threaded_functions(
        server,
        interface_list,
        check_rx_and_tx_incrementing_errors,
        "  Gathering Incrementing RX and TX Errors",
    )
    print("\n  Report Printout:")
    for interface in interface_list:
        print_report(interface)
        if interfaces[interface].problem is True:
            problem_ints.append(str(interfaces[interface].name))
    print("\n")
    if problem_ints:
        print(tcolor("  The following interfaces have issues: ", color="white"), end="")
        print(tcolor(str([x for x in problem_ints]), color="red"))
    else:
        print(tcolor("  There were no issues found", color="green"))


def main():
    server = input("  Please enter the server name: ")
    print("")
    mode = make_mode_choice().rstrip()
    if mode == "Diagnostic":
        diagnostic_mode(server, mode)
    else:
        normal_mode(server, mode)


if __name__ == "__main__":
    args = arg_parse()
    if args.server and args.interface:
        pipeline_mode(args.server, args.interface)
    elif args.server:
        print()
        normal_mode(args.server, "Entire_Server")
    else:
        print_splash_screen()
        main()
