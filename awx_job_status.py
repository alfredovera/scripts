#!/usr/bin/env python3
import argparse

from lib import awx, general


def arg_parse():
    parser = argparse.ArgumentParser(description="Get the job status from AWX")
    parser.add_argument("job_id", type=str, help="The job ID to query for")
    return parser.parse_args()


def main():
    general.preliminary_checks(["AWX_API_TOKEN"])
    a = awx.AWX()
    print(a.get_job_status(job_id))


if __name__ == "__main__":
    args = arg_parse()
    job_id = args.job_id
    main()
