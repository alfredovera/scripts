import os
import sys

import requests

AWX_API_TOKEN = "AWX_API_TOKEN"
AWX_URL = "https://awx.global.ftlprod.net/api/v2"


class AWX:
    """
    This AWX class requires an API token.
    This can be generated at https://awx.global.ftlprod.net/ in your user details once logged on.

    Add this string to your profile:
    export AWX_API_TOKEN=<your_api_token>

    Each of the execution tasks does a lookup to find the specific ID instead of having the ID static in the code.
    """

    def __init__(self):
        self.api_token = os.environ[AWX_API_TOKEN]
        self.awx_url = AWX_URL
        self.header = {"Authorization": "Bearer %s" % self.api_token}

    def _get_exact_jobname(self, job_type: str, job_name: str):
        params = {"search": job_name}
        try:
            response = requests.get(
                f"{self.awx_url}/{job_type}", headers=self.header, params=params
            ).json()
        except Exception as error:
            raise ConnectionError(f"Failed retrieve data from AWX: {error}")
        return [
            entry
            for entry in response.get("results", [])
            if entry.get("name") == job_name
        ]

    @staticmethod
    def _present_results(results: list) -> None:
        for entry in results:
            print("---")
            print("name:", entry.get("name", ""))
            print("id:", entry.get("id", ""))
            print("description:", entry.get("description", ""))
            print("type:", entry.get("type", ""))

    def _get_id(self, job_type: str, job_name: str) -> str:
        output = self._get_exact_jobname(job_type=job_type, job_name=job_name)
        if len(output) == 1:
            return output[0].get("id")
        else:
            print(f"Expected a single result, got '{len(output)}'. Please investigate.")
            self._present_results(output)
            sys.exit(1)

    def phase2_single_slice(self, limit: str):
        id = self._get_id(job_type="job_templates", job_name="Phase 2")
        job_url = f"/job_templates/{id}/launch/"
        params = {"limit": limit}
        response = requests.post(
            f"{self.awx_url}{job_url}", headers=self.header, json=params
        )
        return response.json()

    def phase3_single_slice(self, limit: str):
        id = self._get_id(job_type="job_templates", job_name="Phase 3")
        job_url = f"/job_templates/{id}/launch/"
        params = {"limit": limit}
        response = requests.post(
            f"{self.awx_url}{job_url}", headers=self.header, json=params
        )
        return response.json()

    def register_pop(self, limit: str):
        id = self._get_id(job_type="job_templates", job_name="Register")
        job_url = f"/job_templates/{id}/launch/"
        params = {"limit": limit}
        response = requests.post(
            f"{self.awx_url}{job_url}", headers=self.header, json=params
        )
        return response.json()

    def update_dns(self, limit: str):
        id = self._get_id(job_type="job_templates", job_name="Update DNS")
        job_url = f"/job_templates/{id}/launch/"
        params = {"limit": limit}
        response = requests.post(
            f"{self.awx_url}{job_url}", headers=self.header, json=params
        )
        return response.json()

    def sync_invenstory(self):
        id = self._get_id(job_type="workflow_job_templates", job_name="Sync Inventory")
        job_url = f"/workflow_job_templates/{id}/launch/"
        response = requests.post(f"{self.awx_url}{job_url}", headers=self.header)
        return response.json()

    def get_job_status(self, job_id: str) -> str:
        # try jobs first, if not, workflow
        status = self.jobs_status(job_id)
        if not status:
            status = self.workflow_job_status(job_id)
        return status

    def jobs_status(self, job_id: str) -> str:
        job_url = f"/jobs/{job_id}/"
        response = requests.get(f"{self.awx_url}{job_url}", headers=self.header).json()
        status = response.get("status", None)
        if status:
            return f"job: {response.get('name')}, status: {status}, server: {response.get('limit')}"
        else:
            return ""

    def workflow_job_status(self, job_id: str) -> str:
        job_url = f"/workflow_jobs/{job_id}/"
        response = requests.get(f"{self.awx_url}{job_url}", headers=self.header).json()
        status = response.get("status", None)
        if status:
            return f"Job name: {response.get('name')} \tstatus: {status}"
        else:
            return ""
