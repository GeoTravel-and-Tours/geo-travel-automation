# src/pages/api/event_api.py

from ...core.base_api import BaseAPI

class EventAPI(BaseAPI):
    def get_all_events(self, **params):
        """GET /api/event/all"""
        return self.get("/api/event/all", params=params)
    
    def get_single_event(self, event_id):
        """GET /api/event/{id}"""
        return self.get(f"/api/event/{event_id}")