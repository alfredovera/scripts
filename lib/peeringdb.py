import os

import requests

PEERINGDB_API_TOKEN = "PEERINGDB_API_TOKEN"
PEERINGDB_URL = "https://www.peeringdb.com"


class PeeringDB:
    """
    This PeeringDB class requires an API token.
    This can be generates at https://www.peeringdb.com/profile once logged on.

    Add this string to your profile:
    export PEERINGDB_API_TOKEN=<your_api_token>
    """

    def __init__(self):
        self.api_token = os.environ[PEERINGDB_API_TOKEN]
        self.url = PEERINGDB_URL
        self.url_path_net = "/api/net"
        self.url_path_poc = "/api/poc"
        self.header = {"AUTHORIZATION": "Api-Key %s" % self.api_token}

    def get_net_id(self, asn: str) -> str:
        net_params = {"asn": asn}
        try:
            response = requests.get(
                f"{self.url}{self.url_path_net}", headers=self.header, params=net_params
            )
            resp_json = response.json().get("data")
        except Exception:
            print("Error communicating to peeringDB api.")
            raise
        return resp_json[0].get("id")

    def get_noc_mail(self, net_id: str) -> str:
        noc_params = {"net_id": net_id, "role": "NOC"}
        try:
            response = requests.get(
                f"{self.url}{self.url_path_poc}", headers=self.header, params=noc_params
            )
            resp_json = response.json().get("data")
        except Exception:
            print("Error communicating to peeringDB api.")
            raise
        if not resp_json:
            return ""
        else:
            return resp_json[0].get("email")

    def get_poc_mail_all(self, net_id: str) -> list[dict]:
        poc_params = {"net_id": net_id}
        try:
            response = requests.get(
                f"{self.url}{self.url_path_poc}", headers=self.header, params=poc_params
            )
            resp_json = response.json().get("data")
        except Exception:
            print("Error communicating to peeringDB api.")
            raise

        details = [
            self._parse_entry(entry) for entry in resp_json if entry.get("email")
        ]

        return details

    @staticmethod
    def _parse_entry(entry: dict) -> dict[str, str]:
        return {
            "email": entry.get("email", ""),
            "role": entry.get("role", ""),
            "name": entry.get("name", ""),
            "status": entry.get("status", ""),
        }
