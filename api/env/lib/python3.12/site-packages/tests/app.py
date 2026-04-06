from cocobase_client.client import CocoBaseClient
import time

test_api_key = "M-CN05en7o_UGPc9jrQJ0mIbAzJGxZ0qeUJ7KaiA"

cb = CocoBaseClient(api_key=test_api_key)


def timed_update_document():
    start = time.time()
    x = cb.update_document(
        "1",
        "00ee8d9d-ddd6-400a-ba89-a727013bb8de",
        {
            "full_name": "Updated Name",
        },
    )
    end = time.time()
    print(x)
    print(f"Time taken: {end - start:.4f} seconds")


if __name__ == "__main__":
    timed_update_document()
