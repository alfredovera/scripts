#!/usr/bin/env python3
import argparse
import sys
import webbrowser
from pprint import pprint

from lib import awx, general


def arg_parse():
    parser = argparse.ArgumentParser(description="Run a build phase from AWX")
    parser.add_argument("server", type=str, help="The server name to query for")
    parser.add_argument(
        "-p",
        "--phase",
        choices=["2", "3"],
        required=True,
        help="Select the phase to run",
    )
    return parser.parse_args()


def main():
    general.preliminary_checks(["AWX_API_TOKEN"])
    a = awx.AWX()
    run_phase = {
        "phase2": a.phase2_single_slice,
        "phase3": a.phase3_single_slice,
    }

    output = run_phase[phase](server)
    job_id = output.get("job", None)
    if job_id:
        webbrowser.open_new_tab(
            f"https://awx.global.ftlprod.net/#/jobs/playbook/{job_id}/output"
        )
        print("Job ID:", job_id)
    else:
        print("Didn't receive the job_id, verify manually.")
        pprint(output)
        sys.exit(1)


if __name__ == "__main__":
    args = arg_parse()
    server = args.server
    phase = f"phase{args.phase}"
    main()
