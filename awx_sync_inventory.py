#!/usr/bin/env python3
import sys
from pprint import pprint

from lib import awx, general


def main():
    general.preliminary_checks(["AWX_API_TOKEN"])
    a = awx.AWX()
    output = a.sync_invenstory()
    job_id = output.get("workflow_job", None)
    if job_id:
        print("To see the output of the job: (will take around 1m45)")
        print(
            f"Job ID: {job_id}\thttps://awx.global.ftlprod.net/#/jobs/workflow/{job_id}/output"
        )
    else:
        print("Didn't receive the job_id, verify manually.")
        pprint(output)
        sys.exit(1)


if __name__ == "__main__":
    main()
