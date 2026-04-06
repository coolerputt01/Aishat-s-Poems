from urllib.parse import urlencode
from typing import Any, Dict


class QueryBuilder:
    """
    QueryBuilder helps construct query parameters for API requests in a fluent and chainable way.

    Example usage:
        qb = QueryBuilder().eq('name', 'John').gt('age', 18).limit(10).offset(20).build()
        # Result: '?name=John&age_gt=18&limit=10&offset=20'
    """

    def __init__(self):
        """
        Initialize a new QueryBuilder instance.
        """
        self.params: Dict[str, Any] = {}

    def eq(self, field: str, value: Any) -> "QueryBuilder":
        """
        Add an equality filter (field == value).
        """
        self.params[field] = value
        return self

    def contains(self, field: str, value: Any) -> "QueryBuilder":
        """
        Add a filter to check if the field contains the given value.
        """
        self.params[f"{field}_contains"] = value
        return self

    def gt(self, field: str, value: Any) -> "QueryBuilder":
        """
        Add a greater-than filter (field > value).
        """
        self.params[f"{field}_gt"] = value
        return self

    def gte(self, field: str, value: Any) -> "QueryBuilder":
        """
        Add a greater-than-or-equal filter (field >= value).
        """
        self.params[f"{field}_gte"] = value
        return self

    def lt(self, field: str, value: Any) -> "QueryBuilder":
        """
        Add a less-than filter (field < value).
        """
        self.params[f"{field}_lt"] = value
        return self

    def lte(self, field: str, value: Any) -> "QueryBuilder":
        """
        Add a less-than-or-equal filter (field <= value).
        """
        self.params[f"{field}_lte"] = value
        return self

    def limit(self, value: int) -> "QueryBuilder":
        """
        Set a limit on the number of results.
        """
        self.params["limit"] = value
        return self

    def offset(self, value: int) -> "QueryBuilder":
        """
        Set the number of results to skip (useful for pagination).
        """
        self.params["offset"] = value
        return self

    def from_dict(self, filters: Dict[str, Any]) -> "QueryBuilder":
        """
        Add multiple filters from a dictionary.
        """
        for key, value in filters.items():
            self.params[key] = value
        return self

    def build(self, prefix: str = "?") -> str:
        """
        Build and return the query string. Returns an empty string if no parameters are set.
        """
        if not self.params:
            return ""
        return prefix + urlencode(self.params)
