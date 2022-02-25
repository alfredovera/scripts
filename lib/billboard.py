import os
import typing
from dataclasses import dataclass
from subprocess import Popen

from .general import shell_cmd, ansible_is_alpha
from .credentials import sops_envfile

bb_path_parsed_type = list[dict[str, typing.Union[str, set[str]]]]


class ParsedDict(typing.TypedDict):
    hostname: str
    peername: str
    asn: str
    peer_ip: str
    prefix: str
    prefixlen: str
    path_type: str
    path_state: str
    prependedAS: str
    communities: str


@dataclass
class bb_dataclass:
    provider: str = ""
    AS: str = ""
    peer_ip: str = ""
    peer_type: str = ""
    state: str = "disabled"
    max_prefixes: str = ""
    filter_regex: str = ""
    interface: str = ""
    interface_state: str = ""


# absolute path of library directory
LIB_DIR = f"{os.path.dirname(__file__)}"


def billboard_runner(cmd: str, server: str) -> tuple[Popen[str], str, str]:

    if ansible_is_alpha(server):
        ckey = "BILLBOARD_API_ALPHA"
        billboard_host = "billboard.subspace-alpha.com"
    else:
        ckey = "BILLBOARD_API_PROD"
        billboard_host = "billboard.subspace.com"

    bb_token_path = f"{LIB_DIR}/../../../secrets/ironroots/ansible/ansible-secrets.env"
    bb_token = sops_envfile(bb_token_path, ckey)
    bb_env = dict(os.environ.copy(), BILLBOARD_API_TOKEN=bb_token)

    bb_cmd = f"billboard --host {billboard_host} " + cmd
    proc, output, errs = shell_cmd(
        bb_cmd, shell=True, communicate_input="y\n", shell_env=bb_env
    )

    return proc, output, errs


def get_peer_data(server: str) -> str:
    cmd = f"get peer hostname={server}"
    _, output, _ = billboard_runner(cmd, server)
    return output


def get_billboard_path_data(server: str) -> str:
    cmd = f"get path hostname={server}"
    _, output, _ = billboard_runner(cmd, server)
    return output


def parse_peer_data(data: str) -> list[bb_dataclass]:
    """
    data:
    Hostname      Name                  AS          IP                                    Type          State     MaxPrefix   FilterASRegex  # noqa
    sub-mxp01-data01  cogent                174         2001:978:2:2a::61:1                   IPT_GLOBAL    ENABLED   0           []         # noqa
    sub-mxp01-data01  cogent                174         149.14.134.49                         IPT_GLOBAL    ENABLED   0           []         # noqa
    """
    billboard_data = []
    # don't use the header
    data_list = data.split("\n")[1:]
    for x in data_list:
        line = x.split()
        billboard_data.append(
            #            provider, AS,     peer_ip, type,    state,   max_prefixes, filter_regex
            bb_dataclass(line[1], line[2], line[3], line[4], line[5], line[6], line[7])
        )
    return billboard_data


def get_parsed_peer_data(server: str) -> list[bb_dataclass]:
    peer_data = get_peer_data(server=server)
    return parse_peer_data(data=peer_data)


def get_parsed_path_data(server: str) -> list[ParsedDict]:
    path_data = get_billboard_path_data(server=server)
    return parse_path_output(get_path_output=path_data)


def billboard_undrain(server: str, path_types: str = "prod_global,monitor") -> tuple:
    cmd = f"undrain agent {server} path_types={path_types}"
    return billboard_runner(cmd, server)


def billboard_drain(server: str) -> tuple:
    cmd = f"drain agent {server} path_types=prod_global,monitor"
    return billboard_runner(cmd, server)


def normalize_communities_entries_separated_by_comma(
    communities: str,
) -> set[str]:
    new_unique = communities.split(",")
    return {x.strip() for x in new_unique}


def parse_path_output(get_path_output: str) -> list[ParsedDict]:
    """
    Parses the output of the billboard get path into a dictionary.

    bb_get_path:
    Hostname          PeerName              AS          PeerIP                                Prefix                                Len  Type              State     PrependAS  Communities  # noqa
    sub-eze01-data01  tisparkle             6762        185.70.203.32                         143.131.181.0                         24   PROD_GLOBAL       DISABLED  0          []  # noqa

    returns:
    [{
        "hostname": hostname,
        "peername": peername,
        "asn": asn,
        "peer_ip": peer_ip,
        "prefix": prefix,
        "prefixlen": prefixlen,
        "path_type": path_type,
        "path_state": path_state,
        "prependedAS": prependedAS,
        "communities": set_current,
    }]
    """
    # get_path_output example
    # Hostname          PeerName              AS          PeerIP                                Prefix                                Len  Type              State     PrependAS  Communities  # noqa
    # sub-eze01-data01  tisparkle             6762        185.70.203.32                         143.131.181.0                         24   PROD_GLOBAL       DISABLED  0          []  # noqa

    # new_communities
    # 0:9299,0:6939,0:57463,0:9002,0:8400,0:8447,0:9498
    parsed_list = []
    for entry in get_path_output.split("\n")[1:]:
        (
            hostname,
            peername,
            asn,
            peer_ip,
            prefix,
            prefixlen,
            path_type,
            path_state,
            prependedAS,
            *extract_communities,
        ) = entry.split()
        # Make a string from the current communities again
        current_communities = " ".join(extract_communities)
        # set_current = set(current_communities.strip("[]").split())
        set_current_str = ",".join(set(current_communities.strip("[]").split()))

        parsed_dict: ParsedDict = {
            "hostname": hostname,
            "peername": peername,
            "asn": asn,
            "peer_ip": peer_ip,
            "prefix": prefix,
            "prefixlen": prefixlen,
            "path_type": path_type,
            "path_state": path_state,
            "prependedAS": prependedAS,
            "communities": set_current_str,
        }
        parsed_list.append(parsed_dict)
    return parsed_list


def parse_path_output_and_communities(
    get_path_output: str, new_communities: set[str]
) -> list[ParsedDict]:

    parsed_output = parse_path_output(get_path_output=get_path_output)

    for path in parsed_output:
        path["communities"] = ",".join(
            set.union(set(path["communities"].split(",")), new_communities)
        )
    return parsed_output


def path_sort(bb_path_parsed: list[ParsedDict]) -> dict[str, dict[str, set[str]]]:
    """
    returns:
    {
        $peer_ip = {
            # each key/value is optional
            "PROD_GLOBAL": [ip/mask, ip/mask, ...],
            "INT_LOCAL": [ip/mask, ip/mask, ...],
            "MONITOR": [ip/mask, ip/mask, ...],
            "SITE_LOCAL": [ip/mask, ip/mask, ...]
            "ENABLED": [ip/mask, ip/mask, ...]
            "DISABLED": [ip/mask, ip/mask, ...]
        }
    }
    """
    bb_sort: dict = {}

    for path in bb_path_parsed:
        peer_ip = path.get("peer_ip")
        bb_sort[peer_ip] = bb_sort.get(peer_ip, {})

        path_type = path.get("path_type")
        subnet = f"{path['prefix']}/{path['prefixlen']}"
        bb_sort[peer_ip][path_type] = bb_sort[peer_ip].get(path_type, set())
        bb_sort[peer_ip][path_type].add(subnet)

        # fill ENABLED or DISABLED key (or potentially another one)
        bb_sort[peer_ip][path.get("path_state")] = bb_sort[peer_ip].get(
            path.get("path_state"), set()
        )
        bb_sort[peer_ip][path.get("path_state")].add(subnet)

    return bb_sort
