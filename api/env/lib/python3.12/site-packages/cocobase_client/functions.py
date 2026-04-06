"""
CloudFunction client for executing server-side functions.

Cloud functions allow you to run custom server-side logic without managing infrastructure.
Functions are written in Python and deployed to your Cocobase project.
"""

from typing import Optional, Dict, Any, Callable
import requests
from cocobase_client.exceptions import CocobaseError


CLOUD_BASEURL = "https://cloud.cocobase.buzz"


class FunctionResponse:
    """Response from a cloud function execution."""

    def __init__(self, data: Dict[str, Any]):
        self.result = data.get("result")
        self.success = data.get("success", False)
        self.error = data.get("error")
        self.execution_time = data.get("execution_time", 0)
        self.output = data.get("output", "")
        self._raw_data = data

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return self._raw_data


class CloudFunction:
    """
    CloudFunction client for executing server-side functions.

    Example:
        # Access via the Cocobase instance
        db = Cocobase(api_key='your-api-key', project_id='your-project-id')

        # Execute a function
        result = db.functions.execute('sendEmail',
            payload={'to': 'user@example.com', 'subject': 'Hello'},
            method='POST'
        )
    """

    def __init__(self, project_id: str, get_token: Callable[[], Optional[str]]):
        """
        Creates a new CloudFunction client.

        Args:
            project_id: Your Cocobase project ID
            get_token: Function that returns the current authentication token

        Raises:
            ValueError: If project_id is empty or invalid
        """
        if not project_id or project_id.strip() == "":
            raise ValueError(
                "CloudFunction requires a valid project_id. Please provide project_id when creating the client."
            )
        self.project_id = project_id
        self.get_token = get_token

    def execute(
        self,
        function_name: str,
        payload: Optional[Dict[str, Any]] = None,
        method: str = "GET",
    ) -> FunctionResponse:
        """
        Executes a cloud function by name.

        Args:
            function_name: Name of the cloud function to execute
            payload: Optional payload to send to the function
            method: HTTP method to use ('GET' or 'POST')

        Returns:
            FunctionResponse with result and metadata

        Raises:
            CocobaseError: If the request fails

        Example:
            # Simple GET request
            result = db.functions.execute('getStats')

            # POST request with payload
            result = db.functions.execute('processOrder',
                payload={'orderId': '12345', 'items': [{'id': 1, 'quantity': 2}]},
                method='POST'
            )

            print(result.result)  # Function output
            print(result.execution_time)  # Execution time in ms
        """
        if not self.project_id or self.project_id.strip() == "":
            raise CocobaseError(
                "Invalid project_id. Please ensure project_id is set in the client."
            )

        url = f"{CLOUD_BASEURL}/functions/{self.project_id}/func/{function_name}"

        # Default to GET if no payload, otherwise use specified method
        if method.upper() not in ["GET", "POST"]:
            method = "POST" if payload else "GET"

        headers = {"Content-Type": "application/json"}

        # Get the latest token dynamically
        token = self.get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        body = None
        if method.upper() == "POST" and payload:
            body = {"payload": payload}

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            else:
                response = requests.post(url, headers=headers, json=body)

            if not response.ok:
                raise CocobaseError(f"Function execution failed: {response.text}")

            data = response.json()
            return FunctionResponse(data)
        except requests.RequestException as e:
            raise CocobaseError(f"Request error: {str(e)}")
