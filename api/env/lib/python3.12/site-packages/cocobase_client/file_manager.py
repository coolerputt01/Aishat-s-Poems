from io import BufferedReader
from typing import IO, Optional
from cocobase_client.client import CocoBaseClient
from cocobase_client.exceptions import CocobaseError
from cocobase_client.types import HttpMethod


class CocoFileManager:
    instance: CocoBaseClient = None

    def __init__(self, instance: CocoBaseClient):
        if not instance.api_key:
            raise CocobaseError(
                "cant initialize file manager when api_key has not been set"
            )
        self.instance = instance

    def upload_file(
        self,
        file: IO[bytes],
        filename: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> str:
        """
        uploading files to specified Coco project, optionaly specify directory to choose where on the server to store your files
        """
        # Prepare upload name
        upload_name = f"{directory}/{filename}" if directory and filename else filename

        # Prepare files dict
        files_dict = {"file": (upload_name, file)}

        # Make request
        res = self.instance.__request__(
            "/collections/file",
            method="POST",  # or HttpMethod.post
            files=files_dict,
        )

        # Return uploaded file URL
        return res.json()["url"]


# file_bytes = b"Hello, world!"

# # No content_type provided
# files = {"file": ("myfile.txt", file_bytes)}

# response = requests.post(url, files=files)
