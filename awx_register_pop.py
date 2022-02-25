#!/usr/bin/env python3
import argparse
import sys
from pprint import pprint

from lib import awx, general


def arg_parse():
    parser = argparse.ArgumentParser(description="Run a build phase from AWX")
    parser.add_argument("server", type=str, help="The server name to query for")
    return parser.parse_args()


def main():
    general.preliminary_checks(["AWX_API_TOKEN"])
    a = awx.AWX()

    output = a.register_pop(server)
    job_id = output.get("job", None)
    if job_id:
        print("To see the output of the job:")
        print(
            f"Job ID: {job_id}\thttps://awx.global.ftlprod.net/#/jobs/playbook/{job_id}/output"
        )
    else:
        print("Didn't receive the job_id, verify manually.")
        pprint(output)
        sys.exit(1)


if __name__ == "__main__":
    args = arg_parse()
    server = args.server
    main()
