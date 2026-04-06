from datetime import datetime
from typing import Any, Optional


class Record:
    """A class representing a record in a database, allowing for dictionary-like access with typed getters."""

    data: dict
    id: str
    collectionId: str
    createdAt: datetime
    collection: dict

    def __init__(self, data: dict):
        self.data = data.get("data", {})
        self.id = data.get("id", "")
        self.collectionId = data.get("collection_id", "")
        created_at = data.get("created_at", 0)
        # Handle string, int, float, or ISO format for created_at
        if isinstance(created_at, datetime):
            self.createdAt = created_at
        elif isinstance(created_at, (int, float)):
            self.createdAt = datetime.fromtimestamp(created_at)
        elif isinstance(created_at, str):
            try:
                # Try ISO format first
                self.createdAt = datetime.fromisoformat(created_at)
            except ValueError:
                try:
                    # Try as float timestamp string
                    self.createdAt = datetime.fromtimestamp(float(created_at))
                except Exception:
                    self.createdAt = datetime.fromtimestamp(0)
        else:
            self.createdAt = datetime.fromtimestamp(0)
        self.collection = data.get("collection", {})

    def __repr__(self):
        return f"Record({self.data})"

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def get(self, key, default=None):
        return self.data.get(key, default)

    def items(self):
        return self.data.items()

    # -----------------------------
    # Typed getter helpers below
    # -----------------------------

    def get_string(self, key: str, raise_error: bool = False) -> Optional[str]:
        value = self.data.get(key)
        try:
            return str(value) if value is not None else None
        except Exception:
            if raise_error:
                raise TypeError(f"Value for '{key}' is not string-convertible: {value}")
            return None

    def get_int(self, key: str, raise_error: bool = False) -> Optional[int]:
        value = self.data.get(key)
        if value is None:
            return None
        try:
            return int(value)
        except Exception:
            if raise_error:
                raise TypeError(f"Value for '{key}' is not int-convertible: {value}")
            return None

    def get_float(self, key: str, raise_error: bool = False) -> Optional[float]:
        value = self.data.get(key)
        if value is None:
            return None
        try:
            return float(value)
        except Exception:
            if raise_error:
                raise TypeError(f"Value for '{key}' is not float-convertible: {value}")
            return None

    def get_bool(self, key: str, raise_error: bool = False) -> Optional[bool]:
        value = self.data.get(key)
        if value is None:
            return None
        try:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                val = value.strip().lower()
                if val in ("true", "1", "yes"):
                    return True
                if val in ("false", "0", "no"):
                    return False
            return bool(int(value))  # for numeric truthiness
        except Exception:
            if raise_error:
                raise TypeError(f"Value for '{key}' is not bool-convertible: {value}")
            return None

    def get_datetime(self, key: str, raise_error: bool = False) -> Optional[datetime]:
        value = self.data.get(key)
        try:
            if isinstance(value, datetime):
                return value
            if isinstance(value, (int, float)):
                return datetime.fromtimestamp(value)
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value)
                except ValueError:
                    return datetime.fromtimestamp(float(value))
        except Exception:
            pass
        if raise_error:
            raise TypeError(f"Value for '{key}' is not datetime-convertible: {value}")
        return None


class Collection:
    """A class representing a collection in a database, allowing for dictionary-like access with typed getters."""

    name: str
    id: str
    createdAt: datetime

    def __init__(self, data: dict):
        self.name = data.get("name", "")
        self.id = data.get("id", "")
        created_at = data.get("created_at", 0)
        # Handle string, int, float, or ISO format for created_at
        if isinstance(created_at, datetime):
            self.createdAt = created_at
        elif isinstance(created_at, (int, float)):
            self.createdAt = datetime.fromtimestamp(created_at)
        elif isinstance(created_at, str):
            try:
                # Try ISO format first
                self.createdAt = datetime.fromisoformat(created_at)
            except ValueError:
                try:
                    # Try as float timestamp string
                    self.createdAt = datetime.fromtimestamp(float(created_at))
                except Exception:
                    self.createdAt = datetime.fromtimestamp(0)
        else:
            self.createdAt = datetime.fromtimestamp(0)

    def __repr__(self):
        return f"Collection(name={self.name}, id={self.id}, createdAt={self.createdAt})"
