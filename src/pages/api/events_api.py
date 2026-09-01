"""
src/pages/api/events_api.py

API client for the /api/event endpoints of the Geo Travel backend:
listing events and fetching a single event's details.
"""

from ...core.base_api import BaseAPI

class EventAPI(BaseAPI):
    """API client for the /api/event resource (events).

    All methods hit endpoints under the ``/api/event/*`` prefix.
    """

    def get_all_events(self, **params):
        """List events.

        GET /api/event/all

        Args:
            **params: Arbitrary query parameters (e.g. pagination,
                filters) forwarded as-is to the request's query string.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.get("/api/event/all", params=params)

    def get_single_event(self, event_id):
        """Fetch a single event by id.

        GET /api/event/{id}

        Args:
            event_id: Identifier of the event to fetch.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.get(f"/api/event/{event_id}")
