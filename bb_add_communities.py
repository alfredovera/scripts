#!/usr/bin/env python3
import argparse
import sys

from lib import billboard, general


def arg_parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
    Add (merge) comumnities for existing paths.

    Billboard will be updated with a unique list of communities combined of
    existing entries combined with the newly provided ones

    To add the same communities to various peer IP's this could be used:
        COMMUNITY=0:60294,0:3216,0:9605,0:16345,0:8369,0:31200,0:18001,0:15600,0:8821,0:21051,0:12355,0:41275,0:8758,0:50581
        bb_add_communities.py $SERVER PEER_IP1 $COMMUNITY
        bb_add_communities.py $SERVER PEER_IP2 $COMMUNITY
        bb_add_communities.py $SERVER PEER_IP3 $COMMUNITY
        bb_add_communities.py $SERVER PEER_IP4 $COMMUNITY
        """,
    )
    parser.add_argument("server", type=str, help="The server name to apply to")
    parser.add_argument("peer_ip", type=str, help="The peer_ip to apply to")
    parser.add_argument(
        "new_communities",
        type=str,
        help="The communities to add (merge). e.g. '0:9299,0:6939,0:57463'",
    )
    return parser.parse_args()


def extract_parse_paths() -> list[billboard.ParsedDict]:
    bb_path_parsed: list[billboard.ParsedDict] = []
    path_types = ("prod_global", "monitor")

    new_unique = set()
    if new_communities:
        new_unique = billboard.normalize_communities_entries_separated_by_comma(
            new_communities
        )

    for t in path_types:
        get_cmd = f"billboard get path hostname={server} ip={peer_ip} type={t}"
        proc, output, errors = general.shell_cmd(get_cmd, shell=True)

        if not output:
            print("No output from billboard command.")
            print(proc)
            print(errors)
            sys.exit(2)

        # bb_path_parsed = bb_path_parsed + parse_path_output(output)
        bb_path_parsed = bb_path_parsed + billboard.parse_path_output_and_communities(
            output, new_unique
        )
    return bb_path_parsed


def execute_new_com(bb_path_parsed: list[billboard.ParsedDict]) -> None:
    """
    Given the list of dicts with parsed billboard data
    the billboard update commands are generated and executed directly.
    """
    for bb in bb_path_parsed:
        cmd = f"billboard update path {server} {peer_ip} prefix={bb['prefix']} prefix_len={bb['prefixlen']} type={bb['path_type']} communities=\"{bb['communities']}\""  # noqa
        _, output, errors = general.shell_cmd(cmd, shell=True, communicate_input="y\n")
        print(output)
        if errors:
            print("errors:", errors)


def main() -> None:
    general.preliminary_checks(["BILLBOARD_API_TOKEN"])
    bb_path_parsed = extract_parse_paths()
    execute_new_com(bb_path_parsed)


if __name__ == "__main__":
    args = arg_parse()
    server = args.server
    peer_ip = args.peer_ip
    new_communities = args.new_communities
    main()
