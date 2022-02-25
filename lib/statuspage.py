import os
import typing

import airports
import regions
import requests

from . import general

STATUSPAGE_API_TOKEN = "STATUSPAGE_API_TOKEN"
URL = "https://api.statuspage.io/v1/pages"
COMPONENT_PAGE_ID = "p8ggy6gzy9bw"


class StatusPage:
    """
    This class is used to update the subspace.statuspage.io page.
    """

    def __init__(self):
        self.url = URL
        self.component_page_id = COMPONENT_PAGE_ID
        self.header = {
            "Authorization": "OAuth %s" % os.getenv("STATUSPAGE_API_TOKEN"),
            "content-type": "application/json",
        }
        self.comp_url = f"{self.url}/{self.component_page_id}/components"
        self.comp_group_url = f"{self.url}/{self.component_page_id}/component-groups"
        self.existing_components = []
        self.component_group_id = {}
        self.existing_component_groups = []
        self.active_billboard_pops = []

        self.initial_setup()

    def initial_setup(self) -> None:
        """Prepare the dependencies:
        The component IDs (servers)
        The group IDs
        A mapping of the region to the ID
        """
        self.get_components()
        self.get_component_groups()
        self.map_region_with_group_id()

    def get_components(self) -> list[dict[str, str]]:
        """Get a list of dicts of current components used by the webpage"""
        self.existing_components = self._get_api_call(url=self.comp_url).json()
        return self.existing_components

    def get_component_groups(self) -> typing.Any:
        """Get a list of dicts of current component groups used by the webpage"""
        self.existing_component_groups = self._get_api_call(
            url=self.comp_group_url
        ).json()
        return self.existing_component_groups

    def map_region_with_group_id(self) -> dict[str, str]:
        self.component_group_id = {
            x["name"].split()[-1]: x["id"] for x in self.existing_component_groups
        }
        return self.component_group_id

    @staticmethod
    def get_short_name(hostname: str) -> str:
        """
        Out of these options:
            sub-xxxyy-data01
            xxxyy-data01
            lln-xxxyy-data01
            nnm-xxxyy-data01

        it returns:
            xxxyy
        """
        _, site_name = general.get_server_site(hostname)
        return site_name.upper()

    def _get_existing_component_id(self, short_name: str) -> str:
        entries = [
            x for x in self.existing_components if short_name in x.get("name", "")
        ]
        if len(entries) == 1:
            return entries[0].get("id", "")
        elif len(entries) > 1:
            raise SystemExit(
                f"More than one entry found for {short_name}. Entries: {entries}"
            )
        else:
            return ""

    def get_airport_details(self, hostname: str) -> airports.Airport:
        """
        returns: (airports.Airport)
            continent: "EU"
            coordinates: '4.76389, 52.308601'
            iadata: "AMS"
            iso_country: "NL"
            municipality: "Amsterdam"
            name: "Amsterdam Airport Schiphol"
        """
        airport_lookup = airports.Airports()
        airport_code_upper = self.get_short_name(hostname)[0:3]
        airport = airport_lookup.lookup(airport_code_upper)
        if airport is None:
            raise ValueError(
                f"{airport_code_upper} is not based on a valid IATA airport code"
            )
        return airport

    @staticmethod
    def get_region_details(airport: airports.Airport) -> regions.Region:
        """
        returns: (regions.Region)
            iso_country: "NL"
            name: "Netherlands"
            region: "Europe"
            sub_region: "Western Europe"
        """
        r = regions.Regions()
        return r.lookup(airport.iso_country)

    def get_title_description_region(self, hostname: str) -> tuple[str, str, str]:
        short_name = self.get_short_name(hostname)
        airport = self.get_airport_details(hostname)
        region = self.get_region_details(airport)

        title = f"{airport.iso_country} - {airport.municipality} - {short_name}"
        description = f"Region: {region.region}, \nCountry: {region.name}"
        return title, description, region.region

    def _get_api_call(self, url: str) -> requests.Response:
        try:
            response = requests.get(url, headers=self.header)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise SystemExit(e)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)
        return response

    def _patch_api_call(self, url: str, component: dict = None) -> requests.Response:
        try:
            response = requests.patch(url, headers=self.header, json=component)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise SystemExit(e)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)
        return response

    def _post_api_call(self, url: str, component: dict = None) -> requests.Response:
        try:
            response = requests.post(url, headers=self.header, json=component)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise SystemExit(e)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)
        return response

    def _delete_api_call(self, url: str, component: dict = None) -> requests.Response:
        try:
            response = requests.delete(url, headers=self.header, json=component)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise SystemExit(e)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)
        return response

    def create_component(
        self, hostname: str, status: str = "under_maintenance"
    ) -> typing.Any:
        component_id = self.get_id_by_hostname(hostname=hostname)
        if component_id:
            return False

        title, description, region = self.get_title_description_region(hostname)
        # status: Enum: "operational" "under_maintenance" "degraded_performance" "partial_outage" "major_outage" ""
        component = {
            "component": {
                "name": title,
                "description": description,
                "status": status,
                "only_show_if_degraded": False,
                "group_id": self.component_group_id[region],
                "showcase": True,
            }
        }
        output = self._post_api_call(url=self.comp_url, component=component)
        self.existing_components.append(output.json())
        return output

    def update_component(
        self,
        hostname: str,
        status: str = None,
    ) -> typing.Any:

        title, description, region = self.get_title_description_region(hostname)
        id = self.get_id_by_hostname(hostname)

        if not id:
            print("Server not found. Creating a new instance.")
            if status:
                print(f"  Setting status to: '{status}'")
                output = self.create_component(hostname, status)
            else:
                output = self.create_component(hostname)
            return output

        comp_id_url = f"{self.comp_url}/{id}"
        component = {
            "component": {
                "name": title,
                "description": description,
                "only_show_if_degraded": False,
                "group_id": self.component_group_id[region],
                "showcase": True,
            }
        }
        if status:
            component["component"]["status"] = status

        return self._patch_api_call(url=comp_id_url, component=component)

    def delete_component(self, hostname: str) -> typing.Any:
        """
        hostname: the server hostname
        """
        id = self.get_id_by_hostname(hostname)
        if not id:
            print(f"Server '{hostname}' not found.")
            return None

        comp_id_url = f"{self.comp_url}/{id}"
        return self._delete_api_call(url=comp_id_url)

    def get_component(self, hostname: str) -> dict:
        """
        hostname: the server hostname
        """
        if not (id := self.get_id_by_hostname(hostname)):
            return {}
        comp_id_url = f"{self.comp_url}/{id}"

        output = self._get_api_call(url=comp_id_url).json()
        return output

    def get_id_by_hostname(self, hostname: str) -> str:
        short_name = self.get_short_name(hostname)
        return self._get_existing_component_id(short_name)

    def set_status_operational(self, hostname: str) -> typing.Any:
        return self.update_component(hostname, "operational")

    def set_status_maintenance(self, hostname: str):
        return self.update_component(hostname, "under_maintenance")
