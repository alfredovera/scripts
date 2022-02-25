import os
import typing

import requests

# API requires username and token
ZENDESK_USERNAME = "ZENDESK_USERNAME"
ZENDESK_API_TOKEN = "ZENDESK_API_TOKEN"
URL = "https://subspace.zendesk.com/api/v2"


class Zendesk:
    """
    This Zendesk class requires an API token.
    This can be generated at https://subspace.zendesk.com/ in your user details once logged on.

    Add this string to your profile:
    export ZENDESK_USERNAME=<your_zendesk_email>
    export ZENDESK_API_TOKEN=<your_api_token>

    """

    def __init__(self):
        self.username = os.getenv(ZENDESK_USERNAME)
        self.api_token = os.getenv(ZENDESK_API_TOKEN)
        self.url = URL
        self.header = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.auth = (self.username + "/token", self.api_token)

    def create_ticket(
        self,
        requester: str,
        subject: str,
        body: str,
        peer_name: str = "",
        asn: str = "",
        partner_outreach: str = "yes",
        tags: list[str] = None,
        cc_emails: list[str] = None,
    ) -> dict:
        """[summary]

        Args:
            requester (str): The email address of the requester
            subject (str): The subject string of the ticket
            body (str): The body of the ticket
            peer_name (str, optional): peer_name string. Defaults to "".
            asn (str, optional): asn number. Defaults to "".
            partner_outreach (str, optional): To send out the initial ticket to the requester . Defaults to "yes".
            tags (list[str], optional): Free form tagging. Defaults to None.
            cc_emails (list[str], optional): Email addresses to assign as CC. Defaults to None.

        Returns:
            dict: The response of Zendesk of creating the ticket
        """
        ccs = self._cc_email_check(cc_emails)

        url = f"{self.url}/tickets"
        ticket = {
            "ticket": {
                "subject": subject,
                "comment": {"body": body},
                "requester": {
                    "name": requester,
                    "email": requester,
                },
                # "requester_id": self._get_my_user_id(),
                "assignee_id": self._get_my_user_id(),
                "email_ccs": self._email_ccs(ccs),
                "custom_fields": [
                    {"id": 1500009824442, "value": peer_name},  # Peer Name
                    {"id": 1900001486045, "value": asn},  # ASN
                    {
                        "id": 1500012461542,
                        "value": partner_outreach,
                    },  # partner outreach
                ],
                "tags": tags,
            }
        }
        response = self._post_api_call(url=url, json=ticket)

        try:
            return response.json()
        except Exception:
            print(
                f"Couldn't convert create ticket response to json.\n{subject = }, {requester = }\n{response = }"
            )
            raise

    def add_comment(
        self,
        ticket_id: int,
        comment: str,
        cc_emails: list[str] = None,
        public: bool = True,
    ) -> dict[str, dict[str, str]]:
        """Add a comment to an existing ticket

        Keep the following in mind when providing the comment:
        * tabs are ignored
        * consecutive spaces are reduced to one

        Args:
            ticket_id (str): the ticket ID to add the comment to
            comment (str): The body of the comment
            cc_emails (list[str], optional): A list of email address to assign as CC. Defaults to None.
            public (bool, optional): Make the comment public (default) or internal. Defaults to True.

        Returns:
            dict: the response of the API call in dict/json format
        """
        ccs = self._cc_email_check(cc_emails)

        url = f"{self.url}/tickets/{ticket_id}"
        ticket = {
            "ticket": {
                "comment": {
                    "body": comment,
                    "public": public,
                },
                "email_ccs": self._email_ccs(ccs),
            }
        }
        response = self._put_api_call(url=url, json=ticket)
        try:
            return response.json()
        except Exception:
            print(
                f"Couldn't convert add comment response to json.\n{ticket_id = }\n{response = }"
            )
            raise

    def _get_api_call(self, url: str, json: dict = None):
        """Internal function to call the Zendesk API using get.

        Args:
            url (str): the URL to send the request to
            json (dict, optional): Provide a dict to send. Defaults to None.

        Returns:
            [type]: [description]
        """
        try:
            response = requests.get(url, headers=self.header, auth=self.auth, json=json)
            response.raise_for_status()
        except Exception:
            print("Error communicating to Zendesk api.")
            raise
        return response

    def _put_api_call(self, url: str, json: dict = None):
        """Internal function to call the Zendesk API using put.

        Args:
            url (str): the URL to send the request to
            json (dict, optional): Provide a dict to send. Defaults to None.

        Returns:
            [type]: [description]
        """
        try:
            response = requests.put(url, headers=self.header, auth=self.auth, json=json)
            response.raise_for_status()
        except Exception:
            print("Error communicating to Zendesk api.")
            raise
        return response

    def _post_api_call(self, url: str, json: dict = None):
        """Internal function to call the Zendesk API using post.

        Args:
            url (str): the URL to send the request to
            json (dict, optional): Provide a dict to send. Defaults to None.

        Returns:
            [type]: [description]
        """
        try:
            response = requests.post(
                url, headers=self.header, auth=self.auth, json=json
            )
            response.raise_for_status()
        except Exception:
            print("Error communicating to Zendesk api.")
            raise
        return response

    def get_ticket(self, ticket_id: typing.Union[str, int]) -> dict:
        """Get the json output for the prvoided ticket number

        Args:
            ticket_id (str, int): the ticket ID to request

        Returns:
            dict: a dictionary with the ticket information {"ticket": {...}}
        """
        url = f"{self.url}/tickets/{ticket_id}"
        response = self._get_api_call(url=url).json()
        return response

    def get_comments(self, ticket_id: typing.Union[str, int]) -> dict:
        """Get the json output for the comments for the prvoided ticket number

        Args:
            ticket_id (str, int): the ticket ID to request

        Returns:
            dict: a dictionary with the ticket information {"ticket": {...}}
        """
        url = f"{self.url}/tickets/{ticket_id}/comments"
        response = self._get_api_call(url=url).json()
        return response

    def get_user(self, user_id: typing.Union[str, int]):
        """Get the json output for the prvoided user

        Args:
            user_id (str, int): the user ID to request

        Returns:
            dict: a dictionary with the user information {"user": {...}}
        """
        url = f"{self.url}/users/{user_id}"
        response = self._get_api_call(url=url).json()
        return response

    def get_ticket_field(self, ticket_field: typing.Union[str, int]):
        """Get the json output for the ticket fields for the prvoided ticket ID

        Args:
            ticket_field (str, int): the ticket_field ID to request for

        Returns:
            dict: a dictionary with the user information {"ticket_field": {...}}
        """
        url = f"{self.url}/ticket_fields/{ticket_field}"
        response = self._get_api_call(url=url).json()
        return response

    def _get_my_user_id(self) -> int:
        """Retrieve my own user ID

        Returns:
            int: My user ID
        """
        # Does it need an email to resolve?
        url = f"{self.url}/users/me.json"
        response = self._get_api_call(url=url).json()
        my_id = response.get("user", {}).get("id")
        return my_id

    @staticmethod
    def _email_ccs(emails: list[str]) -> list[dict[str, str]]:
        """Generate a list of dicts for the CC field based on the provided email addresses

        Args:
            emails (list[str]): list of email addresses

        Returns:
            list[dict[str, str]]: {"user_email": <email address>, "action": "put"}
        """
        return [{"user_email": e, "action": "put"} for e in emails]

    @staticmethod
    def _cc_email_check(cc_emails: typing.Union[list[str], None]) -> list[str]:
        """This function ensures the output is an iterable. Either a the provided iterable
        is verified and returned or an empty list is returned.

        Args:
            cc_emails (list[str]): list of email addresses

        Raises:
            ValueError: [description]

        Returns:
            list[str]: [description]
        """
        if cc_emails is None:
            cc_emails = []
        elif not isinstance(cc_emails, list):
            raise ValueError("ccs needs to be a list")
        return cc_emails
