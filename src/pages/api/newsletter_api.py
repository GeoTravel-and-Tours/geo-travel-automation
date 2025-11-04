# src/pages/api/newsletter_api.py


from ...core.base_api import BaseAPI

class NewsletterAPI(BaseAPI):
    def subscribe_newsletter(self, subscribe_data):
        """POST /api/newsletter/create"""
        return self.post("/api/newsletter/create", json=subscribe_data)