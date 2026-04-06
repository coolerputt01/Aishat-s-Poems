from requests import Response, get, post, patch, delete
import requests
from typing import Optional, Dict, Any, List
from cocobase_client.config import BASEURL
from cocobase_client.exceptions import CocobaseError
from cocobase_client.query import QueryBuilder
from cocobase_client.record import Collection, Record
from cocobase_client.types import HttpMethod
from cocobase_client.auth import AuthHandler
from cocobase_client.functions import CloudFunction
import json


class CocoBaseClient:
    """
    A client for interacting with the CocoBase API.
    Provides methods for collection, document, and user authentication management.
    """

    api_key = None
    project_id = None
    base_url = None

    def __init__(self, api_key: Optional[str] = None, project_id: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the CocoBaseClient with an API key and optional project ID.

        Args:
            api_key: Your Cocobase API key
            project_id: Your Cocobase project ID (required for cloud functions)
            base_url: Custom base URL (defaults to https://api.cocobase.buzz)
        """
        self.api_key = api_key
        self.project_id = project_id
        self.base_url = base_url or BASEURL
        self.auth = AuthHandler(api_key=api_key, base_url=self.base_url)
        self.functions = CloudFunction(
            project_id or "project id required",
            lambda: self.auth.get_token()
        )

    def __request__(
        self,
        url,
        method: HttpMethod = HttpMethod.get,
        data: Optional[Dict[str, Any]] = None,
        custom_headers: Optional[Dict[str, Any]] = None,
        files=None,
        use_data_key: bool = True,
    ) -> Response:
        """
        Internal method to send HTTP requests to the CocoBase API.
        Handles GET, POST, PATCH, and DELETE methods, and allows custom headers.
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        if self.auth.get_token():
            headers["Authorization"] = f"Bearer {self.auth.get_token()}"

        if not url.startswith("/"):
            url = "/" + url
        if custom_headers is not None:
            headers.update(custom_headers)
        if method not in (
            HttpMethod.get,
            HttpMethod.post,
            HttpMethod.delete,
            HttpMethod.patch,
        ):
            raise ValueError(
                "Invalid HTTP method. Use HttpMethod.get, HttpMethod.post, HttpMethod.delete, or HttpMethod.patch."
            )
        url = self.base_url + url

        # Wrap data in data key if needed
        payload = {"data": data} if use_data_key and data else data

        if method == HttpMethod.get:
            return get(url, headers=headers, files=files)
        elif method == HttpMethod.delete:
            return delete(url, headers=headers, json=payload, files=files)
        elif method == HttpMethod.patch:
            return patch(url, headers=headers, json=payload, files=files)
        else:
            return post(url, headers=headers, json=payload, files=files)

    # ------------------- COLLECTION METHODS -------------------
    def create_collection(
        self, collection_name, webhookurl: str | None = None
    ) -> Collection:
        """
        Create a new collection with an optional webhook URL.
        """
        data = {"name": collection_name}
        if webhookurl is not None:
            data["webhook_url"] = webhookurl
        req = self.__request__("/collections/", method=HttpMethod.post, data=data)
        if req.status_code == 400:
            raise CocobaseError("Invalid Request: " + req.text)
        elif req.status_code == 422:
            raise CocobaseError("A field is missing: " + req.text)
        elif req.status_code == 500:
            raise CocobaseError("Internal Server Error")
        elif req.status_code == 201:
            return Collection(req.json())
        else:
            raise CocobaseError(f"Unexpected status code {req.status_code}: {req.text}")

    def update_collection(
        self,
        collection_id,
        collection_name: str | None = None,
        webhookurl: str | None = None,
    ) -> dict:
        """
        Update an existing collection's name and/or webhook URL.
        """
        data = dict()
        if collection_id is None:
            raise CocobaseError("Collection ID must be provided.")
        if webhookurl is None and collection_name is None:
            raise CocobaseError(
                "At least one of webhook_url or collection_name must be provided."
            )
        if webhookurl is not None:
            data["webhook_url"] = webhookurl
        if collection_name is not None:
            data["name"] = collection_name
        req = self.__request__(
            f"/collections/{collection_id}", method=HttpMethod.patch, data=data
        )
        if req.status_code == 400:
            raise CocobaseError("Invalid Request: " + req.text)
        elif req.status_code == 404:
            raise CocobaseError("Collection not found")
        elif req.status_code == 422:
            raise CocobaseError("A field is missing: " + req.text)
        elif req.status_code == 500:
            raise CocobaseError("Internal Server Error")
        elif req.status_code == 200:
            return req.json()
        else:
            raise CocobaseError(f"Unexpected status code {req.status_code}: {req.text}")

    def delete_collection(self, collection_id) -> bool:
        """
        Delete a collection by its ID.
        """
        if collection_id is None:
            raise CocobaseError("Collection ID must be provided.")
        req = self.__request__(
            f"/collections/{collection_id}", method=HttpMethod.delete
        )
        if req.status_code == 400:
            raise CocobaseError("Invalid Request: " + req.text)
        elif req.status_code == 404:
            raise CocobaseError("Collection not found")
        elif req.status_code == 422:
            raise CocobaseError("A field is missing: " + req.text)
        elif req.status_code == 500:
            raise CocobaseError("Internal Server Error")
        elif req.status_code == 204 or req.status_code == 200:
            return True
        else:
            raise CocobaseError(f"Unexpected status code {req.status_code}: {req.text}")

    # ------------------- DOCUMENT METHODS -------------------
    def create_document(self, collection_id, data: dict) -> Record:
        """
        Create a new document in a collection.
        """
        if collection_id is None:
            raise CocobaseError("Collection ID must be provided.")
        if not isinstance(data, dict):
            raise CocobaseError("Data must be a dictionary.")
        req = self.__request__(
            f"/collections/documents?collection=" + collection_id,
            method=HttpMethod.post,
            data={"data": data},
        )
        if req.status_code == 400:
            raise CocobaseError("Invalid Request: " + req.text)
        elif req.status_code == 404:
            raise CocobaseError("Collection not found")
        elif req.status_code == 422:
            raise CocobaseError("A field is missing: " + req.text)
        elif req.status_code == 500:
            raise CocobaseError("Internal Server Error")
        elif req.status_code == 201:
            return Record(req.json())
        else:
            raise CocobaseError(f"Unexpected status code {req.status_code}: {req.text}")

    def list_documents(
        self, collection_id, query: QueryBuilder | None = None
    ) -> list[Record]:
        """
        List all documents in a collection, optionally filtered by a query.
        """
        if collection_id is None:
            raise CocobaseError("Collection ID must be provided.")
        if query is not None and not isinstance(query, QueryBuilder):
            raise CocobaseError("Query must be an instance of QueryBuilder.")
        url = (
            f"/collections/{collection_id}/documents{query.build()}"
            if query is not None
            else f"/collections/{collection_id}/documents"
        )
        req = self.__request__(url)
        if req.status_code == 400:
            raise CocobaseError("Invalid Request: " + req.text)
        elif req.status_code == 404:
            raise CocobaseError("Collection not found")
        elif req.status_code == 422:
            raise CocobaseError("A field is missing: " + req.text)
        elif req.status_code == 500:
            raise CocobaseError("Internal Server Error")
        elif req.status_code == 200:
            return [Record(doc) for doc in req.json()]
        else:
            raise CocobaseError(f"Unexpected status code {req.status_code}: {req.text}")

    def get_document(self, collection_id, document_id) -> Record:
        """
        Retrieve a single document by its ID from a collection.
        """
        if collection_id is None:
            raise CocobaseError("Collection ID must be provided.")
        if document_id is None:
            raise CocobaseError("Document ID must be provided.")
        req = self.__request__(f"/collections/{collection_id}/documents/{document_id}")
        if req.status_code == 400:
            raise CocobaseError("Invalid Request: " + req.text)
        elif req.status_code == 404:
            raise CocobaseError("Document not found")
        elif req.status_code == 422:
            raise CocobaseError("A field is missing: " + req.text)
        elif req.status_code == 500:
            raise CocobaseError("Internal Server Error")
        elif req.status_code == 200:
            return Record(req.json())
        else:
            raise CocobaseError(f"Unexpected status code {req.status_code}: {req.text}")

    def delete_document(self, collection_id, document_id) -> bool:
        """
        Delete a document from a collection by its ID.
        """
        if collection_id is None:
            raise CocobaseError("Collection ID must be provided.")
        if document_id is None:
            raise CocobaseError("Document ID must be provided.")
        req = self.__request__(
            f"/collections/{collection_id}/documents/{document_id}",
            method=HttpMethod.delete,
        )
        if req.status_code == 400:
            raise CocobaseError("Invalid Request: " + req.text)
        elif req.status_code == 404:
            raise CocobaseError("Document not found")
        elif req.status_code == 422:
            raise CocobaseError("A field is missing: " + req.text)
        elif req.status_code == 500:
            raise CocobaseError("Internal Server Error")
        elif req.status_code == 200 or req.status_code == 204:
            return True
        else:
            raise CocobaseError(f"Unexpected status code {req.status_code}: {req.text}")

    def update_document(self, collection_id, document_id, data: dict) -> Record:
        """
        Update a document in a collection by its ID.
        """
        if collection_id is None:
            raise CocobaseError("Collection ID must be provided.")
        if document_id is None:
            raise CocobaseError("Document ID must be provided.")
        if not isinstance(data, dict):
            raise CocobaseError("Data must be a dictionary.")
        req = self.__request__(
            f"/collections/{collection_id}/documents/{document_id}",
            method=HttpMethod.patch,
            data=data,
        )
        if req.status_code == 400:
            raise CocobaseError("Invalid Request: " + req.text)
        elif req.status_code == 404:
            raise CocobaseError("Document not found")
        elif req.status_code == 422:
            raise CocobaseError("A field is missing: " + req.text)
        elif req.status_code == 500:
            raise CocobaseError("Internal Server Error")
        elif req.status_code == 200:
            return Record(req.json())
        else:
            raise CocobaseError(f"Unexpected status code {req.status_code}: {req.text}")

    # ------------------- FILE UPLOAD METHODS -------------------
    def create_document_with_files(
        self,
        collection_id: str,
        data: Dict[str, Any],
        files: Dict[str, Any],
    ) -> Record:
        """
        Create a document with file uploads.

        Args:
            collection_id: Collection name
            data: Document data (JSON object)
            files: Dictionary mapping field names to file objects

        Returns:
            Created document record
        """
        form_data = {"data": json.dumps(data)}

        # Add files with their field names
        files_dict = {}
        for field_name, file_or_files in files.items():
            if isinstance(file_or_files, list):
                # Multiple files with same field name creates an array
                files_dict[field_name] = [
                    (field_name, file_obj) for file_obj in file_or_files
                ]
            else:
                # Single file
                files_dict[field_name] = file_or_files

        url = f"{self.base_url}/collections/documents?collection={collection_id}"
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        if self.auth.get_token():
            headers["Authorization"] = f"Bearer {self.auth.get_token()}"

        response = requests.post(url, data=form_data, files=files_dict, headers=headers)

        if not response.ok:
            raise CocobaseError(f"File upload failed: {response.text}")

        return Record(response.json())

    def update_document_with_files(
        self,
        collection_id: str,
        document_id: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Record:
        """
        Update a document with file uploads.

        Args:
            collection_id: Collection name
            document_id: Document ID
            data: Partial document data to update (optional)
            files: Dictionary mapping field names to file objects (optional)

        Returns:
            Updated document record
        """
        form_data = {}
        if data:
            form_data["data"] = json.dumps(data)

        # Add files with their field names if provided
        files_dict = {}
        if files:
            for field_name, file_or_files in files.items():
                if isinstance(file_or_files, list):
                    files_dict[field_name] = [
                        (field_name, file_obj) for file_obj in file_or_files
                    ]
                else:
                    files_dict[field_name] = file_or_files

        url = f"{self.base_url}/collections/{collection_id}/documents/{document_id}"
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        if self.auth.get_token():
            headers["Authorization"] = f"Bearer {self.auth.get_token()}"

        response = requests.patch(url, data=form_data, files=files_dict, headers=headers)

        if not response.ok:
            raise CocobaseError(f"File upload failed: {response.text}")

        return Record(response.json())

    def upload_file(self, file) -> Dict[str, str]:
        """
        Uploads a single file to Cocobase cloud storage.

        Args:
            file: File object to upload

        Returns:
            Dictionary containing the file URL
        """
        files = {"file": file}

        url = f"{self.base_url}/collections/file"
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        response = requests.post(url, files=files, headers=headers)

        if not response.ok:
            raise CocobaseError("File upload failed")

        return response.json()

    # ------------------- BATCH OPERATIONS -------------------
    def delete_documents(self, collection_id: str, document_ids: List[str]) -> Dict[str, Any]:
        """
        Batch delete documents.

        Args:
            collection_id: Collection name
            document_ids: List of document IDs to delete

        Returns:
            Dictionary with status, message, and count
        """
        req = self.__request__(
            f"/collections/{collection_id}/batch/documents/delete",
            method=HttpMethod.post,
            data={"document_ids": document_ids},
            use_data_key=False,
        )
        if req.status_code == 200:
            return req.json()
        else:
            raise CocobaseError(f"Batch delete failed: {req.text}")

    def create_documents(self, collection_id: str, documents: List[Dict[str, Any]]) -> List[Record]:
        """
        Batch create documents.

        Args:
            collection_id: Collection name
            documents: List of document data objects

        Returns:
            List of created document records
        """
        req = self.__request__(
            f"/collections/{collection_id}/batch/documents/create",
            method=HttpMethod.post,
            data={"documents": documents},
            use_data_key=False,
        )
        if req.status_code == 200 or req.status_code == 201:
            return [Record(doc) for doc in req.json()]
        else:
            raise CocobaseError(f"Batch create failed: {req.text}")

    def update_documents(
        self,
        collection_id: str,
        updates: Dict[str, Dict[str, Any]],
    ) -> List[Record]:
        """
        Batch update documents.

        Args:
            collection_id: Collection name
            updates: Dictionary mapping document IDs to partial update objects

        Returns:
            List of updated document records
        """
        req = self.__request__(
            f"/collections/{collection_id}/batch/documents/update",
            method=HttpMethod.post,
            data={"updates": updates},
            use_data_key=False,
        )
        if req.status_code == 200:
            return [Record(doc) for doc in req.json()]
        else:
            raise CocobaseError(f"Batch update failed: {req.text}")

    # ------------------- ADVANCED QUERY OPERATIONS -------------------
    def count_documents(
        self,
        collection_id: str,
        query: Optional[QueryBuilder] = None,
    ) -> Dict[str, int]:
        """
        Count documents matching filters without returning the documents.

        Args:
            collection_id: Collection name
            query: Optional query builder for filtering

        Returns:
            Dictionary with count
        """
        query_str = query.build() if query else ""
        url = f"/collections/{collection_id}/query/documents/count{query_str}"
        req = self.__request__(url)

        if req.status_code == 200:
            return req.json()
        else:
            raise CocobaseError(f"Count failed: {req.text}")

    def aggregate_documents(
        self,
        collection_id: str,
        field: str,
        operation: str,
        query: Optional[QueryBuilder] = None,
    ) -> Dict[str, Any]:
        """
        Perform aggregation on documents.

        Args:
            collection_id: Collection name
            field: Field name to perform aggregation on
            operation: Type of aggregation ('count', 'sum', 'avg', 'min', 'max')
            query: Optional query builder for filtering

        Returns:
            Dictionary with aggregation results
        """
        query_str = query.build("&") if query else ""
        url = f"/collections/{collection_id}/query/documents/aggregate?field={field}&operation={operation}{query_str}"
        req = self.__request__(url)

        if req.status_code == 200:
            return req.json()
        else:
            raise CocobaseError(f"Aggregation failed: {req.text}")

    # ------------------- AUTHENTICATION METHODS (DEPRECATED) -------------------
    # These methods are deprecated. Use db.auth.* methods instead.

    def init_auth(self):
        """
        DEPRECATED: Use db.auth.init_auth() instead.
        Initializes authentication by restoring the session from storage.
        """
        return self.auth.init_auth()

    def login(self, email: str, password: str):
        """
        DEPRECATED: Use db.auth.login() instead.
        Log in a user with email and password.
        """
        return self.auth.login(email, password)

    def register(self, email: str, password: str, data: Optional[Dict[str, Any]] = None):
        """
        DEPRECATED: Use db.auth.register() instead.
        Register a new user with email, password, and optional extra data.
        """
        return self.auth.register(email, password, data)

    def logout(self):
        """
        DEPRECATED: Use db.auth.logout() instead.
        Log out the current user.
        """
        return self.auth.logout()

    def is_authenticated(self) -> bool:
        """
        DEPRECATED: Use db.auth.is_authenticated() instead.
        Check if the client is authenticated.
        """
        return self.auth.is_authenticated()

    def get_current_user(self):
        """
        DEPRECATED: Use db.auth.get_current_user() instead.
        Get the current user's information.
        """
        return self.auth.get_current_user()

    def update_user(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ):
        """
        DEPRECATED: Use db.auth.update_user() instead.
        Update the current user's information.
        """
        return self.auth.update_user(data, email, password)
