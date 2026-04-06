import unittest
from cocobase_client.client import CocoBaseClient, CocobaseError
from cocobase_client.query import QueryBuilder
from cocobase_client.record import Record
import uuid

# Replace with your actual API key and test collection/document values
test_api_key = "M-CN05en7o_UGPc9jrQJ0mIbAzJGxZ0qeUJ7KaiA"
test_token = None  # or a valid token if needed


def print_result(test_name, passed):
    print(f"{test_name}-----{'passed' if passed else 'failed'}")


class TestCocoBaseClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = CocoBaseClient(api_key=test_api_key, token=test_token)
        # Use class variables to share test user info between register and login
        cls.test_email = f"testsuser_{uuid.uuid4().hex[:8]}@example.com"
        cls.test_password = "TestPassword123!"
        # Create a collection for document tests
        try:
            result = cls.client.create_collection("test_collection_for_docs2")
            cls.collection_id = result.id if result else None
        except Exception:
            cls.collection_id = None

    def test_create_collection(self):
        try:
            result = self.client.create_collection("test_collection")
            self.assertIsInstance(result, dict)
            print_result("test_create_collection", True)
        except CocobaseError as e:
            print(f"API Response: {getattr(e, 'args', [''])[0]}")
            print_result("test_create_collection", False)
            raise

    def test_update_collection(self):
        # Use the created collection_id
        try:
            result = self.client.update_collection(
                self.collection_id, collection_name="updated_name"
            )
            self.assertIsInstance(result, dict)
            print_result("test_update_collection", True)
        except CocobaseError as e:
            print(f"API Response: {getattr(e, 'args', [''])[0]}")
            print_result("test_update_collection", False)
            raise

    def test_delete_collection(self):
        # Create and then delete a collection to ensure it exists
        try:
            result = self.client.create_collection("to_delete")
            collection_id = result.id if result else None
            del_result = self.client.delete_collection(collection_id)
            self.assertTrue(del_result)
            print_result("test_delete_collection", True)
        except CocobaseError as e:
            print(f"API Response: {getattr(e, 'args', [''])[0]}")
            print_result("test_delete_collection", False)
            raise

    def test_create_document(self):
        try:
            result = self.client.create_document(self.collection_id, {"field": "value"})
            self.assertIsInstance(result, Record)
            print_result("test_create_document", True)
        except CocobaseError as e:
            print(f"API Response: {getattr(e, 'args', [''])[0]}")
            print_result("test_create_document", False)
            raise

    def test_list_documents(self):
        try:
            result = self.client.list_documents(self.collection_id)
            self.assertIsInstance(result, list)
            print_result("test_list_documents", True)
        except CocobaseError as e:
            print(f"API Response: {getattr(e, 'args', [''])[0]}")
            print_result("test_list_documents", False)
            raise

    def test_authentication(self):
        try:
            self.assertFalse(self.client.is_authenticated())
            print_result("test_authentication", True)
        except Exception:
            print_result("test_authentication", False)
            raise

    def test_register(self):
        try:
            result = self.client.register(self.test_email, self.test_password)
            self.assertTrue(result)
            print_result("test_register", True)
        except CocobaseError as e:
            print(f"API Response: {getattr(e, 'args', [''])[0]}")
            print_result("test_register", False)
            raise

    def test_login(self):
        # Ensure registration happens before login
        self.test_register()
        try:
            result = self.client.login(self.test_email, self.test_password)
            self.assertTrue(result)
            print_result("test_login", True)
        except CocobaseError as e:
            print(f"API Response: {getattr(e, 'args', [''])[0]}")
            print_result("test_login", False)
            raise


if __name__ == "__main__":
    unittest.main()
